import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/constants.dart';
import '../providers/providers.dart';

class AudioPlayerWidget extends ConsumerStatefulWidget {
  final String audioUrl;
  final ValueChanged<double>? onSpeedChanged;

  const AudioPlayerWidget({
    super.key,
    required this.audioUrl,
    this.onSpeedChanged,
  });

  @override
  ConsumerState<AudioPlayerWidget> createState() => _AudioPlayerWidgetState();
}

class _AudioPlayerWidgetState extends ConsumerState<AudioPlayerWidget> {
  StreamSubscription? _posSub;
  StreamSubscription? _playSub;
  StreamSubscription? _speedSub;

  Duration _position = Duration.zero;
  Duration _duration = const Duration(seconds: 60);
  bool _isPlaying = false;
  double _currentSpeed = 1.0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initPlayer();
    });
  }

  void _initPlayer() async {
    final player = ref.read(audioPlaybackProvider);
    await player.load(widget.audioUrl);
    _posSub = player.positionStream.listen((pos) {
      if (mounted) setState(() => _position = pos);
    });
    player.durationStream.listen((dur) {
      if (mounted && dur != null) setState(() => _duration = dur);
    });
    _playSub = player.playingStream.listen((playing) {
      if (mounted) setState(() => _isPlaying = playing);
    });
    _speedSub = player.speedStream.listen((speed) {
      if (mounted) setState(() => _currentSpeed = speed);
    });
  }

  @override
  void dispose() {
    _posSub?.cancel();
    _playSub?.cancel();
    _speedSub?.cancel();
    super.dispose();
  }

  void _togglePlay() {
    final player = ref.read(audioPlaybackProvider);
    if (_isPlaying) {
      player.pause();
    } else {
      player.play();
    }
  }

  void _setSpeed(double speed) {
    final player = ref.read(audioPlaybackProvider);
    player.setSpeed(speed);
    widget.onSpeedChanged?.call(speed);
  }

  void _seek(double seconds) {
    final player = ref.read(audioPlaybackProvider);
    player.seek(Duration(seconds: seconds.toInt()));
  }

  @override
  Widget build(BuildContext context) {
    final durationSeconds = _duration.inSeconds > 0 ? _duration.inSeconds.toDouble() : 60.0;
    final positionSeconds = _position.inSeconds.toDouble().clamp(0.0, durationSeconds);

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              children: [
                IconButton(
                  key: const Key('playPauseButton'),
                  iconSize: 42,
                  color: AppConstants.primaryEmerald,
                  icon: Icon(_isPlaying ? Icons.pause_circle_filled : Icons.play_circle_filled),
                  onPressed: _togglePlay,
                ),
                Expanded(
                  child: Slider(
                    value: positionSeconds,
                    max: durationSeconds,
                    activeColor: AppConstants.primaryEmerald,
                    inactiveColor: Colors.grey.shade300,
                    onChanged: _seek,
                  ),
                ),
                Text(
                  '${_position.inSeconds}ث / ${_duration.inSeconds}ث',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              alignment: WrapAlignment.center,
              crossAxisAlignment: WrapCrossAlignment.center,
              spacing: 8,
              runSpacing: 4,
              children: [
                const Text('سرعة الصوت: ', style: TextStyle(fontSize: 13)),
                ...[0.75, 1.0, 1.25, 1.5].map((s) {
                  final isSelected = (_currentSpeed - s).abs() < 0.01;
                  return ChoiceChip(
                    label: Text('${s}x'),
                    selected: isSelected,
                    selectedColor: AppConstants.accentGold,
                    onSelected: (_) => _setSpeed(s),
                  );
                }),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

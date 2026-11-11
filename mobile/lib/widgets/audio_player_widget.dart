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
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;
  bool _isPlaying = false;
  double _currentSpeed = 1.0;
  bool _hasError = false;
  String? _errorMessage;

  StreamSubscription<Duration>? _posSub;
  StreamSubscription<bool>? _playSub;
  StreamSubscription<double>? _speedSub;
  StreamSubscription<String?>? _errSub;

  final List<double> _speeds = [0.75, 1.0, 1.25, 1.5];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initPlayer();
    });
  }

  void _initPlayer() async {
    final player = ref.read(audioPlaybackProvider);
    final url = widget.audioUrl.trim();
    if (url.isEmpty) {
      if (mounted) {
        setState(() {
          _hasError = true;
          _errorMessage = 'لا يوجد ملف صوتي معتمد لهذا النص';
          _isPlaying = false;
        });
      }
      return;
    }

    if (mounted) {
      setState(() {
        _hasError = false;
        _errorMessage = null;
        _isPlaying = false;
      });
    }

    try {
      await player.load(url);
    } catch (e) {
      if (mounted) {
        setState(() {
          _hasError = true;
          _errorMessage = 'تعذر تحميل الملف الصوتي';
          _isPlaying = false;
        });
      }
      return;
    }

    _posSub?.cancel();
    _posSub = player.positionStream.listen((pos) {
      if (mounted) setState(() => _position = pos);
    });
    player.durationStream.listen((dur) {
      if (mounted && dur != null) setState(() => _duration = dur);
    });
    _playSub?.cancel();
    _playSub = player.playingStream.listen((playing) {
      if (mounted) setState(() => _isPlaying = _hasError ? false : playing);
    });
    _speedSub?.cancel();
    _speedSub = player.speedStream.listen((speed) {
      if (mounted) setState(() => _currentSpeed = speed);
    });
    _errSub?.cancel();
    _errSub = player.errorStream.listen((err) {
      if (mounted && err != null) {
        setState(() {
          _hasError = true;
          _errorMessage = 'تعذر تحميل الملف الصوتي';
          _isPlaying = false;
        });
      }
    });
  }

  @override
  void dispose() {
    _posSub?.cancel();
    _playSub?.cancel();
    _speedSub?.cancel();
    _errSub?.cancel();
    super.dispose();
  }

  void _togglePlay() {
    if (_hasError) return;
    final player = ref.read(audioPlaybackProvider);
    if (_isPlaying) {
      player.pause();
    } else {
      player.play();
    }
  }

  void _setSpeed(double speed) {
    if (_hasError) return;
    final player = ref.read(audioPlaybackProvider);
    player.setSpeed(speed);
    widget.onSpeedChanged?.call(speed);
  }

  void _seek(double seconds) {
    if (_hasError) return;
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
            if (_hasError) ...[
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                margin: const EdgeInsets.only(bottom: 8),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline, color: AppConstants.errorRed, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _errorMessage ?? 'تعذر تحميل الملف الصوتي',
                        style: const TextStyle(color: AppConstants.errorRed, fontSize: 13),
                        textDirection: TextDirection.rtl,
                      ),
                    ),
                    TextButton.icon(
                      key: const Key('retryLoadAudioButton'),
                      onPressed: _initPlayer,
                      icon: const Icon(Icons.refresh, size: 16, color: AppConstants.primaryEmerald),
                      label: const Text(
                        'إعادة المحاولة',
                        style: TextStyle(fontSize: 12, color: AppConstants.primaryEmerald, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            Row(
              children: [
                IconButton(
                  key: const Key('playPauseButton'),
                  iconSize: 42,
                  color: _hasError ? Colors.grey : AppConstants.primaryEmerald,
                  icon: Icon((!_hasError && _isPlaying) ? Icons.pause_circle_filled : Icons.play_circle_filled),
                  onPressed: _hasError ? null : _togglePlay,
                ),
                Expanded(
                  child: Slider(
                    value: positionSeconds,
                    max: durationSeconds,
                    activeColor: AppConstants.primaryEmerald,
                    inactiveColor: Colors.grey.shade300,
                    onChanged: _hasError ? null : _seek,
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
              children: [
                const Text('سرعة الصوت:', style: TextStyle(fontSize: 12, color: Colors.grey)),
                ..._speeds.map((s) {
                  final isSelected = (_currentSpeed - s).abs() < 0.01;
                  return ChoiceChip(
                    label: Text('${s}x', style: TextStyle(fontSize: 11, color: isSelected ? Colors.white : Colors.black)),
                    selected: isSelected,
                    selectedColor: AppConstants.primaryEmerald,
                    onSelected: _hasError ? null : (_) => _setSpeed(s),
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

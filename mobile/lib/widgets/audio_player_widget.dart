import 'package:flutter/material.dart';
import '../core/constants.dart';

class AudioPlayerWidget extends StatefulWidget {
  final String audioUrl;
  final ValueChanged<double>? onSpeedChanged;

  const AudioPlayerWidget({
    super.key,
    required this.audioUrl,
    this.onSpeedChanged,
  });

  @override
  State<AudioPlayerWidget> createState() => _AudioPlayerWidgetState();
}

class _AudioPlayerWidgetState extends State<AudioPlayerWidget> {
  bool _isPlaying = false;
  double _currentSpeed = 1.0;
  double _position = 0.0;
  final double _duration = 60.0;

  void _togglePlay() {
    setState(() {
      _isPlaying = !_isPlaying;
    });
  }

  void _setSpeed(double speed) {
    setState(() {
      _currentSpeed = speed;
    });
    widget.onSpeedChanged?.call(speed);
  }

  @override
  Widget build(BuildContext context) {
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
                  iconSize: 42,
                  color: AppConstants.primaryEmerald,
                  icon: Icon(_isPlaying ? Icons.pause_circle_filled : Icons.play_circle_filled),
                  onPressed: _togglePlay,
                ),
                Expanded(
                  child: Slider(
                    value: _position,
                    max: _duration,
                    activeColor: AppConstants.primaryEmerald,
                    inactiveColor: Colors.grey.shade300,
                    onChanged: (val) {
                      setState(() {
                        _position = val;
                      });
                    },
                  ),
                ),
                Text(
                  '${_position.toInt()}ث / ${_duration.toInt()}ث',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text('سرعة الصوت: ', style: TextStyle(fontSize: 13)),
                Wrap(
                  spacing: 8,
                  children: [0.75, 1.0, 1.25].map((s) {
                    final isSelected = _currentSpeed == s;
                    return ChoiceChip(
                      label: Text('${s}x'),
                      selected: isSelected,
                      selectedColor: AppConstants.accentGold,
                      onSelected: (_) => _setSpeed(s),
                    );
                  }).toList(),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

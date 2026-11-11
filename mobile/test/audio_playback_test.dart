import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/audio_playback_service.dart';

void main() {
  group('AudioPlaybackService Tests', () {
    test('SimulatedAudioPlaybackService updates speed and notifies speedStream', () async {
      final player = SimulatedAudioPlaybackService();
      expect(player.speed, equals(1.0));

      final speeds = <double>[];
      final sub = player.speedStream.listen(speeds.add);

      await player.setSpeed(0.75);
      await player.setSpeed(1.25);
      await player.setSpeed(1.5);

      expect(player.speed, equals(1.5));
      expect(speeds, equals([0.75, 1.25, 1.5]));

      await sub.cancel();
      player.dispose();
    });

    test('SimulatedAudioPlaybackService controls playback and seek states', () async {
      final player = SimulatedAudioPlaybackService(duration: const Duration(seconds: 120));
      expect(player.isPlaying, isFalse);

      final playStates = <bool>[];
      final playSub = player.playingStream.listen(playStates.add);

      await player.play();
      expect(player.isPlaying, isTrue);

      await player.pause();
      expect(player.isPlaying, isFalse);
      expect(playStates, equals([true, false]));

      final positions = <Duration>[];
      final posSub = player.positionStream.listen(positions.add);

      await player.seek(const Duration(seconds: 45));
      expect(player.position, equals(const Duration(seconds: 45)));
      expect(positions, equals([const Duration(seconds: 45)]));

      await playSub.cancel();
      await posSub.cancel();
      player.dispose();
    });

    test('AudioPlaybackService stream emissions notify listeners accurately', () async {
      final player = SimulatedAudioPlaybackService(duration: const Duration(seconds: 180));
      bool notified = false;
      final sub = player.speedStream.listen((s) {
        if (s == 1.5) notified = true;
      });
      await player.setSpeed(1.5);
      expect(notified, isTrue);
      await sub.cancel();
      player.dispose();
    });
  });
}


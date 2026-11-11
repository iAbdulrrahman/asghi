import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/audio_recorder_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('BundledAudioSource Tests', () {
    test('generateWavBytes creates valid 60s RIFF WAVE header and payload', () {
      final bytes = BundledAudioSource.generateWavBytes(60);
      expect(bytes.length, equals(44 + 44100 * 2 * 60)); // 44-byte header + 60s 16-bit mono
      // Check RIFF header
      expect(String.fromCharCodes(bytes.sublist(0, 4)), equals('RIFF'));
      expect(String.fromCharCodes(bytes.sublist(8, 12)), equals('WAVE'));
      expect(String.fromCharCodes(bytes.sublist(12, 16)), equals('fmt '));
      expect(String.fromCharCodes(bytes.sublist(36, 40)), equals('data'));
    });

    test('startRecording and stopRecording writes real audio file to disk', () async {
      final recorder = BundledAudioSource(simulatedDuration: const Duration(seconds: 1));
      final tempDir = Directory.systemTemp.createTempSync('audio_test');
      final path = '${tempDir.path}/test_recording.wav';

      await recorder.startRecording(path);
      expect(await recorder.isRecording(), isTrue);

      final savedPath = await recorder.stopRecording();
      expect(savedPath, isNotNull);
      expect(File(savedPath!).existsSync(), isTrue);
      expect(File(savedPath).lengthSync(), equals(44 + 44100 * 2 * 1));

      // Cleanup
      tempDir.deleteSync(recursive: true);
    });

    test('pickAudioFile creates valid picked audio file on disk', () async {
      final recorder = BundledAudioSource(simulatedDuration: const Duration(seconds: 2));
      final pickedPath = await recorder.pickAudioFile();
      expect(pickedPath, isNotNull);
      final file = File(pickedPath!);
      expect(file.existsSync(), isTrue);
      expect(file.lengthSync(), equals(44 + 44100 * 2 * 2));
      file.deleteSync();
    });
  });
}

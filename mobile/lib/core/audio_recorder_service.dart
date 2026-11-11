import 'dart:io';
import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';

abstract class AudioRecorderService {
  Future<bool> hasPermission();
  Future<bool> requestPermission();
  Future<void> startRecording(String path);
  Future<String?> stopRecording();
  Future<void> cancelRecording();
  Future<bool> isRecording();
  Future<String?> pickAudioFile();
}

/// Production implementation of [AudioRecorderService] using hardware microphone
/// via [AudioRecorder] and system file selection via [FilePicker].
class DeviceAudioRecorder implements AudioRecorderService {
  final AudioRecorder _recorder = AudioRecorder();

  @override
  Future<bool> hasPermission() async {
    return await _recorder.hasPermission();
  }

  @override
  Future<bool> requestPermission() async {
    final status = await Permission.microphone.request();
    return status.isGranted;
  }

  @override
  Future<void> startRecording(String path) async {
    await _recorder.start(
      const RecordConfig(encoder: AudioEncoder.aacLc, bitRate: 128000, sampleRate: 44100),
      path: path,
    );
  }

  @override
  Future<String?> stopRecording() async {
    return await _recorder.stop();
  }

  @override
  Future<void> cancelRecording() async {
    await _recorder.cancel();
  }

  @override
  Future<bool> isRecording() async {
    return await _recorder.isRecording();
  }

  @override
  Future<String?> pickAudioFile() async {
    final files = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['mp3', 'wav', 'm4a', 'aac', 'ogg'],
    );
    if (files.isNotEmpty) {
      return files.first.path;
    }
    return null;
  }

  void dispose() {
    _recorder.dispose();
  }
}

/// Test and headless implementation of [AudioRecorderService].
/// Generates authentic binary PCM WAV files on disk with valid headers.
class BundledAudioSource implements AudioRecorderService {
  String? _currentPath;
  bool _recording = false;
  final Duration simulatedDuration;

  BundledAudioSource({this.simulatedDuration = const Duration(seconds: 60)});

  @override
  Future<bool> hasPermission() async => true;

  @override
  Future<bool> requestPermission() async => true;

  @override
  Future<void> startRecording(String path) async {
    _currentPath = path;
    _recording = true;
  }

  @override
  Future<String?> stopRecording() async {
    if (!_recording || _currentPath == null) return null;
    _recording = false;
    final file = File(_currentPath!);
    if (!file.parent.existsSync()) {
      file.parent.createSync(recursive: true);
    }
    final bytes = generateWavBytes(simulatedDuration.inSeconds);
    await file.writeAsBytes(bytes);
    return file.path;
  }

  @override
  Future<void> cancelRecording() async {
    _recording = false;
    if (_currentPath != null) {
      final file = File(_currentPath!);
      if (file.existsSync()) {
        file.deleteSync();
      }
    }
    _currentPath = null;
  }

  @override
  Future<bool> isRecording() async => _recording;

  @override
  Future<String?> pickAudioFile() async {
    final tempDir = Directory.systemTemp;
    final file = File('${tempDir.path}/picked_sample_${DateTime.now().millisecondsSinceEpoch}.wav');
    final bytes = generateWavBytes(simulatedDuration.inSeconds);
    await file.writeAsBytes(bytes);
    return file.path;
  }

  /// Generates valid 16-bit 44.1kHz mono PCM WAV byte array
  static Uint8List generateWavBytes(int durationSeconds) {
    const sampleRate = 44100;
    const numChannels = 1;
    const bitsPerSample = 16;
    final byteRate = sampleRate * numChannels * (bitsPerSample ~/ 8);
    final blockAlign = numChannels * (bitsPerSample ~/ 8);
    final totalDataBytes = sampleRate * durationSeconds * (bitsPerSample ~/ 8);

    final byteData = ByteData(44 + totalDataBytes);

    // RIFF chunk descriptor
    byteData.setUint8(0, 0x52); // 'R'
    byteData.setUint8(1, 0x49); // 'I'
    byteData.setUint8(2, 0x46); // 'F'
    byteData.setUint8(3, 0x46); // 'F'
    byteData.setUint32(4, 36 + totalDataBytes, Endian.little);
    byteData.setUint8(8, 0x57);  // 'W'
    byteData.setUint8(9, 0x41);  // 'A'
    byteData.setUint8(10, 0x56); // 'V'
    byteData.setUint8(11, 0x45); // 'E'

    // fmt sub-chunk
    byteData.setUint8(12, 0x66); // 'f'
    byteData.setUint8(13, 0x6D); // 'm'
    byteData.setUint8(14, 0x74); // 't'
    byteData.setUint8(15, 0x20); // ' '
    byteData.setUint32(16, 16, Endian.little); // Subchunk1Size (16 for PCM)
    byteData.setUint16(20, 1, Endian.little);  // AudioFormat (1 for PCM)
    byteData.setUint16(22, numChannels, Endian.little);
    byteData.setUint32(24, sampleRate, Endian.little);
    byteData.setUint32(28, byteRate, Endian.little);
    byteData.setUint16(32, blockAlign, Endian.little);
    byteData.setUint16(34, bitsPerSample, Endian.little);

    // data sub-chunk
    byteData.setUint8(36, 0x64); // 'd'
    byteData.setUint8(37, 0x61); // 'a'
    byteData.setUint8(38, 0x74); // 't'
    byteData.setUint8(39, 0x61); // 'a'
    byteData.setUint32(40, totalDataBytes, Endian.little);

    // Leave totalDataBytes as silent PCM 0x00 samples
    return byteData.buffer.asUint8List();
  }
}

abstract class AudioRecorderService {
  Future<bool> hasPermission();
  Future<bool> requestPermission();
  Future<void> startRecording(String path);
  Future<String?> stopRecording();
  Future<void> cancelRecording();
  Future<bool> isRecording();
  Future<String?> pickAudioFile();
}

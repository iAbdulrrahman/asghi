abstract class AudioPlaybackService {
  Stream<Duration> get positionStream;
  Stream<Duration?> get durationStream;
  Stream<bool> get playingStream;
  Stream<double> get speedStream;
  Stream<String?> get errorStream;

  Duration get position;
  Duration? get duration;
  bool get isPlaying;
  double get speed;

  Future<void> load(String url);
  Future<void> play();
  Future<void> pause();
  Future<void> seek(Duration position);
  Future<void> setSpeed(double speed);
  Future<void> stop();
  void dispose();
}

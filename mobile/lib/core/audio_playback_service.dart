import 'dart:async';
import 'package:just_audio/just_audio.dart';

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

/// Production implementation of [AudioPlaybackService] using [AudioPlayer] from just_audio.
class JustAudioPlaybackService implements AudioPlaybackService {
  final AudioPlayer _player = AudioPlayer();
  final StreamController<String?> _errorController = StreamController<String?>.broadcast();

  JustAudioPlaybackService() {
    _player.playbackEventStream.listen(
      (_) {},
      onError: (Object e, StackTrace st) {
        _errorController.add(e.toString());
      },
    );
  }

  @override
  Stream<Duration> get positionStream => _player.positionStream;

  @override
  Stream<Duration?> get durationStream => _player.durationStream;

  @override
  Stream<bool> get playingStream => _player.playingStream;

  @override
  Stream<double> get speedStream => _player.speedStream;

  @override
  Stream<String?> get errorStream => _errorController.stream;

  @override
  Duration get position => _player.position;

  @override
  Duration? get duration => _player.duration;

  @override
  bool get isPlaying => _player.playing;

  @override
  double get speed => _player.speed;

  @override
  Future<void> load(String url) async {
    try {
      if (url.startsWith('http://') || url.startsWith('https://')) {
        await _player.setUrl(url);
      } else {
        await _player.setFilePath(url);
      }
    } catch (e) {
      _errorController.add(e.toString());
    }
  }

  @override
  Future<void> play() => _player.play();

  @override
  Future<void> pause() => _player.pause();

  @override
  Future<void> seek(Duration position) => _player.seek(position);

  @override
  Future<void> setSpeed(double speed) => _player.setSpeed(speed);

  @override
  Future<void> stop() => _player.stop();

  @override
  void dispose() {
    _errorController.close();
    _player.dispose();
  }
}

/// Test and headless implementation of [AudioPlaybackService].
class SimulatedAudioPlaybackService implements AudioPlaybackService {
  final StreamController<Duration> _posCtrl = StreamController<Duration>.broadcast();
  final StreamController<Duration?> _durCtrl = StreamController<Duration?>.broadcast();
  final StreamController<bool> _playCtrl = StreamController<bool>.broadcast();
  final StreamController<double> _speedCtrl = StreamController<double>.broadcast();
  final StreamController<String?> _errCtrl = StreamController<String?>.broadcast();

  Duration _position = Duration.zero;
  final Duration? _duration;
  bool _isPlaying = false;
  double _speed = 1.0;

  SimulatedAudioPlaybackService({Duration? duration})
      : _duration = duration ?? const Duration(seconds: 90);

  @override
  Stream<Duration> get positionStream => _posCtrl.stream;

  @override
  Stream<Duration?> get durationStream => _durCtrl.stream;

  @override
  Stream<bool> get playingStream => _playCtrl.stream;

  @override
  Stream<double> get speedStream => _speedCtrl.stream;

  @override
  Stream<String?> get errorStream => _errCtrl.stream;

  @override
  Duration get position => _position;

  @override
  Duration? get duration => _duration;

  @override
  bool get isPlaying => _isPlaying;

  @override
  double get speed => _speed;

  @override
  Future<void> load(String url) async {
    _position = Duration.zero;
    _posCtrl.add(_position);
    _durCtrl.add(_duration);
  }

  @override
  Future<void> play() async {
    _isPlaying = true;
    _playCtrl.add(true);
  }

  @override
  Future<void> pause() async {
    _isPlaying = false;
    _playCtrl.add(false);
  }

  @override
  Future<void> seek(Duration position) async {
    _position = position;
    _posCtrl.add(_position);
  }

  @override
  Future<void> setSpeed(double speed) async {
    _speed = speed;
    _speedCtrl.add(speed);
  }

  @override
  Future<void> stop() async {
    _isPlaying = false;
    _position = Duration.zero;
    _playCtrl.add(false);
    _posCtrl.add(_position);
  }

  @override
  void dispose() {
    _posCtrl.close();
    _durCtrl.close();
    _playCtrl.close();
    _speedCtrl.close();
    _errCtrl.close();
  }
}

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/core/audio_playback_service.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/models/models.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/learner/practice_screen.dart';
import 'mock_adapter.dart';

class SpyAudioPlaybackService implements AudioPlaybackService {
  String? lastLoadedUrl;
  bool shouldFail = false;

  final StreamController<Duration> _posCtrl = StreamController<Duration>.broadcast();
  final StreamController<Duration?> _durCtrl = StreamController<Duration?>.broadcast();
  final StreamController<bool> _playCtrl = StreamController<bool>.broadcast();
  final StreamController<double> _speedCtrl = StreamController<double>.broadcast();
  final StreamController<String?> _errCtrl = StreamController<String?>.broadcast();

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
  Duration get position => Duration.zero;
  @override
  Duration? get duration => const Duration(seconds: 90);
  @override
  bool get isPlaying => false;
  @override
  double get speed => 1.0;

  @override
  Future<void> load(String url) async {
    lastLoadedUrl = url;
    if (shouldFail) {
      _errCtrl.add('Failed to load audio source');
      throw Exception('Failed to load audio source');
    }
  }

  @override
  Future<void> pause() async {}
  @override
  Future<void> play() async {}
  @override
  Future<void> seek(Duration position) async {}
  @override
  Future<void> setSpeed(double speed) async {}
  @override
  Future<void> stop() async {}
  @override
  void dispose() {
    _posCtrl.close();
    _durCtrl.close();
    _playCtrl.close();
    _speedCtrl.close();
    _errCtrl.close();
  }
}

void main() {
  testWidgets('PracticeScreen resolves audioUrl containing /api/audio/', (tester) async {
    final spy = SpyAudioPlaybackService();
    final mockAdapter = MockHttpAdapter();
    final apiClient = ApiClient();
    apiClient.useSecureStorage = false;
    apiClient.dio.httpClientAdapter = mockAdapter;

    final testPassage = Passage(
      passageId: 'p-1',
      text: 'نص تجريبي للاستماع',
      level: 'B1',
      topic: 'العلوم',
      durationSeconds: 90,
      status: 'VERIFIED',
      audioRecordings: [
        AudioRecording(
          recordingId: 'rec-1',
          audioFile: 'sample_fusha_01.mp3',
          durationSeconds: 90,
          status: 'VERIFIED',
          attribution: 'SHOW_NAME',
        ),
      ],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(apiClient),
          audioPlaybackProvider.overrideWithValue(spy),
        ],
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          locale: const Locale('ar'),
          supportedLocales: const [Locale('ar')],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          builder: (context, c) => Directionality(textDirection: TextDirection.rtl, child: c!),
          home: PracticeScreen(passage: testPassage),
        ),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    // Assert that the loaded URL is not a bare local filename and contains /api/audio/
    expect(spy.lastLoadedUrl, isNotNull);
    expect(spy.lastLoadedUrl, contains('/api/audio/'));
  });

  testWidgets('AudioPlayerWidget shows Arabic error message on load failure and disables play button', (tester) async {
    final spy = SpyAudioPlaybackService()..shouldFail = true;

    final testPassage = Passage(
      passageId: 'p-1',
      text: 'نص تجريبي',
      level: 'B1',
      topic: 'عام',
      durationSeconds: 90,
      status: 'VERIFIED',
      audioRecordings: [
        AudioRecording(
          recordingId: 'rec-1',
          audioFile: 'missing.mp3',
          durationSeconds: 90,
          status: 'VERIFIED',
          attribution: 'SHOW_NAME',
        ),
      ],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          audioPlaybackProvider.overrideWithValue(spy),
        ],
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          locale: const Locale('ar'),
          supportedLocales: const [Locale('ar')],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          builder: (context, c) => Directionality(textDirection: TextDirection.rtl, child: c!),
          home: PracticeScreen(passage: testPassage),
        ),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    // Should display Arabic error message
    expect(find.textContaining('تعذر تحميل الملف الصوتي'), findsOneWidget);

    // Play button should be disabled (onPressed == null)
    final playBtn = tester.widget<IconButton>(find.byKey(const Key('playPauseButton')));
    expect(playBtn.onPressed, isNull);
  });
}

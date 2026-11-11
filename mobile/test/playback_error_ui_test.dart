import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile/core/audio_playback_service.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/widgets/audio_player_widget.dart';

class ThrowingAudioPlaybackService extends SimulatedAudioPlaybackService {
  bool shouldThrow = true;
  int loadCallCount = 0;

  ThrowingAudioPlaybackService() : super(duration: const Duration(seconds: 60));

  @override
  Future<void> load(String url) async {
    loadCallCount++;
    if (shouldThrow) {
      throw Exception('PlayerException: audio stream failed to load');
    }
    return super.load(url);
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('AudioPlayerWidget surfaces load failure with Arabic message, retry button, and disabled controls', (tester) async {
    final fakeService = ThrowingAudioPlaybackService();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          audioPlaybackProvider.overrideWithValue(fakeService),
        ],
        child: const MaterialApp(
          home: Scaffold(
            body: AudioPlayerWidget(
              audioUrl: 'https://test.asghi.org/api/audio/sample.mp3',
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    // 1. Assert initial load failed
    expect(fakeService.loadCallCount, equals(1));

    // 2. Inline Arabic error message appears
    expect(find.text('تعذر تحميل الملف الصوتي'), findsOneWidget);

    // 3. Retry button must be visible
    final retryBtn = find.byKey(const Key('retryLoadAudioButton'));
    expect(retryBtn, findsOneWidget);

    // 4. Play button must be disabled (null onPressed) and never show playing state
    final playBtn = tester.widget<IconButton>(find.byKey(const Key('playPauseButton')));
    expect(playBtn.onPressed, isNull);
    expect(find.byIcon(Icons.pause_circle_filled), findsNothing);
    expect(find.byIcon(Icons.play_circle_filled), findsOneWidget);

    // 5. Slider must be disabled
    final slider = tester.widget<Slider>(find.byType(Slider));
    expect(slider.onChanged, isNull);

    // 6. Fix backend/stream, tap retry button, and verify load re-invoked
    fakeService.shouldThrow = false;
    await tester.tap(retryBtn);
    await tester.pumpAndSettle();

    expect(fakeService.loadCallCount, equals(2));
    // Error message and retry button should be cleared
    expect(find.text('تعذر تحميل الملف الصوتي'), findsNothing);
    expect(find.byKey(const Key('retryLoadAudioButton')), findsNothing);

    // Play button should now be enabled
    final enabledPlayBtn = tester.widget<IconButton>(find.byKey(const Key('playPauseButton')));
    expect(enabledPlayBtn.onPressed, isNotNull);
  });
}

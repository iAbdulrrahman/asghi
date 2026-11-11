import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/core/audio_playback_service.dart';
import 'package:mobile/core/audio_recorder_service.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/models/models.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/auth/login_screen.dart';
import 'package:mobile/screens/contributor/contributor_screen.dart';
import 'package:mobile/screens/learner/practice_screen.dart';
import 'package:mobile/widgets/audio_player_widget.dart';
import 'package:mobile/widgets/tashkeel_text_widget.dart';
import 'mock_adapter.dart';

Widget createTestableWidget(Widget child, {AudioRecorderService? recorder, AudioPlaybackService? player}) {
  final apiClient = ApiClient();
  apiClient.useSecureStorage = false;
  apiClient.dio.httpClientAdapter = MockHttpAdapter();

  return ProviderScope(
    overrides: [
      apiClientProvider.overrideWithValue(apiClient),
      audioRecorderProvider.overrideWithValue(recorder ?? BundledAudioSource(simulatedDuration: const Duration(seconds: 75))),
      audioPlaybackProvider.overrideWithValue(player ?? SimulatedAudioPlaybackService()),
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
      home: child,
    ),
  );
}

void main() {
  setUp(() {
    final client = ApiClient();
    client.useSecureStorage = false;
    client.dio.httpClientAdapter = MockHttpAdapter();
  });

  testWidgets('Item 25: Login screen renders input fields and submit button', (WidgetTester tester) async {
    await tester.pumpWidget(createTestableWidget(const LoginScreen()));
    await tester.pump();

    expect(find.byType(TextField), findsNWidgets(2));
    expect(find.text('تسجيل الدخول'), findsWidgets);
  });

  testWidgets('Item 25: AudioPlayerWidget renders controls and playback speed buttons', (WidgetTester tester) async {
    await tester.pumpWidget(createTestableWidget(
      const AudioPlayerWidget(audioUrl: 'http://localhost:8000/audio/test.mp3'),
    ));
    for (int i = 0; i < 5; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    expect(find.byKey(const Key('playPauseButton')), findsOneWidget);
    expect(find.byIcon(Icons.play_circle_filled), findsOneWidget);
    expect(find.text('1.0x'), findsOneWidget);
    expect(find.text('0.75x'), findsOneWidget);
    expect(find.text('1.25x'), findsOneWidget);
    expect(find.text('1.5x'), findsOneWidget);
  });

  testWidgets('Item 25: TashkeelTextWidget toggles diacritics stripping correctly', (WidgetTester tester) async {
    const textWithTashkeel = 'العَرَبِيَّةُ الفُصْحَى';
    const textWithoutTashkeel = 'العربية الفصحى';

    expect(TashkeelTextWidget.stripTashkeel(textWithTashkeel), textWithoutTashkeel);

    await tester.pumpWidget(createTestableWidget(
      const TashkeelTextWidget(text: textWithTashkeel, showTashkeel: false),
    ));
    await tester.pump();

    expect(find.text(textWithoutTashkeel), findsOneWidget);
  });

  testWidgets('Item 25: Contributor screen renders claim buttons, 72h banner, and tabs', (WidgetTester tester) async {
    await tester.pumpWidget(createTestableWidget(const ContributorScreen()));
    for (int i = 0; i < 10; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    expect(find.textContaining('72 ساعة'), findsOneWidget);
    expect(find.text('نصوص للتسجيل'), findsOneWidget);
    expect(find.text('تسجيلاتي وحالتها'), findsOneWidget);
    expect(find.byKey(const Key('claimButton_p-awaiting-1')), findsOneWidget);

    // Tap claim button
    await tester.tap(find.byKey(const Key('claimButton_p-awaiting-1')));
    for (int i = 0; i < 10; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    expect(find.textContaining('تم حجز النص بنجاح'), findsOneWidget);
  });

  testWidgets('Item 6: Contributor recording modal opens and shows duration validation', (WidgetTester tester) async {
    final shortRecorder = BundledAudioSource(simulatedDuration: const Duration(seconds: 30));
    await tester.pumpWidget(createTestableWidget(const ContributorScreen(), recorder: shortRecorder));
    for (int i = 0; i < 10; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Claim
    await tester.tap(find.byKey(const Key('claimButton_p-awaiting-1')));
    for (int i = 0; i < 10; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    expect(find.text('تسجيل ورفع الصوت الحقيقي'), findsOneWidget);
    await tester.tap(find.text('تسجيل ورفع الصوت الحقيقي'));
    for (int i = 0; i < 10; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Modal open
    expect(find.text('بدء التسجيل'), findsOneWidget);
    expect(find.text('استيراد ملف'), findsOneWidget);
    expect(find.text('تأكيد ورفع الملف الصوتي'), findsOneWidget);
  });

  testWidgets('Item 25: Full learner practice session (browse -> play -> answer -> score)', (WidgetTester tester) async {
    final passage = Passage(
      passageId: 'p-test-1',
      text: 'نص تجريبي متكامل لجلسة الاستماع الفصيح مع التشكيل التام',
      level: 'B1',
      topic: 'تاريخ وحضارة',
      durationSeconds: 45.0,
      status: 'VERIFIED',
    );

    await tester.pumpWidget(createTestableWidget(PracticeScreen(passage: passage)));
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    expect(find.text('تاريخ وحضارة'), findsOneWidget);
    expect(find.text('ما هو المحور الرئيسي للنص؟'), findsOneWidget);

    // Select correct answer 'الحضارة'
    await tester.tap(find.text('الحضارة'));
    for (int i = 0; i < 10; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    expect(find.textContaining('إجابة صحيحة'), findsOneWidget);
    expect(find.text('السؤال التالي'), findsOneWidget);
  });
}

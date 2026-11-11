import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/models/models.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/auth/login_screen.dart';
import 'package:mobile/screens/contributor/contributor_screen.dart';
import 'package:mobile/screens/learner/practice_screen.dart';
import 'package:mobile/widgets/audio_player_widget.dart';
import 'package:mobile/widgets/tashkeel_text_widget.dart';
import 'mock_adapter.dart';

Widget createTestableWidget(Widget child) {
  final apiClient = ApiClient();
  apiClient.useSecureStorage = false;
  apiClient.dio.httpClientAdapter = MockHttpAdapter();

  return ProviderScope(
    overrides: [
      apiClientProvider.overrideWithValue(apiClient),
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

    expect(find.byKey(const Key('identifierField')), findsOneWidget);
    expect(find.byKey(const Key('passwordField')), findsOneWidget);
    expect(find.byKey(const Key('loginButton')), findsOneWidget);
    expect(find.text('تسجيل الدخول'), findsWidgets);
  });

  testWidgets('Item 25: AudioPlayerWidget renders controls and playback speed buttons', (WidgetTester tester) async {
    double selectedSpeed = 1.0;
    await tester.pumpWidget(createTestableWidget(
      AudioPlayerWidget(
        audioUrl: '/audio/sample.mp3',
        onSpeedChanged: (s) => selectedSpeed = s,
      ),
    ));
    await tester.pump();

    expect(find.byIcon(Icons.play_circle_filled), findsOneWidget);
    expect(find.text('0.75x'), findsOneWidget);
    expect(find.text('1.0x'), findsOneWidget);
    expect(find.text('1.25x'), findsOneWidget);

    // Tap speed choice chip
    await tester.tap(find.text('1.25x'));
    await tester.pump();
    expect(selectedSpeed, 1.25);
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

  testWidgets('Item 25: Contributor screen renders claim buttons and 72h banner', (WidgetTester tester) async {
    await tester.pumpWidget(createTestableWidget(const ContributorScreen()));
    for (int i = 0; i < 5; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    expect(find.textContaining('72 ساعة'), findsOneWidget);
    expect(find.byKey(const Key('claimButton_p-awaiting-1')), findsOneWidget);

    // Tap claim button
    await tester.tap(find.byKey(const Key('claimButton_p-awaiting-1')));
    for (int i = 0; i < 5; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    expect(find.textContaining('تم حجز النص بنجاح'), findsOneWidget);
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
    for (int i = 0; i < 6; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Verify passage topic and player loaded
    expect(find.text('تاريخ وحضارة'), findsOneWidget);
    expect(find.byIcon(Icons.play_circle_filled), findsOneWidget);

    // Verify question is loaded
    expect(find.byKey(const Key('questionCard')), findsOneWidget);
    expect(find.text('ما هو المحور الرئيسي للنص؟'), findsOneWidget);
    expect(find.text('الحضارة'), findsOneWidget);

    // Tap correct option
    await tester.tap(find.text('الحضارة'));
    for (int i = 0; i < 5; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Verify instant explanation and score progression
    expect(find.textContaining('إجابة صحيحة'), findsOneWidget);
    expect(find.textContaining('النقاط: 20'), findsOneWidget);
    expect(find.textContaining('شرح مفصل يؤكد صحة الإجابة الحضارية'), findsOneWidget);
  });
}

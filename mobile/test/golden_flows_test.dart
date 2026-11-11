import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/core/audio_playback_service.dart';
import 'package:mobile/core/audio_recorder_service.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/models/models.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/admin/admin_screen.dart';
import 'package:mobile/screens/auth/login_screen.dart';
import 'package:mobile/screens/contributor/contributor_screen.dart';
import 'package:mobile/screens/learner/practice_screen.dart';
import 'package:mobile/screens/reviewer/reviewer_screen.dart';
import 'mock_adapter.dart';

Widget testableWidget(Widget child) {
  final client = ApiClient();
  client.useSecureStorage = false;
  client.dio.httpClientAdapter = MockHttpAdapter();

  return ProviderScope(
    overrides: [
      apiClientProvider.overrideWithValue(client),
      audioRecorderProvider.overrideWithValue(BundledAudioSource()),
      audioPlaybackProvider.overrideWithValue(SimulatedAudioPlaybackService()),
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
      home: Scaffold(body: child),
    ),
  );
}

void main() {
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    final fontLoader = FontLoader('NotoNaskhArabic');
    final fontFile = File('assets/fonts/NotoNaskhArabic.ttf');
    if (fontFile.existsSync()) {
      final fontBytes = fontFile.readAsBytesSync();
      fontLoader.addFont(Future.value(ByteData.view(fontBytes.buffer)));
      await fontLoader.load();
    }
  });

  testWidgets('Capture Flow 1 - Contributor Screen', (WidgetTester tester) async {
    await tester.pumpWidget(testableWidget(const ContributorScreen()));
    await tester.pump();
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }
    await expectLater(find.byType(ContributorScreen), matchesGoldenFile('goldens/flow_1.png'));
  });

  testWidgets('Capture Flow 2 - Reviewer Screen', (WidgetTester tester) async {
    await tester.pumpWidget(testableWidget(const ReviewerScreen()));
    await tester.pump();
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }
    await expectLater(find.byType(ReviewerScreen), matchesGoldenFile('goldens/flow_2.png'));
  });

  testWidgets('Capture Flow 3 - Practice Screen', (WidgetTester tester) async {
    final passage = Passage(
      passageId: 'p-gold-1',
      text: 'نص تجريبي فصيح لجلسة الاستماع التكيفي',
      level: 'B1',
      topic: 'تاريخ وحضارة',
      durationSeconds: 60.0,
      status: 'VERIFIED',
      audioRecordings: [
        AudioRecording(
          recordingId: 'rec-gold-1',
          audioFile: 'sample_fusha_01.mp3',
          audioUrl: '/api/audio/sample_fusha_01.mp3',
          durationSeconds: 60.0,
          status: 'VERIFIED',
          attribution: 'SHOW_NAME',
        ),
      ],
    );
    await tester.pumpWidget(testableWidget(PracticeScreen(passage: passage)));
    await tester.pump();
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }
    await expectLater(find.byType(PracticeScreen), matchesGoldenFile('goldens/flow_3.png'));
  });

  testWidgets('Capture Flow 4 - Login Screen', (WidgetTester tester) async {
    await tester.pumpWidget(testableWidget(const LoginScreen()));
    await tester.pumpAndSettle();
    await expectLater(find.byType(LoginScreen), matchesGoldenFile('goldens/flow_4.png'));
  });

  testWidgets('Capture Flow 5 - Admin Screen', (WidgetTester tester) async {
    await tester.pumpWidget(testableWidget(const AdminScreen()));
    await tester.pump();
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }
    await expectLater(find.byType(AdminScreen), matchesGoldenFile('goldens/flow_5.png'));
  });

  tearDownAll(() {
    // Copy generated goldens to mobile/docs/flow_{1..5}.png
    for (int i = 1; i <= 5; i++) {
      final src = File('test/goldens/flow_$i.png');
      final dst = File('docs/flow_$i.png');
      if (src.existsSync()) {
        dst.parent.createSync(recursive: true);
        src.copySync(dst.path);
      }
    }
  });
}

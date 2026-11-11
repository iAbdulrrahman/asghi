import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/core/audio_recorder_service.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/contributor/contributor_screen.dart';
import 'mock_adapter.dart';

class FailingAudioRecorder implements AudioRecorderService {
  @override
  Future<bool> hasPermission() async => false;

  @override
  Future<bool> requestPermission() async => false;

  @override
  Future<void> startRecording(String path) async {
    throw PlatformException(code: 'PERMISSION_DENIED', message: 'Microphone permission denied');
  }

  @override
  Future<String?> stopRecording() async => null;

  @override
  Future<void> cancelRecording() async {}

  @override
  Future<bool> isRecording() async => false;

  @override
  Future<String?> pickAudioFile() async => null;
}

void main() {
  testWidgets('Audio recording failure displays Arabic error SnackBar and resets UI', (tester) async {
    final mockAdapter = MockHttpAdapter();
    final apiClient = ApiClient();
    apiClient.useSecureStorage = false;
    apiClient.dio.httpClientAdapter = mockAdapter;

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(apiClient),
          audioRecorderProvider.overrideWithValue(FailingAudioRecorder()),
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
          home: const ContributorScreen(),
        ),
      ),
    );

    await tester.pump();
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Step 1: Claim passage
    final claimButton = find.text('حجز النص للتسجيل');
    expect(claimButton, findsOneWidget);
    await tester.tap(claimButton);

    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Step 2: Open recording modal
    final recordModalButton = find.text('تسجيل ورفع الصوت الحقيقي');
    expect(recordModalButton, findsOneWidget);
    await tester.tap(recordModalButton);

    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Step 3: Now inside modal, find "بدء التسجيل" button
    final startButton = find.text('بدء التسجيل');
    expect(startButton, findsOneWidget);

    // Tap "بدء التسجيل"
    await tester.tap(startButton);
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Should catch error, show SnackBar, and remain in start recording state
    expect(find.text('تعذر بدء التسجيل الصوتي'), findsOneWidget);
    expect(find.text('بدء التسجيل'), findsOneWidget);
  });
}

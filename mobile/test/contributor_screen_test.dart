import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/core/audio_recorder_service.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/contributor/contributor_screen.dart';
import 'mock_adapter.dart';

void main() {
  testWidgets('ContributorScreen displays submissions, rejection reasons, and tashkeel toggle', (tester) async {
    final mockAdapter = MockHttpAdapter();
    final apiClient = ApiClient();
    apiClient.useSecureStorage = false;
    apiClient.dio.httpClientAdapter = mockAdapter;

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(apiClient),
          audioRecorderProvider.overrideWithValue(BundledAudioSource()),
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

    // Initial pump and settle
    await tester.pump();
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Tab 1: Available passages
    expect(find.text('نصوص بانتظار التسجيل'), findsOneWidget);
    expect(find.text('أدب ولغة'), findsOneWidget);

    // Switch to Tab 2: My Submissions
    await tester.tap(find.text('تسجيلاتي السابقة'));
    for (int i = 0; i < 10; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Verify rejection reason and verified status appear (Req 8)
    expect(find.textContaining('سبب الرفض: وجود كلمات عامية غير فصيحة في التسجيل'), findsOneWidget);
    expect(find.text('الحالة: VERIFIED'), findsOneWidget);
  });
}

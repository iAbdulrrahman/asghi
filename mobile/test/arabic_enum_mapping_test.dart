import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/core/arabic_display.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/admin/admin_screen.dart';
import 'mock_adapter.dart';

void main() {
  group('ArabicDisplay mappings', () {
    test('Translates ContentType, ContentStatus, AttributionType, Origin, Difficulty, Level', () {
      expect(ArabicDisplay.contentType('PASSAGE'), 'نص قرائي');
      expect(ArabicDisplay.contentType('AUDIO_RECORDING'), 'تسجيل صوتي');
      expect(ArabicDisplay.contentType('QUESTION'), 'سؤال استيعاب');

      expect(ArabicDisplay.status('PENDING_REVIEW'), 'قيد المراجعة');
      expect(ArabicDisplay.status('VERIFIED'), 'معتمد');
      expect(ArabicDisplay.status('DRAFT'), 'مسودة');
      expect(ArabicDisplay.status('FLAGGED'), 'مبلّغ عنه');
      expect(ArabicDisplay.status('PENDING'), 'معلق');

      expect(ArabicDisplay.attribution('SHOW_NAME'), 'ذكر الاسم');
      expect(ArabicDisplay.attribution('ANONYMOUS'), 'مجهول (بدون اسم)');

      expect(ArabicDisplay.origin('AI'), 'ذكاء اصطناعي');
      expect(ArabicDisplay.origin('HUMAN'), 'بشري');

      expect(ArabicDisplay.difficulty('EASY'), 'سهل');
      expect(ArabicDisplay.difficulty('MEDIUM'), 'متوسط');
      expect(ArabicDisplay.difficulty('HARD'), 'متقدم');
    });
  });

  testWidgets('AdminScreen renders Arabic translation for flag content type and status', (tester) async {
    final mockAdapter = MockHttpAdapter();
    final apiClient = ApiClient();
    apiClient.useSecureStorage = false;
    apiClient.dio.httpClientAdapter = mockAdapter;

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(apiClient)],
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
          home: const AdminScreen(),
        ),
      ),
    );

    await tester.pump();
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Switch to Flags tab
    await tester.tap(find.text('البلاغات والنزاعات'));
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Must NOT contain raw English enum PASSAGE
    expect(find.textContaining('بلاغ عن PASSAGE'), findsNothing);
    expect(find.textContaining('بلاغ عن نص قرائي'), findsOneWidget);
    expect(find.text('معلق'), findsWidgets);
  });
}

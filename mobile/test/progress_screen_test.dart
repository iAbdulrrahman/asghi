import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/learner/progress_screen.dart';
import 'mock_adapter.dart';

void main() {
  testWidgets('ProgressScreen fetches /api/learner/progress and renders metrics', (tester) async {
    final mockAdapter = MockHttpAdapter();
    final apiClient = ApiClient();
    apiClient.useSecureStorage = false;
    apiClient.dio.httpClientAdapter = mockAdapter;

    await tester.pumpWidget(
      ProviderScope(
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
          home: const ProgressScreen(),
        ),
      ),
    );

    // Initial loading frame
    await tester.pump();
    // Allow async API responses to complete
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Verify UI displays metrics from /api/learner/progress
    expect(find.text('إحصائيات التقدم'), findsOneWidget);
    expect(find.text('إجمالي النقاط'), findsOneWidget);
    expect(find.text('150'), findsOneWidget);
    expect(find.text('أيام التدريب المتتالية'), findsOneWidget);
    expect(find.text('3'), findsOneWidget);
    expect(find.text('الاختبارات المكتملة'), findsOneWidget);
    expect(find.text('5'), findsOneWidget);
  });
}

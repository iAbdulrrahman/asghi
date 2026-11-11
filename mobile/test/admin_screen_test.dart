import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/admin/admin_screen.dart';
import 'mock_adapter.dart';

void main() {
  testWidgets('AdminScreen renders dashboard metrics, flags, disputes, and reports', (tester) async {
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
          home: const AdminScreen(),
        ),
      ),
    );

    // Initial pump and settle
    await tester.pump();
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Verify Tab 1: Dashboard metrics
    expect(find.text('لوحة المؤشرات'), findsOneWidget);
    expect(find.text('إجمالي المستخدمين'), findsOneWidget);
    expect(find.text('120'), findsOneWidget);

    // Switch to Tab 2: Flags & Disputes
    await tester.tap(find.text('البلاغات والنزاعات'));
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    expect(find.textContaining('محتوى غير لائق يتطلب مراجعة المشرف'), findsOneWidget);
    expect(find.text('إبقاء المحتوى'), findsOneWidget);
    expect(find.text('إزالة المحتوى'), findsOneWidget);
  });
}

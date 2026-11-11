import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/learner/progress_screen.dart';
import 'mock_adapter.dart';

void main() {
  testWidgets('ProgressScreen fetches /api/learner/progress and renders metrics', (tester) async {
    final mockAdapter = MockHttpAdapter();
    final apiClient = ApiClient();
    apiClient.dio.httpClientAdapter = mockAdapter;

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(apiClient),
        ],
        child: const MaterialApp(
          home: ProgressScreen(),
        ),
      ),
    );

    // Initial loading
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    // Let async network requests complete
    await tester.pumpAndSettle();

    // Verify UI displays metrics from /api/learner/progress
    expect(find.text('إحصائيات التقدم'), findsOneWidget);
    expect(find.text('إجمالي النقاط'), findsOneWidget);
    expect(find.text('150'), findsOneWidget);
    expect(find.text('أيام التدريب المتتالية'), findsOneWidget);
    expect(find.text('3'), findsOneWidget);
  });
}

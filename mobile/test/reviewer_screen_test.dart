import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/core/audio_playback_service.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/reviewer/reviewer_screen.dart';
import 'mock_adapter.dart';

void main() {
  testWidgets('ReviewerScreen renders audio queue and question review queue', (tester) async {
    final mockAdapter = MockHttpAdapter();
    final apiClient = ApiClient();
    apiClient.useSecureStorage = false;
    apiClient.dio.httpClientAdapter = mockAdapter;

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(apiClient),
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
          home: const ReviewerScreen(),
        ),
      ),
    );

    // Initial pump and settle
    await tester.pump();
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Tab 1: Audio recordings review queue
    expect(find.text('تدقيق التسجيلات'), findsOneWidget);
    expect(find.textContaining('أدب عربي'), findsOneWidget);
    expect(find.text('مطابقة كاملة للغة العربية الفصحى'), findsOneWidget);

    // Switch to Tab 2: Question review queue
    await tester.tap(find.text('تدقيق الأسئلة'));
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Verify pending question appears
    expect(find.textContaining('سؤال للمراجعة: ما الفكرة العامة؟'), findsOneWidget);
    expect(find.text('اعتماد السؤال'), findsOneWidget);
  });
}

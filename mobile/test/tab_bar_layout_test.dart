import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/core/audio_recorder_service.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/contributor/contributor_screen.dart';
import 'package:mobile/screens/reviewer/reviewer_screen.dart';
import 'mock_adapter.dart';

void main() {
  testWidgets('ContributorScreen TabBar is wrapped in explicit PreferredSize >= 48 without overflow', (tester) async {
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

    await tester.pump();
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Verify explicit PreferredSize wrapping
    final preferredSizeFinder = find.descendant(
      of: find.byType(AppBar),
      matching: find.byType(PreferredSize),
    );
    expect(preferredSizeFinder, findsOneWidget, reason: 'TabBar in ContributorScreen must be wrapped in explicit PreferredSize');

    final tabBarFinder = find.byType(TabBar);
    expect(tabBarFinder, findsOneWidget);
    final size = tester.getSize(tabBarFinder);
    expect(size.height >= 48.0, isTrue, reason: 'TabBar height must be >= 48dp to prevent collapse');
  });

  testWidgets('ReviewerScreen TabBar is wrapped in explicit PreferredSize >= 48 without overflow', (tester) async {
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
          home: const ReviewerScreen(),
        ),
      ),
    );

    await tester.pump();
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    final preferredSizeFinder = find.descendant(
      of: find.byType(AppBar),
      matching: find.byType(PreferredSize),
    );
    expect(preferredSizeFinder, findsOneWidget, reason: 'TabBar in ReviewerScreen must be wrapped in explicit PreferredSize');

    final tabBarFinder = find.byType(TabBar);
    expect(tabBarFinder, findsOneWidget);
    final size = tester.getSize(tabBarFinder);
    expect(size.height >= 48.0, isTrue, reason: 'TabBar height must be >= 48dp to prevent collapse');
  });
}

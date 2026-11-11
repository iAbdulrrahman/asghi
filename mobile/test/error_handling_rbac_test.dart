import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/models/models.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/auth/login_screen.dart';
import 'package:mobile/screens/home_screen.dart';
import 'mock_adapter.dart';

void main() {
  testWidgets('401 response logs out and returns to LoginScreen', (tester) async {
    final mockAdapter = MockHttpAdapter();
    final apiClient = ApiClient();
    apiClient.useSecureStorage = false;
    apiClient.dio.httpClientAdapter = mockAdapter;

    final container = ProviderContainer(
      overrides: [
        apiClientProvider.overrideWithValue(apiClient),
      ],
    );

    // Initial state: authenticated as contributor
    final testUser = User(
      userId: 'u-1',
      displayName: 'القارئ',
      email: 'contributor@asghi.org',
      arabicLevel: 'B1',
      roles: [UserRole.contributor],
    );
    container.read(authProvider.notifier).setAuthenticatedUserForTesting(testUser, UserRole.contributor);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
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
          home: Consumer(
            builder: (context, ref, _) {
              final auth = ref.watch(authProvider);
              return auth.isAuthenticated ? const HomeScreen() : const LoginScreen();
            },
          ),
        ),
      ),
    );

    await tester.pump();
    expect(find.textContaining('المساهمة'), findsOneWidget);

    // Trigger 401 callback
    apiClient.onUnauthorized?.call();
    await tester.pumpAndSettle();

    // Now state is unauthenticated, rendering LoginScreen
    expect(find.text('تسجيل الدخول'), findsWidgets);
  });

  testWidgets('Role-based view only presents authorized tabs for active role', (tester) async {
    final mockAdapter = MockHttpAdapter();
    final apiClient = ApiClient();
    apiClient.useSecureStorage = false;
    apiClient.dio.httpClientAdapter = mockAdapter;

    final container = ProviderContainer(
      overrides: [
        apiClientProvider.overrideWithValue(apiClient),
      ],
    );

    // Authenticated as Learner
    final learnerUser = User(
      userId: 'u-learner',
      displayName: 'المتعلم',
      email: 'learner@asghi.org',
      arabicLevel: 'B1',
      roles: [UserRole.learner, UserRole.contributor],
    );
    container.read(authProvider.notifier).setAuthenticatedUserForTesting(learnerUser, UserRole.learner);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
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
          home: const HomeScreen(),
        ),
      ),
    );

    await tester.pump();
    // Learner tabs present
    expect(find.text('المكتبة'), findsOneWidget);
    expect(find.text('التقدم'), findsOneWidget);
    // Reviewer and Admin tabs NOT present
    expect(find.text('المراجعة'), findsNothing);
    expect(find.text('الإدارة'), findsNothing);
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile/core/constants.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/screens/auth/login_screen.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    // Reset to default
    await ApiClient().setBaseUrl(null);
  });

  tearDown(() async {
    await ApiClient().setBaseUrl(null);
  });

  group('Item 1: Runtime-configurable API base URL & Normalization', () {
    test('Normalizes missing scheme and trailing slashes correctly', () {
      expect(
        AppConstants.normalizeAndValidateServerUrl('http://10.0.2.2:8000/'),
        equals('http://10.0.2.2:8000'),
      );
      expect(
        AppConstants.normalizeAndValidateServerUrl('https://invoicing.0xabdul.dev/'),
        equals('https://invoicing.0xabdul.dev'),
      );
      expect(
        AppConstants.normalizeAndValidateServerUrl('invoicing.0xabdul.dev'),
        equals('https://invoicing.0xabdul.dev'),
      );
      expect(
        AppConstants.normalizeAndValidateServerUrl('10.0.2.2:8000'),
        equals('http://10.0.2.2:8000'),
      );
      expect(
        AppConstants.normalizeAndValidateServerUrl('invalid_uri_!@#\$'),
        isNull,
      );
    });

    test('Setting override updates ApiClient and audio URL composer; clearing reverts to default', () async {
      final defaultUrl = AppConstants.defaultApiBaseUrl;
      expect(AppConstants.apiBaseUrl, equals(defaultUrl));
      expect(ApiClient().dio.options.baseUrl, equals(defaultUrl));

      // 1. Set override
      await ApiClient().setBaseUrl('https://custom.asghi.org');
      expect(AppConstants.apiBaseUrl, equals('https://custom.asghi.org'));
      expect(ApiClient().dio.options.baseUrl, equals('https://custom.asghi.org'));

      // 2. Audio URL composer uses live value
      final audioUrl = AppConstants.resolveAudioUrl('/api/audio/sample.mp3');
      expect(audioUrl, equals('https://custom.asghi.org/api/audio/sample.mp3'));

      // 3. Clear override -> reverts to default
      await ApiClient().setBaseUrl(null);
      expect(AppConstants.apiBaseUrl, equals(defaultUrl));
      expect(ApiClient().dio.options.baseUrl, equals(defaultUrl));
      expect(
        AppConstants.resolveAudioUrl('/api/audio/sample.mp3'),
        equals('$defaultUrl/api/audio/sample.mp3'),
      );
    });

    testWidgets('LoginScreen allows changing server address via dialog', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: LoginScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Find server settings button in AppBar
      final settingsBtn = find.byKey(const Key('server_settings_button'));
      expect(settingsBtn, findsOneWidget);
      await tester.tap(settingsBtn);
      await tester.pumpAndSettle();

      // Dialog should be visible
      expect(find.text('إعدادات عنوان الخادم'), findsOneWidget);
      final inputField = find.byKey(const Key('server_address_field'));
      expect(inputField, findsOneWidget);

      // Enter new server address
      await tester.enterText(inputField, 'https://wonder.0xabdul.dev');
      final saveBtn = find.byKey(const Key('server_address_save_button'));
      await tester.tap(saveBtn);
      await tester.pumpAndSettle();

      // Live base URL should be updated
      expect(AppConstants.apiBaseUrl, equals('https://wonder.0xabdul.dev'));
      expect(ApiClient().dio.options.baseUrl, equals('https://wonder.0xabdul.dev'));
    });
  });
}

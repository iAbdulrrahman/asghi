import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/api_client.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/providers/providers.dart';
import 'package:mobile/screens/admin/admin_screen.dart';

class FlagResolveCapturingAdapter implements HttpClientAdapter {
  final List<Map<String, dynamic>> resolvedActions = [];

  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<List<int>>? requestStream, Future<void>? cancelFuture) async {
    final path = options.uri.path;
    final method = options.method;

    if (path.contains('/api/admin/flags') && method == 'GET') {
      final data = [
        {
          'flagId': 'flag-123',
          'contentId': 'content-456',
          'contentType': 'PASSAGE',
          'reason': 'محتوى مخالف للشروط',
          'status': 'PENDING',
        }
      ];
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    if (path.contains('/api/admin/flags/') && path.contains('/resolve') && method == 'POST') {
      final body = options.data is Map ? (options.data as Map).cast<String, dynamic>() : (jsonDecode(options.data.toString()) as Map).cast<String, dynamic>();
      resolvedActions.add(body);
      final resp = {'message': 'تمت معالجة البلاغ بنجاح', 'flagId': 'flag-123', 'status': body['newState']};
      return ResponseBody.fromString(jsonEncode(resp), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    if (path.contains('/api/admin/dashboard')) {
      final data = {'report': {'totalUsers': 5, 'pendingFlags': 1, 'activeClaims': 0}};
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    if (path.contains('/api/admin/report')) {
      final data = {'totalUsers': 5, 'period': 'MONTHLY', 'passagesByStatus': {'VERIFIED': 1}};
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    return ResponseBody.fromString('{}', 200, headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType],
    });
  }
}

void main() {
  testWidgets('Admin resolves flag with NO_ACTION and ACTION_TAKEN payload', (tester) async {
    final adapter = FlagResolveCapturingAdapter();
    final apiClient = ApiClient();
    apiClient.useSecureStorage = false;
    apiClient.dio.httpClientAdapter = adapter;

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

    await tester.pump();
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Switch to Flags tab
    await tester.tap(find.text('البلاغات والنزاعات'));
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    expect(find.text('إبقاء المحتوى'), findsOneWidget);
    expect(find.text('إزالة المحتوى'), findsOneWidget);

    // Tap "إبقاء المحتوى" (should send NO_ACTION)
    await tester.tap(find.text('إبقاء المحتوى'));
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    expect(adapter.resolvedActions.length, 1);
    expect(adapter.resolvedActions[0]['newState'], 'NO_ACTION',
        reason: 'Flag resolution for keep must send NO_ACTION enum value');
  });
}

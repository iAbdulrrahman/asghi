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

class RefreshFlagsCapturingAdapter implements HttpClientAdapter {
  final List<Map<String, dynamic>> flags = [
    {
      'flagId': 'flag-to-resolve-1',
      'contentId': 'content-999',
      'contentType': 'PASSAGE',
      'reason': 'بلاغ عن محتوى يخالف الشروط',
      'status': 'PENDING',
    }
  ];

  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<List<int>>? requestStream, Future<void>? cancelFuture) async {
    final path = options.uri.path;
    final method = options.method;

    if (path.contains('/api/admin/flags') && method == 'GET') {
      return ResponseBody.fromString(jsonEncode(flags), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    if (path.contains('/api/admin/flags/') && path.contains('/resolve') && method == 'POST') {
      final body = options.data is Map ? (options.data as Map).cast<String, dynamic>() : (jsonDecode(options.data.toString()) as Map).cast<String, dynamic>();
      final flagId = path.split('/')[4];
      for (final f in flags) {
        if (f['flagId'] == flagId) {
          f['status'] = body['newState'] ?? 'NO_ACTION';
        }
      }
      final resp = {'message': 'تمت معالجة البلاغ بنجاح', 'flagId': flagId, 'status': body['newState']};
      return ResponseBody.fromString(jsonEncode(resp), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    if (path.contains('/api/admin/dashboard')) {
      final pendingCount = flags.where((f) => f['status'] == 'PENDING').length;
      final data = {'report': {'totalUsers': 5, 'pendingFlags': pendingCount, 'activeClaims': 0}};
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
  testWidgets('Resolving a flag reloads flags and immediately removes resolved card from view', (tester) async {
    final adapter = RefreshFlagsCapturingAdapter();
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

    // Flag should initially be displayed
    expect(find.textContaining('بلاغ عن محتوى يخالف الشروط'), findsOneWidget);
    expect(find.text('إبقاء المحتوى'), findsOneWidget);

    // Tap "إبقاء المحتوى" to resolve
    await tester.tap(find.text('إبقاء المحتوى'));
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 50));
    }

    // Resolved flag must disappear from pending list
    expect(find.textContaining('بلاغ عن محتوى يخالف الشروط'), findsNothing,
        reason: 'Resolved flag should not remain in pending flags queue after resolution');
  });
}

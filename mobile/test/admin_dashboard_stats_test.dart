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

class RealDashboardMetricsAdapter implements HttpClientAdapter {
  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<List<int>>? requestStream, Future<void>? cancelFuture) async {
    final path = options.uri.path;

    if (path.contains('/api/admin/dashboard')) {
      final realBackendJson = {
        'report': {
          'period': 'MONTHLY',
          'totalUsers': 5,
          'totalPassages': 3,
          'verifiedPassages': 4,
          'pendingRecordings': 2,
          'totalFlags': 1,
          'disputesCount': 0,
        },
        'users': [
          {'userId': 'u-1', 'displayName': 'مدير النظام', 'email': 'admin@asghi.org', 'roles': ['ADMIN'], 'status': 'ACTIVE'},
        ],
      };
      return ResponseBody.fromString(jsonEncode(realBackendJson), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    if (path.contains('/api/admin/report')) {
      final data = {
        'period': 'MONTHLY',
        'totalUsers': 5,
        'passagesByStatus': {'VERIFIED': 4, 'DRAFT': 1, 'PENDING': 1},
      };
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    if (path.contains('/api/admin/flags')) {
      final data = [
        {'flagId': 'f-1', 'reason': 'بلاغ تجريبي', 'status': 'PENDING'}
      ];
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
  testWidgets('AdminScreen accurately parses nested report metrics from live backend response', (tester) async {
    final apiClient = ApiClient();
    apiClient.useSecureStorage = false;
    apiClient.dio.httpClientAdapter = RealDashboardMetricsAdapter();

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

    // Verify Tab 1 (Dashboard) shows non-zero real values matching report
    expect(find.text('لوحة المؤشرات'), findsOneWidget);
    expect(find.text('5'), findsOneWidget, reason: 'Total users must be 5');
    expect(find.text('3'), findsOneWidget, reason: 'Total passages must be 3');
    expect(find.text('4'), findsOneWidget, reason: 'Verified recordings/passages must be 4');
  });
}

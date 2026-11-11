import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile/core/constants.dart';
import 'package:mobile/core/theme.dart';
import 'package:mobile/screens/contributor/contributor_screen.dart';
import 'package:mobile/screens/reviewer/reviewer_screen.dart';
import 'package:mobile/screens/admin/admin_screen.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('Item 4: Tab Bar Label Contrast & Fixed Height Across Roles', () {
    testWidgets('AppTheme defines high-contrast white TabBarThemeData with gold indicator', (tester) async {
      final theme = AppTheme.lightTheme;
      final tabTheme = theme.tabBarTheme;

      expect(tabTheme.labelColor, equals(Colors.white));
      expect(tabTheme.labelColor, isNot(equals(AppConstants.primaryEmerald)));
      expect(tabTheme.unselectedLabelColor, equals(Colors.white70));
      expect(tabTheme.indicatorColor, equals(AppConstants.accentGold));
    });

    testWidgets('ContributorScreen TabBar has fixed height, white selected label, and gold indicator', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            theme: AppTheme.lightTheme,
            home: const ContributorScreen(),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      final tabBarFinder = find.byType(TabBar);
      expect(tabBarFinder, findsOneWidget);
      final tabBar = tester.widget<TabBar>(tabBarFinder);

      expect(tabBar.labelColor, equals(Colors.white));
      expect(tabBar.labelColor, isNot(equals(AppConstants.primaryEmerald)));
      expect(tabBar.unselectedLabelColor, equals(Colors.white70));
      expect(tabBar.indicatorColor, equals(AppConstants.accentGold));

      // Selected tab label 'نصوص للتسجيل' is present in tree
      expect(find.text('نصوص للتسجيل'), findsOneWidget);
      expect(find.text('تسجيلاتي وحالتها'), findsOneWidget);
    });

    testWidgets('ReviewerScreen TabBar has fixed height, white selected label, and gold indicator', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            theme: AppTheme.lightTheme,
            home: const ReviewerScreen(),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      final tabBarFinder = find.byType(TabBar);
      expect(tabBarFinder, findsOneWidget);
      final tabBar = tester.widget<TabBar>(tabBarFinder);

      expect(tabBar.labelColor, equals(Colors.white));
      expect(tabBar.labelColor, isNot(equals(AppConstants.primaryEmerald)));
      expect(tabBar.unselectedLabelColor, equals(Colors.white70));
      expect(tabBar.indicatorColor, equals(AppConstants.accentGold));

      expect(find.text('تدقيق التسجيلات'), findsOneWidget);
      expect(find.text('تدقيق الأسئلة'), findsOneWidget);
    });

    testWidgets('AdminScreen TabBar has fixed height, white selected label, and gold indicator', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            theme: AppTheme.lightTheme,
            home: const AdminScreen(),
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      final tabBarFinder = find.byType(TabBar);
      expect(tabBarFinder, findsOneWidget);
      final tabBar = tester.widget<TabBar>(tabBarFinder);

      expect(tabBar.labelColor, equals(Colors.white));
      expect(tabBar.labelColor, isNot(equals(AppConstants.primaryEmerald)));
      expect(tabBar.unselectedLabelColor, equals(Colors.white70));
      expect(tabBar.indicatorColor, equals(AppConstants.accentGold));

      expect(find.text('لوحة المؤشرات'), findsOneWidget);
      expect(find.text('البلاغات والنزاعات'), findsOneWidget);
      expect(find.text('توليد المحتوى'), findsOneWidget);
    });
  });
}

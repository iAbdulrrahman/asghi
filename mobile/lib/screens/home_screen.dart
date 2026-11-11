import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/constants.dart';
import '../models/models.dart';
import '../providers/providers.dart';
import '../widgets/offline_banner.dart';
import 'admin/admin_screen.dart';
import 'contributor/contributor_screen.dart';
import 'learner/catalogue_screen.dart';
import 'learner/progress_screen.dart';
import 'reviewer/reviewer_screen.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final user = authState.user;
    final activeRole = authState.activeRole;
    final isOffline = ref.watch(isOfflineProvider);

    // Build tabs based on active role
    final List<Widget> tabs = [];
    final List<BottomNavigationBarItem> navItems = [];

    if (activeRole == UserRole.learner) {
      tabs.addAll([const CatalogueScreen(), const ProgressScreen()]);
      navItems.addAll([
        const BottomNavigationBarItem(icon: Icon(Icons.library_books), label: 'المكتبة'),
        const BottomNavigationBarItem(icon: Icon(Icons.insights), label: 'التقدم'),
      ]);
    } else if (activeRole == UserRole.contributor) {
      tabs.addAll([const ContributorScreen()]);
      navItems.addAll([
        const BottomNavigationBarItem(icon: Icon(Icons.mic), label: 'المساهمة'),
      ]);
    } else if (activeRole == UserRole.reviewer) {
      tabs.addAll([const ReviewerScreen()]);
      navItems.addAll([
        const BottomNavigationBarItem(icon: Icon(Icons.fact_check), label: 'المراجعة'),
      ]);
    } else if (activeRole == UserRole.admin) {
      tabs.addAll([const AdminScreen()]);
      navItems.addAll([
        const BottomNavigationBarItem(icon: Icon(Icons.admin_panel_settings), label: 'الإدارة'),
      ]);
    }

    final safeIndex = _currentIndex < tabs.length ? _currentIndex : 0;

    return Scaffold(
      appBar: AppBar(
        title: Text('${AppConstants.appNameArabic} — ${activeRole.displayNameArabic}'),
        actions: [
          // Role switcher if user has multiple roles
          if ((user?.roles.length ?? 0) > 1)
            PopupMenuButton<UserRole>(
              icon: const Icon(Icons.swap_horiz),
              tooltip: 'تبديل الدور',
              onSelected: (role) {
                ref.read(authProvider.notifier).switchRole(role);
                setState(() => _currentIndex = 0);
              },
              itemBuilder: (ctx) => user!.roles.map((r) {
                return PopupMenuItem(
                  value: r,
                  child: Row(
                    children: [
                      if (r == activeRole) const Icon(Icons.check, size: 18),
                      const SizedBox(width: 8),
                      Text(r.displayNameArabic),
                    ],
                  ),
                );
              }).toList(),
            ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'تسجيل الخروج',
            onPressed: () => ref.read(authProvider.notifier).logout(),
          ),
        ],
      ),
      body: Column(
        children: [
          OfflineBanner(
            isOffline: isOffline,
            onRetry: () => ref.read(isOfflineProvider.notifier).setOffline(false),
          ),
          Expanded(child: tabs.isNotEmpty ? tabs[safeIndex] : const SizedBox.shrink()),
        ],
      ),
      bottomNavigationBar: navItems.length > 1
          ? BottomNavigationBar(
              currentIndex: safeIndex,
              selectedItemColor: AppConstants.primaryEmerald,
              onTap: (idx) => setState(() => _currentIndex = idx),
              items: navItems,
            )
          : null,
    );
  }
}

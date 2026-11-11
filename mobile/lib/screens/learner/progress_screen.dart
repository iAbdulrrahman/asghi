import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_client.dart';
import '../../core/constants.dart';
import '../../providers/providers.dart';

class ProgressScreen extends ConsumerStatefulWidget {
  const ProgressScreen({super.key});

  @override
  ConsumerState<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends ConsumerState<ProgressScreen> {
  Map<String, dynamic>? _userProfile;
  Map<String, dynamic>? _progressData;
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadProgress();
  }

  Future<void> _loadProgress() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final client = ref.read(apiClientProvider);
    try {
      // 1. Fetch user profile for display name / header
      try {
        final meResp = await client.dio.get('/api/users/me');
        final rawUser = ApiClient.parseData(meResp.data);
        if (rawUser is Map<String, dynamic>) {
          _userProfile = rawUser;
        }
      } catch (_) {
        // Fallback gracefully if /api/users/me fails
      }

      // 2. Fetch authoritative Learner Progress (Req 6.6)
      final progResp = await client.dio.get('/api/learner/progress');
      final rawProg = ApiClient.parseData(progResp.data);
      if (mounted) {
        setState(() {
          _progressData = rawProg is Map<String, dynamic> ? rawProg : null;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = 'تعذر تحميل بيانات التقدم: $e';
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_errorMessage != null && _progressData == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('إحصائيات التقدم')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(_errorMessage!, style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _loadProgress,
                icon: const Icon(Icons.refresh),
                label: const Text('إعادة المحاولة'),
              ),
            ],
          ),
        ),
      );
    }

    final score = _progressData?['totalScore'] ?? 0;
    final timeSpent = _progressData?['totalTimeSpent'] ?? _progressData?['listeningTimeSeconds'] ?? 0;
    final streak = _progressData?['currentStreakDays'] ?? _progressData?['currentStreak'] ?? _progressData?['streak'] ?? 0;
    final completedTests = _progressData?['completedTests'] ?? 0;
    final displayName = _userProfile?['displayName'] ?? 'المتعلم';
    final arabicLevel = _userProfile?['arabicLevel'] ?? 'B1';

    return Scaffold(
      appBar: AppBar(
        title: const Text('إحصائيات التقدم'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadProgress,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadProgress,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // User Header Card
            Card(
              elevation: 2,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    const CircleAvatar(
                      radius: 28,
                      backgroundColor: AppConstants.primaryEmerald,
                      child: Icon(Icons.person, size: 32, color: Colors.white),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            displayName,
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'المستوى اللغوي: $arabicLevel',
                            style: const TextStyle(color: Colors.grey),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Key Metrics Grid
            Row(
              children: [
                Expanded(
                  child: _buildMetricCard(
                    title: 'إجمالي النقاط',
                    value: '$score',
                    icon: Icons.star,
                    color: AppConstants.accentGold,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildMetricCard(
                    title: 'أيام التدريب المتتالية',
                    value: '$streak',
                    icon: Icons.local_fire_department,
                    color: Colors.deepOrange,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            Row(
              children: [
                Expanded(
                  child: _buildMetricCard(
                    title: 'وقت الاستماع',
                    value: '${(timeSpent / 60).toStringAsFixed(1)} دقيقة',
                    icon: Icons.timer,
                    color: AppConstants.primaryLight,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildMetricCard(
                    title: 'الاختبارات المكتملة',
                    value: '$completedTests',
                    icon: Icons.task_alt,
                    color: AppConstants.successGreen,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Achievements Section
            const Text(
              'أوسمة الإنجاز',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            ListTile(
              leading: const CircleAvatar(
                backgroundColor: AppConstants.primaryEmerald,
                child: Icon(Icons.hearing, color: Colors.white),
              ),
              title: const Text('مستمع مبتدئ'),
              subtitle: const Text('أكمل أول جلسة تدريب استماع فصيح'),
              trailing: Icon(
                completedTests > 0 || score > 0 ? Icons.check_circle : Icons.lock,
                color: completedTests > 0 || score > 0 ? Colors.green : Colors.grey,
              ),
            ),
            ListTile(
              leading: const CircleAvatar(
                backgroundColor: AppConstants.accentGold,
                child: Icon(Icons.bolt, color: Colors.black87),
              ),
              title: const Text('متسابق الدقة'),
              subtitle: const Text('أجب عن 5 أسئلة متتالية بشكل صحيح'),
              trailing: Icon(
                score >= 100 ? Icons.check_circle : Icons.lock,
                color: score >= 100 ? Colors.green : Colors.grey,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(icon, size: 36, color: color),
            const SizedBox(height: 8),
            Text(title, textAlign: TextAlign.center, style: const TextStyle(fontSize: 13, color: Colors.grey)),
            const SizedBox(height: 4),
            Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }
}

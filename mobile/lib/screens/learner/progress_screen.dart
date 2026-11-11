import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants.dart';
import '../../providers/providers.dart';

class ProgressScreen extends ConsumerStatefulWidget {
  const ProgressScreen({super.key});

  @override
  ConsumerState<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends ConsumerState<ProgressScreen> {
  Map<String, dynamic>? _progressData;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProgress();
  }

  void _loadProgress() async {
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.get('/api/users/me');
      final profiles = (resp.data['profiles'] as List<dynamic>?) ?? [];
      final learnerProf = profiles.firstWhere(
        (p) => p['role'] == 'LEARNER',
        orElse: () => null,
      );
      if (mounted) {
        setState(() {
          _progressData = learnerProf?['progress'];
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final score = _progressData?['totalScore'] ?? 0;
    final timeSpent = _progressData?['totalTimeSpent'] ?? 0;
    final streak = _progressData?['streak'] ?? 0;

    return Scaffold(
      appBar: AppBar(title: const Text('إحصائيات التقدم')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
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
          _buildMetricCard(
            title: 'الوقت المستغرق في الاستماع',
            value: '${(timeSpent / 60).toStringAsFixed(1)} دقيقة',
            icon: Icons.timer,
            color: AppConstants.primaryLight,
          ),
          const SizedBox(height: 24),
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
            trailing: Icon(score > 0 ? Icons.check_circle : Icons.lock, color: score > 0 ? Colors.green : Colors.grey),
          ),
          ListTile(
            leading: const CircleAvatar(
              backgroundColor: AppConstants.accentGold,
              child: Icon(Icons.bolt, color: Colors.black87),
            ),
            title: const Text('متسابق الدقة'),
            subtitle: const Text('أجب عن 5 أسئلة متتالية بشكل صحيح'),
            trailing: Icon(score >= 100 ? Icons.check_circle : Icons.lock, color: score >= 100 ? Colors.green : Colors.grey),
          ),
        ],
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
            Text(title, style: const TextStyle(fontSize: 13, color: Colors.grey)),
            const SizedBox(height: 4),
            Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }
}

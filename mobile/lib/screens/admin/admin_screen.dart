import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_client.dart';
import '../../core/constants.dart';
import '../../providers/providers.dart';

class AdminScreen extends ConsumerStatefulWidget {
  const AdminScreen({super.key});

  @override
  ConsumerState<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends ConsumerState<AdminScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic>? _dashboardData;
  Map<String, dynamic>? _reportData;
  List<dynamic> _flaggedItems = [];
  bool _isLoading = true;

  // AI Generation Tool State
  final _aiTopicController = TextEditingController(text: 'الثقافة والعلوم');
  String _aiLevel = 'B1';

  // Dispute Resolution State
  final _disputeContentIdController = TextEditingController();

  // Report period
  String _selectedPeriod = 'MONTHLY';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadAllAdminData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _aiTopicController.dispose();
    _disputeContentIdController.dispose();
    super.dispose();
  }

  Future<void> _loadAllAdminData() async {
    setState(() => _isLoading = true);
    await Future.wait([
      _loadDashboard(),
      _loadReport(_selectedPeriod),
      _loadFlags(),
    ]);
    if (mounted) setState(() => _isLoading = false);
  }

  Future<void> _loadDashboard() async {
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.get('/api/admin/dashboard');
      final raw = ApiClient.parseData(resp.data);
      if (mounted) {
        setState(() {
          _dashboardData = raw is Map<String, dynamic> ? raw : null;
        });
      }
    } catch (_) {}
  }

  Future<void> _loadReport(String period) async {
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.get('/api/admin/report', queryParameters: {'period': period});
      final raw = ApiClient.parseData(resp.data);
      if (mounted) {
        setState(() {
          _selectedPeriod = period;
          _reportData = raw is Map<String, dynamic> ? raw : null;
        });
      }
    } catch (_) {}
  }

  Future<void> _loadFlags() async {
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.get('/api/admin/flags');
      final raw = ApiClient.parseData(resp.data);
      if (mounted) {
        setState(() {
          _flaggedItems = (raw as List<dynamic>?) ?? [];
        });
      }
    } catch (_) {}
  }

  Future<void> _resolveFlag(String flagId, String newState) async {
    final client = ref.read(apiClientProvider);
    try {
      await client.dio.post('/api/admin/flags/$flagId/resolve', data: {
        'newState': newState,
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('تمت معالجة البلاغ بنجاح'), backgroundColor: AppConstants.successGreen),
        );
        _loadFlags();
        _loadDashboard();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('فشل معالجة البلاغ: $e'), backgroundColor: AppConstants.errorRed),
        );
      }
    }
  }

  Future<void> _resolveDispute(String contentId, String action) async {
    if (contentId.trim().isEmpty) return;
    final client = ref.read(apiClientProvider);
    try {
      await client.dio.post('/api/admin/disputes/${contentId.trim()}/resolve', data: {
        'action': action,
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(action == 'VERIFY' ? 'تم اعتماد المحتوى وحل النزاع' : 'تم رفض المحتوى وحل النزاع'),
            backgroundColor: action == 'VERIFY' ? AppConstants.successGreen : AppConstants.errorRed,
          ),
        );
        _disputeContentIdController.clear();
        _loadFlags();
        _loadDashboard();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('فشل حل النزاع: $e'), backgroundColor: AppConstants.errorRed),
        );
      }
    }
  }

  Future<void> _triggerAiGeneration() async {
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.post('/api/admin/generate', data: {
        'topic': _aiTopicController.text.trim(),
        'level': _aiLevel,
      });
      final raw = ApiClient.parseData(resp.data);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('تم توليد النص بنجاح: ${raw?['topic'] ?? _aiTopicController.text}'),
            backgroundColor: AppConstants.successGreen,
          ),
        );
        _loadDashboard();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('فشل توليد النص: $e'), backgroundColor: AppConstants.errorRed),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('لوحة تحكم المشرف (Admin)'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'لوحة المؤشرات', icon: Icon(Icons.dashboard)),
            Tab(text: 'البلاغات والنزاعات', icon: Icon(Icons.shield)),
            Tab(text: 'توليد المحتوى', icon: Icon(Icons.auto_awesome)),
          ],
        ),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadAllAdminData),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                // Tab 1: Dashboard & Reports (Req 10.2)
                RefreshIndicator(
                  onRefresh: _loadAllAdminData,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      _buildDashboardMetrics(),
                      const SizedBox(height: 16),
                      _buildReportingSection(),
                    ],
                  ),
                ),

                // Tab 2: Flags & Dispute Resolution (Req 5.4, 6.7, 10.2)
                RefreshIndicator(
                  onRefresh: _loadAllAdminData,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      _buildDisputeResolutionCard(),
                      const SizedBox(height: 16),
                      const Text(
                        'قائمة البلاغات المعلقة والمراجعة',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      if (_flaggedItems.isEmpty)
                        const Center(
                          child: Padding(
                            padding: EdgeInsets.all(32),
                            child: Text('لا توجد بلاغات معلقة حالياً'),
                          ),
                        )
                      else
                        ..._flaggedItems.map((flag) => _buildFlagCard(flag)),
                    ],
                  ),
                ),

                // Tab 3: AI Generation (Req 3.1, 3.2, 3.3)
                RefreshIndicator(
                  onRefresh: _loadAllAdminData,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      _buildAiGenerationCard(),
                    ],
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildDashboardMetrics() {
    final report = _dashboardData?['report'] is Map ? (_dashboardData!['report'] as Map) : (_dashboardData ?? {});
    final totalUsers = report['totalUsers'] ?? _dashboardData?['totalUsers'] ?? (_dashboardData?['users'] as List?)?.length ?? 0;
    final totalPassages = report['totalPassages'] ?? _dashboardData?['totalPassages'] ?? 0;
    final verifiedRecordings = report['verifiedPassages'] ?? report['verifiedRecordings'] ?? _dashboardData?['verifiedRecordings'] ?? 0;
    final pendingFlags = report['totalFlags'] ?? report['pendingFlags'] ?? _dashboardData?['pendingFlags'] ?? _flaggedItems.length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text(
          'المؤشرات الإحصائية العامة',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildMetricTile(
                title: 'إجمالي المستخدمين',
                value: '$totalUsers',
                icon: Icons.people,
                color: AppConstants.primaryEmerald,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildMetricTile(
                title: 'إجمالي النصوص',
                value: '$totalPassages',
                icon: Icons.menu_book,
                color: AppConstants.accentGold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildMetricTile(
                title: 'التسجيلات المعتمدة',
                value: '$verifiedRecordings',
                icon: Icons.verified,
                color: AppConstants.successGreen,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildMetricTile(
                title: 'البلاغات المعلقة',
                value: '$pendingFlags',
                icon: Icons.flag,
                color: AppConstants.errorRed,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildMetricTile({
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
            Icon(icon, size: 32, color: color),
            const SizedBox(height: 8),
            Text(title, textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, color: Colors.grey)),
            const SizedBox(height: 4),
            Text(value, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  Widget _buildReportingSection() {
    final report = _reportData ?? {};
    final turnaround = report['reviewTurnaroundHours'] ?? 0.0;
    final passagesByStatus = (report['passagesByStatus'] as Map<String, dynamic>?) ?? {};

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('تقرير الأداء والمراجعة', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                DropdownButton<String>(
                  value: _selectedPeriod,
                  items: const [
                    DropdownMenuItem(value: 'MONTHLY', child: Text('شهري')),
                    DropdownMenuItem(value: 'ALL_TIME', child: Text('كلي')),
                  ],
                  onChanged: (v) {
                    if (v != null) _loadReport(v);
                  },
                ),
              ],
            ),
            const Divider(),
            Text('متوسط زمن إنجاز المراجعة: $turnaround ساعة'),
            const SizedBox(height: 8),
            const Text('توزيع النصوص حسب الحالة:', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            Wrap(
              spacing: 8,
              children: passagesByStatus.entries.map((e) {
                return Chip(label: Text('${e.key}: ${e.value}'));
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDisputeResolutionCard() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('فض النزاعات وتدقيق الخلافات (Req 5.4)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 8),
            const Text(
              'في حال تعارض قرارات المراجعين، يتولى المشرف الفصل النهائي في المحتوى.',
              style: TextStyle(color: Colors.grey, fontSize: 13),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _disputeContentIdController,
              decoration: const InputDecoration(
                labelText: 'معرف المحتوى المتنازع عليه (Content ID)',
                hintText: 'أدخل UUID للمحتوى',
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(backgroundColor: AppConstants.successGreen),
                    icon: const Icon(Icons.check_circle),
                    label: const Text('اعتماد المحتوى'),
                    onPressed: () => _resolveDispute(_disputeContentIdController.text, 'VERIFY'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(foregroundColor: AppConstants.errorRed),
                    icon: const Icon(Icons.cancel),
                    label: const Text('رفض المحتوى'),
                    onPressed: () => _resolveDispute(_disputeContentIdController.text, 'REJECT'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFlagCard(dynamic flag) {
    final flagId = (flag['flagId'] ?? '').toString();
    final reason = flag['reason'] ?? 'بدون سبب';
    final contentType = flag['contentType'] ?? 'محتوى';
    final status = flag['status'] ?? 'PENDING';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(Icons.report_problem, color: AppConstants.errorRed),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'بلاغ عن $contentType: $reason',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                Chip(label: Text(status)),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(backgroundColor: AppConstants.primaryEmerald),
                    onPressed: () => _resolveFlag(flagId, 'NO_ACTION'),
                    child: const Text('إبقاء المحتوى'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton(
                    style: OutlinedButton.styleFrom(foregroundColor: AppConstants.errorRed),
                    onPressed: () => _resolveFlag(flagId, 'ACTION_TAKEN'),
                    child: const Text('إزالة المحتوى'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAiGenerationCard() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'توليد محتوى جديد بالذكاء الاصطناعي (Req 3.1, 3.2)',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 8),
            const Text(
              'توليد نصوص فصيحة وأسئلة فهم متعددة الصعوبة متوازنة لتكون قيد التدقيق البشري.',
              style: TextStyle(color: Colors.grey, fontSize: 13),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _aiTopicController,
              decoration: const InputDecoration(labelText: 'موضوع النص'),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _aiLevel,
              decoration: const InputDecoration(labelText: 'المستوى اللغوي'),
              items: ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
                  .map((lvl) => DropdownMenuItem(value: lvl, child: Text(lvl)))
                  .toList(),
              onChanged: (v) => setState(() => _aiLevel = v ?? 'B1'),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              icon: const Icon(Icons.auto_awesome),
              label: const Text('توليد بالذكاء الاصطناعي وحفظ كمسودة'),
              onPressed: _triggerAiGeneration,
            ),
          ],
        ),
      ),
    );
  }
}

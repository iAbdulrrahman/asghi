import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants.dart';
import '../../providers/providers.dart';

class AdminScreen extends ConsumerStatefulWidget {
  const AdminScreen({super.key});

  @override
  ConsumerState<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends ConsumerState<AdminScreen> {
  List<dynamic> _flaggedItems = [];
  bool _isLoading = true;
  final _aiTopicController = TextEditingController(text: 'الثقافة والعلوم');
  String _aiLevel = 'B1';

  @override
  void initState() {
    super.initState();
    _loadFlags();
  }

  @override
  void dispose() {
    _aiTopicController.dispose();
    super.dispose();
  }

  void _loadFlags() async {
    setState(() => _isLoading = true);
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.get('/api/admin/flags');
      if (mounted) {
        setState(() {
          _flaggedItems = (resp.data as List<dynamic>?) ?? [];
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _resolveFlag(String flagId, String action) async {
    final client = ref.read(apiClientProvider);
    try {
      await client.dio.post('/api/admin/flags/$flagId/resolve', data: {
        'action': action, // 'ACTION_TAKEN' or 'NO_ACTION'
        'notes': 'تمت المراجعة من المشرف',
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('تمت معالجة البلاغ بنجاح'), backgroundColor: AppConstants.successGreen),
        );
        _loadFlags();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('فشل معالجة البلاغ: $e')),
        );
      }
    }
  }

  void _triggerAiGeneration() async {
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.post('/api/admin/generate-passage', data: {
        'topic': _aiTopicController.text.trim(),
        'level': _aiLevel,
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('تم توليد النص بالذكاء الاصطناعي: ${resp.data['topic']}'),
            backgroundColor: AppConstants.successGreen,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('فشل توليد النص: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('لوحة تحكم المشرف (Admin)'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadFlags),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // AI Generation Tool Card
          Card(
            elevation: 2,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text('توليد محتوى جديد بالذكاء الاصطناعي', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _aiTopicController,
                    decoration: const InputDecoration(labelText: 'موضوع النص'),
                  ),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    initialValue: _aiLevel,
                    decoration: const InputDecoration(labelText: 'المستوى المستهدف'),
                    items: ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
                        .map((l) => DropdownMenuItem(value: l, child: Text(l)))
                        .toList(),
                    onChanged: (v) => setState(() => _aiLevel = v ?? 'B1'),
                  ),
                  const SizedBox(height: 12),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.auto_awesome),
                    label: const Text('توليد النص الصوتي والأسئلة'),
                    onPressed: _triggerAiGeneration,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          const Text('قائمة بلاغات المحتوى قيد المعالجة', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          const SizedBox(height: 8),
          if (_isLoading)
            const Center(child: CircularProgressIndicator())
          else if (_flaggedItems.isEmpty)
            const Card(child: Padding(padding: EdgeInsets.all(16), child: Text('لا توجد بلاغات معلقة')))
          else
            ..._flaggedItems.map((flag) {
              final flagId = flag['flagId'] ?? flag['flag_id'];
              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text('سبب البلاغ: ${flag['reason'] ?? ""}', style: const TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 4),
                      Text('الحالة: ${flag['status'] ?? ""}'),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: ElevatedButton(
                              style: ElevatedButton.styleFrom(backgroundColor: AppConstants.errorRed),
                              onPressed: () => _resolveFlag(flagId, 'ACTION_TAKEN'),
                              child: const Text('حظر المحتوى (Action Taken)'),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: OutlinedButton(
                              onPressed: () => _resolveFlag(flagId, 'NO_ACTION'),
                              child: const Text('رفض البلاغ (No Action)'),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              );
            }),
        ],
      ),
    );
  }
}

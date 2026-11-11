import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants.dart';
import '../../providers/providers.dart';
import '../../widgets/audio_player_widget.dart';

class ReviewerScreen extends ConsumerStatefulWidget {
  const ReviewerScreen({super.key});

  @override
  ConsumerState<ReviewerScreen> createState() => _ReviewerScreenState();
}

class _ReviewerScreenState extends ConsumerState<ReviewerScreen> {
  List<dynamic> _assignments = [];
  bool _isLoading = true;

  // Review form states
  bool _isFusha = true;
  bool _dialectFree = true;
  int _audioQuality = 5;
  final _reasonController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadQueue();
  }

  @override
  void dispose() {
    _reasonController.dispose();
    super.dispose();
  }

  void _loadQueue() async {
    setState(() => _isLoading = true);
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.get('/api/reviewer/assignments');
      if (mounted) {
        setState(() {
          _assignments = (resp.data as List<dynamic>?) ?? [];
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _submitVerdict(String assignmentId, bool isApproved) async {
    final client = ref.read(apiClientProvider);
    try {
      await client.dio.post('/api/reviewer/decision', data: {
        'assignmentId': assignmentId,
        'isFusha': _isFusha,
        'dialectFree': _dialectFree,
        'audioQuality': _audioQuality,
        'isApproved': isApproved,
        'reason': _reasonController.text.trim(),
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(isApproved ? 'تم اعتماد التسجيل بنجاح' : 'تم رفض التسجيل وإرسال الملاحظات للمساهم'),
            backgroundColor: isApproved ? AppConstants.successGreen : AppConstants.errorRed,
          ),
        );
        _reasonController.clear();
        _loadQueue();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('فشل تسجيل القرار: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('قائمة تدقيق الجودة والمراجعة'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadQueue),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _assignments.isEmpty
              ? const Center(child: Text('لا توجد تسجيلات قيد التدقيق حالياً'))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _assignments.length,
                  itemBuilder: (ctx, i) {
                    final a = _assignments[i];
                    final passage = a['passage'];
                    final assignmentId = a['assignmentId'] ?? a['assignment_id'];

                    return Card(
                      margin: const EdgeInsets.only(bottom: 16),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Text(
                              'النص المراد تدقيقه: ${passage?['topic'] ?? ""}',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                            ),
                            const SizedBox(height: 8),
                            Text(passage?['text'] ?? "", maxLines: 3, overflow: TextOverflow.ellipsis),
                            const SizedBox(height: 12),
                            AudioPlayerWidget(audioUrl: a['audioUrl'] ?? a['audio_url'] ?? ''),
                            const Divider(),
                            const Text('معايير الفصاحة والتدقيق:', style: TextStyle(fontWeight: FontWeight.bold)),
                            CheckboxListTile(
                              title: const Text('مطابقة كاملة للغة العربية الفصحى'),
                              value: _isFusha,
                              onChanged: (v) => setState(() => _isFusha = v ?? true),
                            ),
                            CheckboxListTile(
                              title: const Text('خلو تام من اللهجات والمؤثرات العامية'),
                              value: _dialectFree,
                              onChanged: (v) => setState(() => _dialectFree = v ?? true),
                            ),
                            Row(
                              children: [
                                const Text('جودة ونقاء الصوت (1 - 5): '),
                                DropdownButton<int>(
                                  value: _audioQuality,
                                  items: [1, 2, 3, 4, 5]
                                      .map((q) => DropdownMenuItem(value: q, child: Text('$q نجوم')))
                                      .toList(),
                                  onChanged: (v) => setState(() => _audioQuality = v ?? 5),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            TextField(
                              controller: _reasonController,
                              decoration: const InputDecoration(
                                labelText: 'ملاحظات التدقيق (في حال الرفض أو التوجيه)',
                              ),
                            ),
                            const SizedBox(height: 16),
                            Row(
                              children: [
                                Expanded(
                                  child: ElevatedButton.icon(
                                    style: ElevatedButton.styleFrom(backgroundColor: AppConstants.successGreen),
                                    icon: const Icon(Icons.check),
                                    label: const Text('اعتماد'),
                                    onPressed: () => _submitVerdict(assignmentId, true),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: OutlinedButton.icon(
                                    style: OutlinedButton.styleFrom(foregroundColor: AppConstants.errorRed),
                                    icon: const Icon(Icons.close),
                                    label: const Text('رفض'),
                                    onPressed: () => _submitVerdict(assignmentId, false),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}

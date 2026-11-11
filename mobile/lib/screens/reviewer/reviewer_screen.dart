import 'package:mobile/core/arabic_display.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_client.dart';
import '../../core/constants.dart';
import '../../providers/providers.dart';
import '../../widgets/audio_player_widget.dart';

class ReviewerScreen extends ConsumerStatefulWidget {
  const ReviewerScreen({super.key});

  @override
  ConsumerState<ReviewerScreen> createState() => _ReviewerScreenState();
}

class _ReviewerScreenState extends ConsumerState<ReviewerScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<dynamic> _pendingRecordings = [];
  List<dynamic> _pendingQuestions = [];
  bool _isLoadingRecordings = true;
  bool _isLoadingQuestions = true;

  // Review form states for audio
  bool _isFusha = true;
  bool _dialectFree = true;
  int _audioQuality = 5;
  final Map<String, TextEditingController> _reasonControllers = {};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadQueues();
  }

  @override
  void dispose() {
    _tabController.dispose();
    for (final c in _reasonControllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  TextEditingController _getController(String id) {
    return _reasonControllers.putIfAbsent(id, () => TextEditingController());
  }

  void _loadQueues() {
    _loadPendingRecordings();
    _loadPendingQuestions();
  }

  Future<void> _loadPendingRecordings() async {
    setState(() => _isLoadingRecordings = true);
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.get('/api/reviewer/pending-recordings');
      final raw = ApiClient.parseData(resp.data);
      if (mounted) {
        setState(() {
          _pendingRecordings = (raw as List<dynamic>?) ?? [];
          _isLoadingRecordings = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoadingRecordings = false);
    }
  }

  Future<void> _loadPendingQuestions() async {
    setState(() => _isLoadingQuestions = true);
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.get('/api/reviewer/pending-questions');
      final raw = ApiClient.parseData(resp.data);
      if (mounted) {
        setState(() {
          _pendingQuestions = (raw as List<dynamic>?) ?? [];
          _isLoadingQuestions = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoadingQuestions = false);
    }
  }

  Future<void> _submitAudioVerdict(String recordingId, bool isApproved) async {
    final client = ref.read(apiClientProvider);
    final reason = _getController(recordingId).text.trim();

    try {
      // 1. Assign review to obtain assignmentId
      final assignResp = await client.dio.post('/api/reviewer/assignments', data: {
        'contentId': recordingId,
      });
      final assignData = ApiClient.parseData(assignResp.data);
      final assignmentId = assignData['assignmentId'] ?? assignData['assignment_id'];

      // 2. Submit verdict decision
      await client.dio.post('/api/reviewer/decision', data: {
        'assignmentId': assignmentId,
        'isFusha': _isFusha,
        'dialectFree': _dialectFree,
        'audioQuality': _audioQuality,
        'isApproved': isApproved,
        'reason': reason,
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(isApproved ? 'تم اعتماد التسجيل بنجاح' : 'تم رفض التسجيل وإرسال الملاحظات للمساهم'),
            backgroundColor: isApproved ? AppConstants.successGreen : AppConstants.errorRed,
          ),
        );
        _getController(recordingId).clear();
        _loadPendingRecordings();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('فشل تسجيل القرار: $e'), backgroundColor: AppConstants.errorRed),
        );
      }
    }
  }

  Future<void> _submitQuestionVerdict(String questionId, bool isApproved) async {
    final client = ref.read(apiClientProvider);
    final reason = _getController(questionId).text.trim();

    try {
      await client.dio.post('/api/reviewer/questions/$questionId/review', data: {
        'isApproved': isApproved,
        'reason': reason,
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(isApproved ? 'تم اعتماد السؤال ونشره' : 'تم رفض السؤال وحجبه'),
            backgroundColor: isApproved ? AppConstants.successGreen : AppConstants.errorRed,
          ),
        );
        _getController(questionId).clear();
        _loadPendingQuestions();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('فشل تدقيق السؤال: $e'), backgroundColor: AppConstants.errorRed),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('قائمة تدقيق الجودة والمراجعة'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(48),
          child: TabBar(
            controller: _tabController,
            tabs: const [
              Tab(text: 'تدقيق التسجيلات', icon: Icon(Icons.record_voice_over)),
              Tab(text: 'تدقيق الأسئلة', icon: Icon(Icons.quiz)),
            ],
          ),
        ),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadQueues),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Tab 1: Audio Recordings Queue (Req 5.1, 5.2, 5.5)
          RefreshIndicator(
            onRefresh: _loadPendingRecordings,
            child: _isLoadingRecordings
                ? const Center(child: CircularProgressIndicator())
                : _pendingRecordings.isEmpty
                    ? const Center(child: Text('لا توجد تسجيلات قيد التدقيق حالياً'))
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _pendingRecordings.length,
                        itemBuilder: (ctx, i) {
                          final item = _pendingRecordings[i];
                          final recordingId = (item['recordingId'] ?? item['contentId'] ?? '').toString();
                          final topic = item['topic'] ?? item['passageTopic'] ?? 'عام';
                          final text = item['passageText'] ?? item['text'] ?? '';
                          final audioUrl = item['audioUrl'] ?? item['audioFile'] ?? '';
                          final duration = item['durationSeconds'] ?? 0;

                          return Card(
                            margin: const EdgeInsets.only(bottom: 16),
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text(
                                        'موضوع النص: $topic',
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                      ),
                                      Chip(label: Text('${duration.toString()} ثانية')),
                                    ],
                                  ),
                                  if (text.isNotEmpty) ...[
                                    const SizedBox(height: 8),
                                    Text(text, maxLines: 3, overflow: TextOverflow.ellipsis),
                                  ],
                                  const SizedBox(height: 12),
                                  AudioPlayerWidget(audioUrl: audioUrl),
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
                                    controller: _getController(recordingId),
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
                                          onPressed: () => _submitAudioVerdict(recordingId, true),
                                        ),
                                      ),
                                      const SizedBox(width: 12),
                                      Expanded(
                                        child: OutlinedButton.icon(
                                          style: OutlinedButton.styleFrom(foregroundColor: AppConstants.errorRed),
                                          icon: const Icon(Icons.close),
                                          label: const Text('رفض'),
                                          onPressed: () => _submitAudioVerdict(recordingId, false),
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
          ),

          // Tab 2: Questions Queue (Req 3.3, 7.3)
          RefreshIndicator(
            onRefresh: _loadPendingQuestions,
            child: _isLoadingQuestions
                ? const Center(child: CircularProgressIndicator())
                : _pendingQuestions.isEmpty
                    ? const Center(child: Text('لا توجد أسئلة قيد المراجعة حالياً'))
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _pendingQuestions.length,
                        itemBuilder: (ctx, i) {
                          final q = _pendingQuestions[i];
                          final questionId = (q['questionId'] ?? '').toString();
                          final prompt = q['promptText'] ?? '';
                          final difficulty = q['difficulty'] ?? 'MEDIUM';
                          final answers = (q['answers'] as List<dynamic>?) ?? [];
                          final origin = q['origin'] ?? 'AI';

                          return Card(
                            margin: const EdgeInsets.only(bottom: 16),
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Chip(
                                        label: Text('الصعوبة: ${ArabicDisplay.difficulty(difficulty)}'),
                                        backgroundColor: AppConstants.accentGold.withValues(alpha: 0.2),
                                      ),
                                      Chip(
                                        label: Text('المصدر: ${ArabicDisplay.origin(origin)}'),
                                        backgroundColor: AppConstants.primaryLight.withValues(alpha: 0.2),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    prompt,
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                  ),
                                  if (answers.isNotEmpty) ...[
                                    const SizedBox(height: 8),
                                    const Text('الخيارات:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                                    ...answers.map((a) => Padding(
                                          padding: const EdgeInsets.symmetric(vertical: 2),
                                          child: Row(
                                            children: [
                                              const Icon(Icons.arrow_left, size: 16),
                                              Text(a.toString()),
                                            ],
                                          ),
                                        )),
                                  ],
                                  const SizedBox(height: 12),
                                  TextField(
                                    controller: _getController(questionId),
                                    decoration: const InputDecoration(
                                      labelText: 'سبب الرفض أو ملاحظات التحسين',
                                    ),
                                  ),
                                  const SizedBox(height: 16),
                                  Row(
                                    children: [
                                      Expanded(
                                        child: ElevatedButton.icon(
                                          style: ElevatedButton.styleFrom(backgroundColor: AppConstants.successGreen),
                                          icon: const Icon(Icons.check),
                                          label: const Text('اعتماد السؤال'),
                                          onPressed: () => _submitQuestionVerdict(questionId, true),
                                        ),
                                      ),
                                      const SizedBox(width: 12),
                                      Expanded(
                                        child: OutlinedButton.icon(
                                          style: OutlinedButton.styleFrom(foregroundColor: AppConstants.errorRed),
                                          icon: const Icon(Icons.close),
                                          label: const Text('رفض السؤال'),
                                          onPressed: () => _submitQuestionVerdict(questionId, false),
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
          ),
        ],
      ),
    );
  }
}

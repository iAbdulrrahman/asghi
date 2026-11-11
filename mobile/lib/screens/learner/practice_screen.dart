import 'package:mobile/core/arabic_display.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_client.dart';
import '../../core/constants.dart';
import '../../models/models.dart';
import '../../providers/providers.dart';
import '../../widgets/audio_player_widget.dart';
import '../../widgets/tashkeel_text_widget.dart';

class PracticeScreen extends ConsumerStatefulWidget {
  final Passage passage;

  const PracticeScreen({super.key, required this.passage});

  @override
  ConsumerState<PracticeScreen> createState() => _PracticeScreenState();
}

class _PracticeScreenState extends ConsumerState<PracticeScreen> {
  bool _showTashkeel = true;
  String? _sessionId;
  Question? _currentQuestion;
  bool _isLoadingQuestion = false;
  bool _isSessionFinished = false;
  int _score = 0;
  String? _selectedAnswer;
  Map<String, dynamic>? _lastAnswerResult;

  @override
  void initState() {
    super.initState();
    _startSession();
  }

  void _startSession() async {
    setState(() => _isLoadingQuestion = true);
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.post('/api/learner/sessions', data: {
        'passageId': widget.passage.passageId,
      });
      final raw = ApiClient.parseData(resp.data);
      _sessionId = raw['sessionId'];
      _fetchNextQuestion();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('تعذر بدء الجلسة: $e')),
        );
        setState(() => _isLoadingQuestion = false);
      }
    }
  }

  void _fetchNextQuestion() async {
    if (_sessionId == null) return;
    setState(() {
      _isLoadingQuestion = true;
      _selectedAnswer = null;
      _lastAnswerResult = null;
    });
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.get('/api/learner/sessions/$_sessionId/question');
      final raw = ApiClient.parseData(resp.data);
      if (raw['done'] == true) {
        _finishSession();
      } else {
        setState(() {
          _currentQuestion = Question.fromJson(raw as Map<String, dynamic>);
          _isLoadingQuestion = false;
        });
      }
    } catch (e) {
      setState(() => _isLoadingQuestion = false);
    }
  }

  void _submitAnswer(String answer) async {
    if (_sessionId == null || _currentQuestion == null) return;
    setState(() {
      _selectedAnswer = answer;
      _isLoadingQuestion = true;
    });
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.post(
        '/api/learner/sessions/$_sessionId/answer',
        data: {
          'questionId': _currentQuestion!.questionId,
          'answer': answer,
          'responseTime': 5.0,
        },
      );
      final raw = ApiClient.parseData(resp.data) as Map<String, dynamic>;
      setState(() {
        _lastAnswerResult = raw;
        _score = raw['totalScore'] ?? _score;
        _isLoadingQuestion = false;
      });
    } catch (e) {
      setState(() => _isLoadingQuestion = false);
    }
  }

  void _finishSession() async {
    if (_sessionId == null) return;
    final client = ref.read(apiClientProvider);
    try {
      await client.dio.post('/api/learner/sessions/$_sessionId/finish');
    } catch (_) {}
    setState(() {
      _isSessionFinished = true;
      _isLoadingQuestion = false;
    });
  }

  String _resolveAudioUrl(AudioRecording? rec) {
    if (rec == null) return '';
    final token = ApiClient().inMemoryToken;
    final url = rec.audioUrl ?? '';
    if (url.isNotEmpty) return AppConstants.resolveAudioUrl(url, token: token);
    if (rec.audioFile.isNotEmpty) return AppConstants.resolveAudioUrl(rec.audioFile, token: token);
    return '';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.passage.topic),
        actions: [
          IconButton(
            icon: Icon(_showTashkeel ? Icons.format_color_text : Icons.text_fields),
            tooltip: 'تبديل التشكيل',
            onPressed: () => setState(() => _showTashkeel = !_showTashkeel),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Audio Player
            AudioPlayerWidget(
              audioUrl: _resolveAudioUrl(widget.passage.verifiedAudio),
            ),
            const SizedBox(height: 16),

            // Passage Text with Tashkeel Toggle
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('نص الاستماع', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        ActionChip(
                          avatar: const Icon(Icons.spellcheck, size: 16),
                          label: Text(_showTashkeel ? 'التشكيل: مفعّل' : 'التشكيل: معطّل'),
                          onPressed: () => setState(() => _showTashkeel = !_showTashkeel),
                        ),
                      ],
                    ),
                    const Divider(),
                    TashkeelTextWidget(
                      text: widget.passage.text,
                      showTashkeel: _showTashkeel,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Question Card or Session Completion
            if (_isSessionFinished) ...[
              Card(
                color: AppConstants.primaryEmerald.withValues(alpha: 0.1),
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      const Icon(Icons.emoji_events, size: 64, color: AppConstants.accentGold),
                      const SizedBox(height: 12),
                      const Text(
                        'أحسنت! اكتملت الجلسة التدريبية',
                        style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      Text('مجموع النقاط المحققة: $_score', style: const TextStyle(fontSize: 18)),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('العودة للمكتبة'),
                      ),
                    ],
                  ),
                ),
              ),
            ] else if (_isLoadingQuestion) ...[
              const Center(child: CircularProgressIndicator()),
            ] else if (_currentQuestion != null) ...[
              Card(
                key: const Key('questionCard'),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Chip(
                            label: Text('الصعوبة: ${ArabicDisplay.difficulty(_currentQuestion!.difficulty)}'),
                            backgroundColor: Colors.teal.shade50,
                          ),
                          Text('النقاط: $_score', style: const TextStyle(fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        _currentQuestion!.promptText,
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                        textDirection: TextDirection.rtl,
                      ),
                      const SizedBox(height: 16),
                      ..._currentQuestion!.answers.map((ans) {
                        final isSelected = _selectedAnswer == ans;
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: isSelected ? AppConstants.primaryLight : Colors.grey.shade100,
                              foregroundColor: isSelected ? Colors.white : Colors.black87,
                            ),
                            onPressed: _selectedAnswer == null ? () => _submitAnswer(ans) : null,
                            child: Text(ans, textDirection: TextDirection.rtl),
                          ),
                        );
                      }),
                      if (_lastAnswerResult != null) ...[
                        const Divider(),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: (_lastAnswerResult!['isCorrect'] == true)
                                ? Colors.green.shade50
                                : Colors.red.shade50,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                (_lastAnswerResult!['isCorrect'] == true) ? 'إجابة صحيحة! 🎉' : 'إجابة خاطئة! ❌',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: (_lastAnswerResult!['isCorrect'] == true)
                                      ? AppConstants.successGreen
                                      : AppConstants.errorRed,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'الشرح: ${_lastAnswerResult!['explanation'] ?? ""}',
                                textDirection: TextDirection.rtl,
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 12),
                        ElevatedButton(
                          onPressed: _fetchNextQuestion,
                          child: const Text('السؤال التالي'),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

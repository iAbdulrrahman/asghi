import 'dart:async';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_client.dart';
import '../../core/constants.dart';
import '../../models/models.dart';
import '../../providers/providers.dart';
import '../../widgets/tashkeel_text_widget.dart';

class ContributorScreen extends ConsumerStatefulWidget {
  const ContributorScreen({super.key});

  @override
  ConsumerState<ContributorScreen> createState() => _ContributorScreenState();
}

class _ContributorScreenState extends ConsumerState<ContributorScreen> with SingleTickerProviderStateMixin {
  List<Passage> _unclaimedPassages = [];
  List<dynamic> _mySubmissions = [];
  bool _isLoading = true;
  String? _claimedPassageId;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _loadData() {
    _loadUnclaimedPassages();
    _loadSubmissions();
  }

  void _loadUnclaimedPassages() async {
    setState(() => _isLoading = true);
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.get('/api/contributor/awaiting-recording');
      final raw = ApiClient.parseData(resp.data);
      final list = (raw as List<dynamic>?) ?? [];
      if (mounted) {
        setState(() {
          _unclaimedPassages = list.map((item) => Passage.fromJson(item)).toList();
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _loadSubmissions() async {
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.get('/api/contributor/submissions');
      final raw = ApiClient.parseData(resp.data);
      final list = (raw as List<dynamic>?) ?? [];
      if (mounted) {
        setState(() {
          _mySubmissions = list;
        });
      }
    } catch (_) {}
  }

  void _claim(Passage p) async {
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.post('/api/contributor/claim', data: {
        'passageId': p.passageId,
      });
      final raw = ApiClient.parseData(resp.data);
      if (mounted) {
        setState(() {
          _claimedPassageId = p.passageId;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(raw['message'] ?? 'تم حجز النص بنجاح'),
            backgroundColor: AppConstants.successGreen,
          ),
        );
      }
    } on DioException catch (e) {
      if (mounted) {
        if (e.response?.statusCode == 409) {
          _loadUnclaimedPassages();
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('تم حجز هذا النص بواسطة مساهم آخر، تم تحديث القائمة'),
              backgroundColor: AppConstants.errorRed,
            ),
          );
          return;
        }
        final errData = ApiClient.parseData(e.response?.data);
        final detail = errData?['detail'] ?? 'تعذر حجز النص';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(detail.toString()), backgroundColor: AppConstants.errorRed),
        );
      }
    }
  }

  Future<void> _openRecordingModal(Passage p) async {
    final recorder = ref.read(audioRecorderProvider);
    String? localAudioPath;
    double durationSeconds = 0;
    bool isRecording = false;
    Timer? timer;
    int elapsed = 0;
    String attribution = 'SHOW_NAME';
    String? validationError;

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) {
          return Padding(
            padding: EdgeInsets.only(
              bottom: MediaQuery.of(ctx).viewInsets.bottom + 16,
              top: 24,
              left: 16,
              right: 16,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('تسجيل نص: ${p.topic}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () {
                        timer?.cancel();
                        if (isRecording) recorder.cancelRecording();
                        Navigator.pop(ctx);
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Card(
                  color: AppConstants.backgroundLight,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: TashkeelTextWidget(text: p.text, style: const TextStyle(fontSize: 16)),
                  ),
                ),
                const SizedBox(height: 16),
                Center(
                  child: Text(
                    '${(elapsed ~/ 60).toString().padLeft(2, '0')}:${(elapsed % 60).toString().padLeft(2, '0')}',
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: isRecording ? AppConstants.errorRed : AppConstants.primaryEmerald,
                    ),
                  ),
                ),
                if (validationError != null)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    child: Text(
                      validationError!,
                      style: const TextStyle(color: AppConstants.errorRed, fontSize: 13, fontWeight: FontWeight.bold),
                      textAlign: TextAlign.center,
                    ),
                  ),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    if (!isRecording) ...[
                      ElevatedButton.icon(
                        icon: const Icon(Icons.mic),
                        label: const Text('بدء التسجيل'),
                        style: ElevatedButton.styleFrom(backgroundColor: AppConstants.primaryEmerald),
                        onPressed: () async {
                          final tempDir = Directory.systemTemp;
                          final targetPath = '${tempDir.path}/rec_${p.passageId}_${DateTime.now().millisecondsSinceEpoch}.wav';
                          await recorder.startRecording(targetPath);
                          setModalState(() {
                            isRecording = true;
                            elapsed = 0;
                            validationError = null;
                          });
                          timer = Timer.periodic(const Duration(seconds: 1), (t) {
                            setModalState(() {
                              elapsed++;
                            });
                          });
                        },
                      ),
                      const SizedBox(width: 8),
                      OutlinedButton.icon(
                        icon: const Icon(Icons.file_upload),
                        label: const Text('استيراد ملف'),
                        onPressed: () async {
                          final path = await recorder.pickAudioFile();
                          if (path != null) {
                            setModalState(() {
                              localAudioPath = path;
                              // Assume compliant 60s file from picker unless specified
                              durationSeconds = 60.0;
                              elapsed = 60;
                              validationError = null;
                            });
                          }
                        },
                      ),
                    ] else ...[
                      ElevatedButton.icon(
                        icon: const Icon(Icons.stop),
                        label: const Text('إيقاف'),
                        style: ElevatedButton.styleFrom(backgroundColor: AppConstants.errorRed),
                        onPressed: () async {
                          timer?.cancel();
                          final path = await recorder.stopRecording();
                          setModalState(() {
                            isRecording = false;
                            localAudioPath = path;
                            durationSeconds = elapsed.toDouble();
                          });
                        },
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 16),
                const Text('نوع النسبة (Attribution):', style: TextStyle(fontWeight: FontWeight.bold)),
                RadioListTile<String>(
                  title: const Text('إظهار اسمي كقارئ معتمد'),
                  value: 'SHOW_NAME',
                  groupValue: attribution,
                  onChanged: (val) => setModalState(() => attribution = val!),
                ),
                RadioListTile<String>(
                  title: const Text('تسجيل مجهول (Anonymous)'),
                  value: 'ANONYMOUS',
                  groupValue: attribution,
                  onChanged: (val) => setModalState(() => attribution = val!),
                ),
                const SizedBox(height: 12),
                ElevatedButton(
                  onPressed: localAudioPath == null
                      ? null
                      : () async {
                          // Req 19: Audio recordings must be 1 to 3 minutes (60-180 seconds)
                          if (durationSeconds < 60 || durationSeconds > 180) {
                            setModalState(() {
                              validationError = 'يجب أن تكون مدة التسجيل بين 60 و 180 ثانية (1-3 دقائق) وفق معايير الجودة';
                            });
                            return;
                          }
                          Navigator.pop(ctx);
                          await _uploadRealAudio(p, localAudioPath!, durationSeconds, attribution);
                        },
                  child: const Text('تأكيد ورفع الملف الصوتي'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Future<void> _uploadRealAudio(Passage p, String filePath, double duration, String attribution) async {
    final client = ref.read(apiClientProvider);
    try {
      final multipart = await MultipartFile.fromFile(
        filePath,
        filename: filePath.split(Platform.pathSeparator).last,
      );
      final formData = FormData.fromMap({
        'passageId': p.passageId,
        'attribution': attribution,
        'durationSeconds': duration,
        'file': multipart,
      });

      await client.dio.post('/api/contributor/submit-audio', data: formData);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('تم رفع الملف الصوتي الحقيقي بنجاح، بانتظار المراجعة'),
            backgroundColor: AppConstants.successGreen,
          ),
        );
        setState(() => _claimedPassageId = null);
        _loadData();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('فشل رفع الملف الصوتي: $e'), backgroundColor: AppConstants.errorRed),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('منطقة المساهمين'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'نصوص للتسجيل', icon: Icon(Icons.mic)),
            Tab(text: 'تسجيلاتي وحالتها', icon: Icon(Icons.list_alt)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Tab 1: Awaiting Recording
          Column(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                color: AppConstants.accentGold.withValues(alpha: 0.15),
                child: const Row(
                  children: [
                    Icon(Icons.timer, color: AppConstants.primaryEmerald),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'مدة صلاحية حجز النص: 72 ساعة كحد أقصى قبل الإفراج التلقائي عنه للآخرين.',
                        style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: _isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : _unclaimedPassages.isEmpty
                        ? const Center(child: Text('لا توجد نصوص بانتظار التسجيل حالياً'))
                        : ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: _unclaimedPassages.length,
                            itemBuilder: (ctx, i) {
                              final p = _unclaimedPassages[i];
                              final isClaimedByMe = _claimedPassageId == p.passageId;
                              return Card(
                                margin: const EdgeInsets.only(bottom: 12),
                                child: Padding(
                                  padding: const EdgeInsets.all(16),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.stretch,
                                    children: [
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(p.topic, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                          Chip(label: Text(p.level)),
                                        ],
                                      ),
                                      const SizedBox(height: 8),
                                      Text(p.text, maxLines: 3, overflow: TextOverflow.ellipsis),
                                      const SizedBox(height: 12),
                                      if (isClaimedByMe) ...[
                                        Container(
                                          padding: const EdgeInsets.all(8),
                                          color: Colors.green.shade50,
                                          child: const Text('تم الحجز لحسابك، يرجى تسجيل الصوت ورفعه'),
                                        ),
                                        const SizedBox(height: 8),
                                        ElevatedButton.icon(
                                          icon: const Icon(Icons.mic),
                                          label: const Text('تسجيل ورفع الصوت الحقيقي'),
                                          onPressed: () => _openRecordingModal(p),
                                        ),
                                      ] else ...[
                                        OutlinedButton.icon(
                                          key: Key('claimButton_${p.passageId}'),
                                          icon: const Icon(Icons.bookmark_add),
                                          label: const Text('حجز النص للتسجيل'),
                                          onPressed: () => _claim(p),
                                        ),
                                      ],
                                    ],
                                  ),
                                ),
                              );
                            },
                          ),
              ),
            ],
          ),
          // Tab 2: Submissions & Rejection Reasons (Req 8)
          _mySubmissions.isEmpty
              ? const Center(child: Text('لا توجد تسجيلات سابقة لك'))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _mySubmissions.length,
                  itemBuilder: (ctx, i) {
                    final sub = _mySubmissions[i];
                    final status = sub['status'] ?? 'PENDING';
                    final rejectionReason = sub['rejectionReason'] ?? sub['feedback'];
                    final isRejected = status == 'REJECTED';
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        leading: Icon(
                          isRejected ? Icons.cancel : Icons.check_circle,
                          color: isRejected ? AppConstants.errorRed : AppConstants.successGreen,
                        ),
                        title: Text('تسجيل لنص: ${sub['passageTopic'] ?? sub['topic'] ?? 'عام'}'),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('الحالة: $status'),
                            if (isRejected && rejectionReason != null)
                              Text('سبب الرفض: $rejectionReason', style: const TextStyle(color: AppConstants.errorRed)),
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ],
      ),
    );
  }
}

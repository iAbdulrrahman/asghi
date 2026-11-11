import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_client.dart';
import '../../core/constants.dart';
import '../../models/models.dart';
import '../../providers/providers.dart';

class ContributorScreen extends ConsumerStatefulWidget {
  const ContributorScreen({super.key});

  @override
  ConsumerState<ContributorScreen> createState() => _ContributorScreenState();
}

class _ContributorScreenState extends ConsumerState<ContributorScreen> {
  List<Passage> _unclaimedPassages = [];
  bool _isLoading = true;
  String? _claimedPassageId;

  @override
  void initState() {
    super.initState();
    _loadUnclaimedPassages();
  }

  void _loadUnclaimedPassages() async {
    setState(() => _isLoading = true);
    final client = ref.read(apiClientProvider);
    try {
      final resp = await client.dio.get('/api/passages/awaiting-recording');
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
        final errData = ApiClient.parseData(e.response?.data);
        final detail = errData?['detail'] ?? 'تعذر حجز النص';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(detail.toString()), backgroundColor: AppConstants.errorRed),
        );
      }
    }
  }

  void _submitAudioMock(Passage p) async {
    final client = ref.read(apiClientProvider);
    try {
      final formData = FormData.fromMap({
        'passageId': p.passageId,
        'attribution': 'SHOW_NAME',
        'durationSeconds': 45.0,
        'file': MultipartFile.fromString(
          'RIFF....WAVEfmt ....data....',
          filename: 'recording_${p.passageId}.wav',
        ),
      });

      await client.dio.post('/api/contributor/submit-audio', data: formData);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('تم رفع التسجيل بنجاح، بانتظار مراجعة المتخصصين'),
            backgroundColor: AppConstants.successGreen,
          ),
        );
        setState(() => _claimedPassageId = null);
        _loadUnclaimedPassages();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('فشل رفع التسجيل: $e'), backgroundColor: AppConstants.errorRed),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('منطقة المساهمين'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadUnclaimedPassages,
          ),
        ],
      ),
      body: Column(
        children: [
          // 72h Claim Banner
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
                                      icon: const Icon(Icons.upload),
                                      label: const Text('رفع التسجيل الصوتي (Fusha)'),
                                      onPressed: () => _submitAudioMock(p),
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
    );
  }
}

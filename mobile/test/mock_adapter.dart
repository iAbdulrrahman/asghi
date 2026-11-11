import 'dart:convert';
import 'dart:typed_data';
import 'package:dio/dio.dart';

class MockHttpAdapter implements HttpClientAdapter {
  Map<String, dynamic> sessionState = {
    'score': 0,
    'difficulty': 'MEDIUM',
  };

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    final path = options.uri.path;
    final method = options.method.toUpperCase();

    // GET /api/users/me
    if (path.contains('/api/users/me')) {
      final data = {
        'userId': 'u-learner-1',
        'displayName': 'أحمد المتعلم',
        'arabicLevel': 'B1',
        'roles': ['LEARNER'],
      };
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // GET awaiting recording
    if (path.contains('awaiting-recording')) {
      final data = [
        {
          'passageId': 'p-awaiting-1',
          'text': 'نص تجريبي ينتظر تسجيل الصوت الفصيح',
          'level': 'B1',
          'topic': 'أدب ولغة',
          'durationSeconds': 60.0,
          'status': 'DRAFT',
          'audioRecordings': [],
          'questionsCount': 2,
        }
      ];
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // GET /api/contributor/submissions
    if (path.contains('/api/contributor/submissions')) {
      final data = [
        {
          'recordingId': 'rec-sub-1',
          'passageTopic': 'أدب ولغة',
          'status': 'VERIFIED',
          'feedback': 'قراءة فصيحة ومتقنة',
        },
        {
          'recordingId': 'rec-sub-2',
          'passageTopic': 'تاريخ',
          'status': 'REJECTED',
          'rejectionReason': 'وجود كلمات عامية غير فصيحة في التسجيل',
        }
      ];
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // POST /api/contributor/submit-audio
    if (path.contains('/api/contributor/submit-audio')) {
      final data = {
        'message': 'تم استلام الملف الصوتي بنجاح',
        'recordingId': 'rec-new-1',
        'status': 'PENDING_REVIEW',
      };
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // GET /api/passages
    if (path == '/api/passages' || path.startsWith('/api/passages?')) {
      final data = [
        {
          'passageId': 'p-test-1',
          'text': 'نص تجريبي متكامل لجلسة الاستماع الفصيح',
          'level': 'B1',
          'topic': 'تاريخ وحضارة',
          'durationSeconds': 45.0,
          'status': 'VERIFIED',
          'audioRecordings': [
            {
              'recordingId': 'rec-1',
              'audioFile': '/audio/test.mp3',
              'durationSeconds': 45.0,
              'status': 'VERIFIED',
              'attribution': 'SHOW_NAME',
            }
          ],
          'questionsCount': 3,
        }
      ];
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // GET /api/learner/progress
    if (path.contains('/api/learner/progress')) {
      final data = {
        'totalScore': 150,
        'completedTests': 5,
        'currentStreak': 3,
        'listeningTimeSeconds': 1800,
        'levelProgression': {'A1': 100, 'A2': 80, 'B1': 40},
      };
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // POST /api/learner/sessions
    if (path == '/api/learner/sessions' && method == 'POST') {
      sessionState['score'] = 0;
      final data = {
        'sessionId': 'session-123',
        'passageId': 'p-test-1',
        'currentDifficulty': 'MEDIUM',
      };
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // GET /api/learner/sessions/{id}/question
    if (path.contains('/question') && method == 'GET') {
      final data = {
        'done': false,
        'questionId': 'q-101',
        'promptText': 'ما هو المحور الرئيسي للنص؟',
        'answers': ['الحضارة', 'التجارة', 'الصناعة', 'الزراعة'],
        'difficulty': sessionState['difficulty'],
        'type': 'MCQ',
        'passageReference': 'السطر الأول',
      };
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // POST /api/learner/sessions/{id}/answer
    if (path.contains('/answer') && method == 'POST') {
      sessionState['score'] = (sessionState['score'] as int) + 20;
      sessionState['difficulty'] = 'HARD';
      final data = {
        'isCorrect': true,
        'correctAnswer': 'الحضارة',
        'explanation': 'شرح مفصل يؤكد صحة الإجابة الحضارية',
        'totalScore': sessionState['score'],
        'nextDifficulty': 'HARD',
      };
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // POST /api/learner/sessions/{id}/finish
    if (path.contains('/finish') && method == 'POST') {
      final data = {'message': 'تم إنهاء الجلسة بنجاح'};
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // POST /api/contributor/claim
    if (path.contains('/api/contributor/claim') && method == 'POST') {
      final data = {'message': 'تم حجز النص بنجاح لتسجيل الصوت', 'passageId': 'p-awaiting-1'};
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // POST /api/reviewer/assignments
    if (path == '/api/reviewer/assignments' && method == 'POST') {
      final data = {
        'assignmentId': 'assign-101',
        'contentId': 'rec-pending-1',
        'isSpecialistReview': false,
      };
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // POST /api/reviewer/questions/{id}/review
    if (path.contains('/api/reviewer/questions/') && path.contains('/review') && method == 'POST') {
      final data = {
        'message': 'تم تحديث حالة السؤال بنجاح',
        'status': 'VERIFIED',
      };
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // GET /api/reviewer/pending-recordings
    if (path.contains('/api/reviewer/pending-recordings')) {
      final data = [
        {
          'recordingId': 'rec-pending-1',
          'passageId': 'p-test-1',
          'topic': 'أدب عربي',
          'audioFile': '/audio/test.mp3',
          'durationSeconds': 90.0,
          'status': 'PENDING_REVIEW',
        }
      ];
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // GET /api/reviewer/pending-questions
    if (path.contains('/api/reviewer/pending-questions')) {
      final data = [
        {
          'questionId': 'q-pending-1',
          'promptText': 'سؤال للمراجعة: ما الفكرة العامة؟',
          'difficulty': 'MEDIUM',
          'status': 'PENDING_REVIEW',
        }
      ];
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // POST /api/admin/generate
    if (path.contains('/api/admin/generate') && method == 'POST') {
      final data = {
        'message': 'تم توليد المحتوى بالذكاء الاصطناعي',
        'passageId': 'p-ai-gen-1',
        'topic': 'أدب ولغة',
        'questionsCount': 3,
      };
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // GET /api/admin/dashboard
    if (path.contains('/api/admin/dashboard')) {
      final data = {
        'totalUsers': 120,
        'totalPassages': 45,
        'verifiedRecordings': 30,
        'pendingFlags': 2,
        'activeClaims': 4,
      };
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // GET /api/admin/report
    if (path.contains('/api/admin/report')) {
      final data = {
        'period': 'MONTHLY',
        'totalUsers': 120,
        'passagesByStatus': {'VERIFIED': 30, 'DRAFT': 10, 'PENDING': 5},
        'reviewTurnaroundHours': 4.2,
      };
      return ResponseBody.fromString(jsonEncode(data), 200, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }

    // Default fallback
    return ResponseBody.fromString(jsonEncode({'status': 'ok'}), 200, headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType],
    });
  }

  @override
  void close({bool force = false}) {}
}

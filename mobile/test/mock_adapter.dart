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

    // GET /api/passages/awaiting-recording
    if (path.contains('/api/passages/awaiting-recording')) {
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

    // Default fallback
    return ResponseBody.fromString(jsonEncode({'status': 'ok'}), 200, headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType],
    });
  }

  @override
  void close({bool force = false}) {}
}

enum UserRole {
  learner,
  contributor,
  reviewer,
  admin;

  static UserRole fromString(String role) {
    switch (role.toUpperCase()) {
      case 'LEARNER':
        return UserRole.learner;
      case 'CONTRIBUTOR':
        return UserRole.contributor;
      case 'REVIEWER':
        return UserRole.reviewer;
      case 'ADMIN':
        return UserRole.admin;
      default:
        return UserRole.learner;
    }
  }

  String get displayNameArabic {
    switch (this) {
      case UserRole.learner:
        return 'متعلّم';
      case UserRole.contributor:
        return 'مساهم';
      case UserRole.reviewer:
        return 'مراجع';
      case UserRole.admin:
        return 'مشرف';
    }
  }
}

class User {
  final String userId;
  final String? email;
  final String? phoneNo;
  final String displayName;
  final String arabicLevel;
  final List<UserRole> roles;

  User({
    required this.userId,
    this.email,
    this.phoneNo,
    required this.displayName,
    required this.arabicLevel,
    required this.roles,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    final rolesList = (json['roles'] as List<dynamic>?)
            ?.map((r) => UserRole.fromString(r.toString()))
            .toList() ??
        [];
    return User(
      userId: json['userId'] ?? '',
      email: json['email'],
      phoneNo: json['phoneNo'],
      displayName: json['displayName'] ?? '',
      arabicLevel: json['arabicLevel'] ?? 'A1',
      roles: rolesList,
    );
  }
}

class AudioRecording {
  final String recordingId;
  final String audioFile;
  final double durationSeconds;
  final String status;
  final String attribution;

  AudioRecording({
    required this.recordingId,
    required this.audioFile,
    required this.durationSeconds,
    required this.status,
    required this.attribution,
  });

  factory AudioRecording.fromJson(Map<String, dynamic> json) {
    return AudioRecording(
      recordingId: json['recordingId'] ?? json['contentId'] ?? '',
      audioFile: json['audioFile'] ?? '',
      durationSeconds: (json['durationSeconds'] ?? 60.0).toDouble(),
      status: json['status'] ?? 'PENDING_REVIEW',
      attribution: json['attribution'] ?? 'SHOW_NAME',
    );
  }
}

class Passage {
  final String passageId;
  final String text;
  final String level;
  final String topic;
  final double durationSeconds;
  final String status;
  final String? claimedBy;
  final String? claimedAt;
  final List<AudioRecording> audioRecordings;
  final int questionsCount;

  Passage({
    required this.passageId,
    required this.text,
    required this.level,
    required this.topic,
    required this.durationSeconds,
    required this.status,
    this.claimedBy,
    this.claimedAt,
    this.audioRecordings = const [],
    this.questionsCount = 0,
  });

  factory Passage.fromJson(Map<String, dynamic> json) {
    final recs = (json['audioRecordings'] as List<dynamic>?)
            ?.map((r) => AudioRecording.fromJson(r as Map<String, dynamic>))
            .toList() ??
        [];
    return Passage(
      passageId: json['passageId'] ?? '',
      text: json['text'] ?? '',
      level: json['level'] ?? 'B1',
      topic: json['topic'] ?? 'عام',
      durationSeconds: (json['durationSeconds'] ?? 60.0).toDouble(),
      status: json['status'] ?? 'DRAFT',
      claimedBy: json['claimedBy'],
      claimedAt: json['claimedAt'],
      audioRecordings: recs,
      questionsCount: json['questionsCount'] ?? 0,
    );
  }

  AudioRecording? get verifiedAudio {
    for (final r in audioRecordings) {
      if (r.status == 'VERIFIED') return r;
    }
    return null;
  }
}

class Question {
  final String questionId;
  final String promptText;
  final List<String> answers;
  final String difficulty;
  final String type;
  final String? passageReference;

  Question({
    required this.questionId,
    required this.promptText,
    required this.answers,
    required this.difficulty,
    required this.type,
    this.passageReference,
  });

  factory Question.fromJson(Map<String, dynamic> json) {
    final ans = (json['answers'] as List<dynamic>?)
            ?.map((a) => a.toString())
            .toList() ??
        [];
    return Question(
      questionId: json['questionId'] ?? '',
      promptText: json['promptText'] ?? '',
      answers: ans,
      difficulty: json['difficulty'] ?? 'MEDIUM',
      type: json['type'] ?? 'MCQ',
      passageReference: json['passageReference'],
    );
  }
}

class LearnerProgress {
  final int totalScore;
  final int totalTimeSpentSeconds;
  final int currentStreakDays;

  LearnerProgress({
    required this.totalScore,
    required this.totalTimeSpentSeconds,
    required this.currentStreakDays,
  });

  factory LearnerProgress.fromJson(Map<String, dynamic> json) {
    return LearnerProgress(
      totalScore: json['totalScore'] ?? 0,
      totalTimeSpentSeconds: json['totalTimeSpent'] ?? json['totalTimeSpentSeconds'] ?? 0,
      currentStreakDays: json['currentStreakDays'] ?? json['streak'] ?? 0,
    );
  }
}

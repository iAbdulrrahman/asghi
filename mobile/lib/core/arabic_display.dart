/// Arabic display mappings for domain enums, statuses, types, and levels.
class ArabicDisplay {
  static String status(String? status) {
    switch (status?.toUpperCase()) {
      case 'DRAFT':
        return 'مسودة';
      case 'PENDING_REVIEW':
        return 'قيد المراجعة';
      case 'VERIFIED':
        return 'معتمد';
      case 'FLAGGED':
        return 'مبلّغ عنه';
      case 'CLAIMED':
        return 'محجوز';
      case 'PENDING':
        return 'معلق';
      case 'NO_ACTION':
        return 'حفظ البلاغ';
      case 'ACTION_TAKEN':
        return 'إجراء متخذ';
      default:
        return status ?? '';
    }
  }

  static String contentType(String? type) {
    switch (type?.toUpperCase()) {
      case 'PASSAGE':
        return 'نص قرائي';
      case 'AUDIO_RECORDING':
      case 'AUDIO':
        return 'تسجيل صوتي';
      case 'QUESTION':
        return 'سؤال استيعاب';
      default:
        return type ?? '';
    }
  }

  static String attribution(String? attr) {
    switch (attr?.toUpperCase()) {
      case 'SHOW_NAME':
        return 'ذكر الاسم';
      case 'ANONYMOUS':
        return 'مجهول (بدون اسم)';
      default:
        return attr ?? '';
    }
  }

  static String difficulty(String? diff) {
    switch (diff?.toUpperCase()) {
      case 'EASY':
        return 'سهل';
      case 'MEDIUM':
        return 'متوسط';
      case 'HARD':
        return 'متقدم';
      default:
        return diff ?? '';
    }
  }

  static String origin(String? orig) {
    switch (orig?.toUpperCase()) {
      case 'AI':
        return 'ذكاء اصطناعي';
      case 'HUMAN':
        return 'بشري';
      default:
        return orig ?? '';
    }
  }

  static String level(String? lvl) {
    switch (lvl?.toUpperCase()) {
      case 'A1':
        return 'مبتدئ (A1)';
      case 'A2':
        return 'أساسي (A2)';
      case 'B1':
        return 'متوسط (B1)';
      case 'B2':
        return 'فوق المتوسط (B2)';
      case 'C1':
        return 'متقدم (C1)';
      case 'C2':
        return 'إتقان (C2)';
      default:
        return lvl ?? '';
    }
  }
}

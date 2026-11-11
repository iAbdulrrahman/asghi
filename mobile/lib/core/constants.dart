import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class AppConstants {
  static const String appNameArabic = 'اصغِ';
  static const String appSubtitle = 'منصة التدريب على الاستماع العربي الفصيح';

  // Configurable via --dart-define=API_BASE=http://...
  static String get apiBaseUrl {
    const defined = String.fromEnvironment('API_BASE', defaultValue: '');
    if (defined.isNotEmpty) return defined;
    if (kIsWeb) return 'http://localhost:8000';
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://localhost:8000';
  }

  // Brand Palette: High contrast, WCAG 2.1 AA compliant
  static const Color primaryEmerald = Color(0xFF004D40);
  static const Color primaryLight = Color(0xFF00796B);
  static const Color accentGold = Color(0xFFD4AF37);
  static const Color backgroundLight = Color(0xFFF9F8F5);
  static const Color surfaceLight = Color(0xFFFFFFFF);
  static const Color textPrimary = Color(0xFF1B1B1B);
  static const Color textSecondary = Color(0xFF555555);
  static const Color errorRed = Color(0xFFB00020);
  static const Color successGreen = Color(0xFF2E7D32);
}

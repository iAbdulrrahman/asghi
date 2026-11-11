import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class AppConstants {
  static const String appNameArabic = 'اصغِ';
  static const String appSubtitle = 'منصة التدريب على الاستماع العربي الفصيح';

  static String? _customBaseUrl;

  static String? get customBaseUrl => _customBaseUrl;
  static set customBaseUrl(String? val) => _customBaseUrl = val;

  // Compile-time default
  static String get defaultApiBaseUrl {
    const defined = String.fromEnvironment('API_BASE', defaultValue: '');
    if (defined.isNotEmpty) return defined;
    if (kIsWeb) return 'http://localhost:8000';
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://localhost:8000';
  }

  // Live configurable value
  static String get apiBaseUrl => _customBaseUrl ?? defaultApiBaseUrl;

  /// Normalizes missing scheme, trims trailing slashes, and validates syntax.
  static String? normalizeAndValidateServerUrl(String input) {
    var raw = input.trim();
    if (raw.isEmpty) return null;
    while (raw.endsWith('/')) {
      raw = raw.substring(0, raw.length - 1);
    }
    if (!raw.startsWith('http://') && !raw.startsWith('https://')) {
      if (raw.contains(':8000') ||
          raw.startsWith('10.0.2.2') ||
          raw.startsWith('127.0.0.1') ||
          raw.startsWith('localhost')) {
        raw = 'http://$raw';
      } else {
        raw = 'https://$raw';
      }
    }
    final uri = Uri.tryParse(raw);
    if (uri == null || !uri.hasScheme || !uri.hasAuthority || uri.host.isEmpty) {
      return null;
    }
    if (uri.scheme != 'http' && uri.scheme != 'https') {
      return null;
    }
    return raw;
  }

  /// Composes audio stream URLs using live apiBaseUrl.
  static String resolveAudioUrl(String? urlOrFile) {
    if (urlOrFile == null || urlOrFile.isEmpty) return '';
    final trimmed = urlOrFile.trim();
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      return trimmed;
    }
    if (trimmed.startsWith('/')) {
      return '$apiBaseUrl$trimmed';
    }
    return '$apiBaseUrl/api/audio/$trimmed';
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

import 'package:flutter/material.dart';

class AppConstants {
  static const String appNameArabic = 'اصغِ';
  static const String appSubtitle = 'منصة التدريب على الاستماع العربي الفصيح';

  static String? customBaseUrl;

  static const String productionApiBaseUrl = 'https://asghi.0xabdul.dev';

  // Compile-time default; local work overrides it with
  // --dart-define=API_BASE=http://10.0.2.2:8000 (emulator) or a LAN address.
  static String get defaultApiBaseUrl {
    const defined = String.fromEnvironment('API_BASE', defaultValue: '');
    if (defined.isNotEmpty) return defined;
    return productionApiBaseUrl;
  }

  // Live configurable value
  static String get apiBaseUrl => customBaseUrl ?? defaultApiBaseUrl;

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

  /// Composes audio stream URLs using live apiBaseUrl, optionally appending auth token.
  static String resolveAudioUrl(String? urlOrFile, {String? token}) {
    if (urlOrFile == null || urlOrFile.isEmpty) return '';
    final trimmed = urlOrFile.trim();
    String fullUrl;
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      fullUrl = trimmed;
    } else if (trimmed.startsWith('/')) {
      fullUrl = '$apiBaseUrl$trimmed';
    } else {
      fullUrl = '$apiBaseUrl/api/audio/$trimmed';
    }
    if (token != null && token.isNotEmpty && !fullUrl.contains('token=')) {
      final sep = fullUrl.contains('?') ? '&' : '?';
      fullUrl = '$fullUrl${sep}token=$token';
    }
    return fullUrl;
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

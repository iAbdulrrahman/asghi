import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/theme.dart';

void main() {
  test('Arabic font file exists and is declared in pubspec.yaml', () {
    final fontFile = File('assets/fonts/NotoNaskhArabic.ttf');
    expect(fontFile.existsSync(), isTrue, reason: 'Font asset file must exist at assets/fonts/NotoNaskhArabic.ttf');

    final licenseFile = File('assets/fonts/OFL.txt');
    expect(licenseFile.existsSync(), isTrue, reason: 'Font license must exist at assets/fonts/OFL.txt');

    final pubspec = File('pubspec.yaml').readAsStringSync();
    expect(pubspec.contains('family: NotoNaskhArabic'), isTrue, reason: 'pubspec.yaml must declare family: NotoNaskhArabic');
    expect(pubspec.contains('assets/fonts/NotoNaskhArabic.ttf'), isTrue, reason: 'pubspec.yaml must include assets/fonts/NotoNaskhArabic.ttf');
  });

  test('AppTheme configures bundled Arabic font family as global default across all text styles', () {
    final theme = AppTheme.lightTheme;
    expect(theme.textTheme.bodyMedium?.fontFamily, 'NotoNaskhArabic');
    expect(theme.textTheme.bodyLarge?.fontFamily, 'NotoNaskhArabic');
    expect(theme.textTheme.titleLarge?.fontFamily, 'NotoNaskhArabic');
    expect(theme.textTheme.titleMedium?.fontFamily, 'NotoNaskhArabic');
    expect(theme.appBarTheme.titleTextStyle?.fontFamily, 'NotoNaskhArabic');
    expect(theme.elevatedButtonTheme.style?.textStyle?.resolve({})?.fontFamily, 'NotoNaskhArabic');
  });
}

import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Verify all user-facing copy is clean Arabic free of raw specification citations (Req/NFR)', () {
    final libDir = Directory('lib');
    final regex = RegExp(r'''['"][^'"]*?\((?:Req|NFR)\s*[\d\.,\s]+\)[^'"]*?['"]''', caseSensitive: false);
    final violations = <String>[];

    for (final entity in libDir.listSync(recursive: true)) {
      if (entity is File && entity.path.endsWith('.dart')) {
        final lines = entity.readAsLinesSync();
        for (int i = 0; i < lines.length; i++) {
          final line = lines[i].trim();
          if (line.startsWith('//') || line.startsWith('/*') || line.startsWith('*')) {
            continue;
          }
          if (regex.hasMatch(line)) {
            violations.add('${entity.path}:${i + 1}: $line');
          }
        }
      }
    }

    expect(
      violations,
      isEmpty,
      reason: 'User-facing copy must not leak raw requirements or NFR citations:\n${violations.join('\n')}',
    );
  });
}

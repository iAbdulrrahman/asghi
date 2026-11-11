import 'package:flutter/material.dart';

class TashkeelTextWidget extends StatelessWidget {
  final String text;
  final bool showTashkeel;
  final TextStyle? style;

  const TashkeelTextWidget({
    super.key,
    required this.text,
    this.showTashkeel = true,
    this.style,
  });

  static String stripTashkeel(String input) {
    // Regex for Arabic diacritics (harakat, shadda, sukun, tanween)
    final tashkeelRegex = RegExp(r'[\u064B-\u065F\u0670]');
    return input.replaceAll(tashkeelRegex, '');
  }

  @override
  Widget build(BuildContext context) {
    final displayText = showTashkeel ? text : stripTashkeel(text);
    return Text(
      displayText,
      style: style ??
          const TextStyle(
            fontSize: 18,
            height: 1.8,
            color: Color(0xFF1B1B1B),
          ),
      textAlign: TextAlign.justify,
      textDirection: TextDirection.rtl,
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:mobile/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Full Learner Session End-to-End Mobile Flow', (WidgetTester tester) async {
    // 1. Launch real Flutter App against configured API_BASE
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 2));

    // 2. If at Login screen, authenticate as seeded learner
    final loginTitle = find.text('تسجيل الدخول');
    if (loginTitle.evaluate().isNotEmpty) {
      final idField = find.byKey(const Key('identifierField'));
      final passField = find.byKey(const Key('passwordField'));

      expect(idField, findsOneWidget);
      expect(passField, findsOneWidget);

      // Enter identifier
      await tester.enterText(idField, 'learner@asghi.org');
      await tester.pumpAndSettle();

      // Enter password
      await tester.enterText(passField, 'LearnerPass123!');
      await tester.pumpAndSettle();

      // Submit login form
      final loginBtn = find.byKey(const Key('loginButton'));
      expect(loginBtn, findsOneWidget);
      await tester.tap(loginBtn);

      // Wait for login response and home screen transition
      for (int i = 0; i < 40; i++) {
        await tester.pump(const Duration(milliseconds: 200));
        if (find.text('مكتبة النصوص التدريبية').evaluate().isNotEmpty) break;
      }
    }

    // 3. Verify Home Screen loads catalogue of verified listening passages
    expect(find.text('مكتبة النصوص التدريبية'), findsOneWidget);

    // Wait for passage cards to load
    for (int i = 0; i < 40; i++) {
      await tester.pump(const Duration(milliseconds: 200));
      if (find.byType(Card).evaluate().isNotEmpty) break;
    }

    // 4. Select the first available passage card to enter practice
    final passageCard = find.byType(Card).first;
    expect(passageCard, findsOneWidget);
    await tester.tap(passageCard);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    // 5. Verify Practice Screen and question presentation
    for (int i = 0; i < 40; i++) {
      await tester.pump(const Duration(milliseconds: 200));
      if (find.byKey(const Key('playPauseButton')).evaluate().isNotEmpty) break;
    }

    // Audio player controls rendered
    expect(find.byKey(const Key('playPauseButton')), findsOneWidget);
    expect(find.text('1.0x'), findsOneWidget);

    // 6. Verify question card and submit an answer
    for (int i = 0; i < 40; i++) {
      await tester.pump(const Duration(milliseconds: 200));
      if (find.byKey(const Key('questionCard')).evaluate().isNotEmpty) break;
    }
    expect(find.byKey(const Key('questionCard')), findsOneWidget);

    // Select the first answer option button
    final answerBtns = find.descendant(
      of: find.byKey(const Key('questionCard')),
      matching: find.byType(ElevatedButton),
    );
    if (answerBtns.evaluate().isNotEmpty) {
      await tester.ensureVisible(answerBtns.first);
      await tester.tap(answerBtns.first);
      await tester.pumpAndSettle(const Duration(seconds: 2));
    }
  });
}

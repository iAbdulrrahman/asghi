import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:mobile/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Full Learner Session End-to-End Mobile Flow', (WidgetTester tester) async {
    // 1. Launch real Flutter App against configured API_BASE
    app.main();
    await tester.pumpAndSettle();

    // 2. If at Login screen, authenticate as seeded learner
    final loginTitle = find.text('تسجيل الدخول');
    if (loginTitle.evaluate().isNotEmpty) {
      final textFields = find.byType(TextField);
      expect(textFields, findsNWidgets(2));

      // Enter identifier
      await tester.enterText(textFields.first, 'learner@asghi.org');
      await tester.pumpAndSettle();

      // Enter password
      await tester.enterText(textFields.last, 'LearnerPass123!');
      await tester.pumpAndSettle();

      // Submit login form
      final submitBtn = find.widgetWithText(ElevatedButton, 'تسجيل الدخول');
      if (submitBtn.evaluate().isNotEmpty) {
        await tester.tap(submitBtn);
      } else {
        await tester.tap(find.text('تسجيل الدخول').last);
      }

      // Wait for login response and home screen transition
      for (int i = 0; i < 30; i++) {
        await tester.pump(const Duration(milliseconds: 100));
        if (find.text('نصوص الاستماع المتاحة').evaluate().isNotEmpty) break;
      }
    }

    // 3. Verify Home Screen loads catalogue of verified listening passages
    expect(find.text('نصوص الاستماع المتاحة'), findsOneWidget);

    // 4. Select the first available passage card to enter practice
    final passageCard = find.byType(Card).first;
    expect(passageCard, findsOneWidget);
    await tester.tap(passageCard);
    await tester.pumpAndSettle();

    // 5. Verify Practice Screen and question presentation
    for (int i = 0; i < 20; i++) {
      await tester.pump(const Duration(milliseconds: 100));
      if (find.byKey(const Key('playPauseButton')).evaluate().isNotEmpty) break;
    }

    // Audio player controls rendered
    expect(find.byKey(const Key('playPauseButton')), findsOneWidget);
    expect(find.text('1.0x'), findsOneWidget);

    // 6. Select answer option
    final radioListTiles = find.byType(RadioListTile<String>);
    if (radioListTiles.evaluate().isNotEmpty) {
      await tester.tap(radioListTiles.first);
      await tester.pumpAndSettle();

      // Submit answer
      final confirmBtn = find.text('تأكيد الإجابة');
      if (confirmBtn.evaluate().isNotEmpty) {
        await tester.tap(confirmBtn);
        for (int i = 0; i < 20; i++) {
          await tester.pump(const Duration(milliseconds: 100));
        }
      }
    }
  });
}

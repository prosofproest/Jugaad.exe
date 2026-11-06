import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ps03_mobile/main.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('home screen names both outputs and never merges them', (
    tester,
  ) async {
    await tester.pumpWidget(const Ps03App());

    expect(find.text('PS-03'), findsWidgets);
    expect(find.text('Photo assessment'), findsOneWidget);
    expect(find.text('Area outlook'), findsOneWidget);
  });

  testWidgets('chat exposes photo capture and honest demo copy', (
    tester,
  ) async {
    await tester.pumpWidget(const MaterialApp(home: ChatPage()));
    await tester.pumpAndSettle();

    expect(find.byTooltip('Attach a photo'), findsOneWidget);
    expect(find.text('Send'), findsOneWidget);
    expect(find.textContaining('not a diagnosis'), findsWidgets);
    expect(find.textContaining('Attach a photo or describe'), findsOneWidget);

    // Dispose the page so its periodic flush timer is cancelled.
    await tester.pumpWidget(const SizedBox());
    await tester.pump();
  });
}

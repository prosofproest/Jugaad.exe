import 'package:flutter_test/flutter_test.dart';
import 'package:ps03_mobile/main.dart';

void main() {
  testWidgets('home screen names both outputs and never merges them', (tester) async {
    await tester.pumpWidget(const Ps03App());

    expect(find.text('PS-03'), findsWidgets);
    expect(find.text('Photo assessment'), findsOneWidget);
    expect(find.text('Area outlook'), findsOneWidget);
  });
}

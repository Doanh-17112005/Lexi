import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lexilingo_app/core/di/service_locator.dart';
import 'package:lexilingo_app/core/widgets/premium_gate.dart';

void main() {
  testWidgets('fails closed when backend entitlement service is unavailable', (
    tester,
  ) async {
    await sl.reset();

    await tester.pumpWidget(
      const MaterialApp(
        home: PremiumGate(
          lockedChild: Text('locked'),
          child: Text('premium content'),
        ),
      ),
    );
    await tester.pump();

    expect(find.text('locked'), findsOneWidget);
    expect(find.text('premium content'), findsNothing);
  });
}

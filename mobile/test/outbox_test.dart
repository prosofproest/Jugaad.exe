import 'package:flutter_test/flutter_test.dart';
import 'package:ps03_mobile/src/outbox.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('queued turn round-trips through shared preferences', () async {
    final outbox = Outbox(SharedPreferencesOutboxStorage());
    final turn = QueuedTurn(
      clientMessageId: 'cm_1',
      text: 'brown spots on the lower leaves',
      imagePath: '/cache/photo.jpg',
      imageFilename: 'photo.jpg',
      imageContentType: 'image/jpeg',
      conversationId: 'conv_1',
      queuedAt: DateTime.utc(2026, 11, 6, 10, 30),
    );

    await outbox.add(turn);
    final loaded = await outbox.load();

    expect(loaded, hasLength(1));
    final restored = loaded.single;
    expect(restored.clientMessageId, 'cm_1');
    expect(restored.text, 'brown spots on the lower leaves');
    expect(restored.imagePath, '/cache/photo.jpg');
    expect(restored.imageFilename, 'photo.jpg');
    expect(restored.imageContentType, 'image/jpeg');
    expect(restored.conversationId, 'conv_1');
    expect(restored.queuedAt, DateTime.utc(2026, 11, 6, 10, 30));
    expect(restored.state, 'queued');
    expect(restored.retryable, isTrue);
  });

  test('adding the same client_message_id replaces instead of duplicating',
      () async {
    final outbox = Outbox(SharedPreferencesOutboxStorage());
    final turn = QueuedTurn(
      clientMessageId: 'cm_1',
      text: 'first',
      queuedAt: DateTime.utc(2026, 11, 6),
    );

    await outbox.add(turn);
    await outbox.add(turn.copyWith(text: 'second'));

    final loaded = await outbox.load();
    expect(loaded, hasLength(1));
    expect(loaded.single.text, 'second');
  });

  test('update and remove persist the queued state', () async {
    final outbox = Outbox(SharedPreferencesOutboxStorage());
    final turn = QueuedTurn(
      clientMessageId: 'cm_1',
      text: 'hello',
      queuedAt: DateTime.utc(2026, 11, 6),
    );

    await outbox.add(turn);
    await outbox.update(
      turn.copyWith(
        state: 'failed',
        retryable: false,
        lastError: 'upload rejected',
      ),
    );

    var loaded = await outbox.load();
    expect(loaded.single.state, 'failed');
    expect(loaded.single.retryable, isFalse);
    expect(loaded.single.lastError, 'upload rejected');

    await outbox.remove('cm_1');
    loaded = await outbox.load();
    expect(loaded, isEmpty);
  });

  test('a corrupt queue is treated as empty rather than crashing', () async {
    SharedPreferences.setMockInitialValues({outboxStorageKey: 'not-json'});

    final outbox = Outbox(SharedPreferencesOutboxStorage());
    expect(await outbox.load(), isEmpty);
  });
}

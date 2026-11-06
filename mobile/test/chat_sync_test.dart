import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:ps03_mobile/src/api_client.dart';
import 'package:ps03_mobile/src/chat_sync.dart';
import 'package:ps03_mobile/src/outbox.dart';

void main() {
  test('flush uploads an image once and sends the same client id', () async {
    final storage = _MemoryStorage();
    final outbox = Outbox(storage);
    final api = _FakeChatApi();
    final sync = ChatSync(
      api: api,
      outbox: outbox,
      readImageBytes: (_) async => Uint8List.fromList([1, 2, 3]),
    );

    await outbox.add(_turn('cm_1', imagePath: '/cache/photo.jpg'));

    final report = await sync.flush();

    expect(api.createCalls, 1);
    expect(api.uploadCalls, 1);
    expect(api.sentIds, ['cm_1']);
    expect(api.sentImages.single?.uploadId, 'up_1');
    expect(report.sent, hasLength(1));
    expect(await outbox.load(), isEmpty);
  });

  test('a retry reuses the upload id instead of uploading again', () async {
    final outbox = Outbox(_MemoryStorage());
    final api = _FakeChatApi()
      ..sendError = ApiException(503, 'unavailable', 'try later', null);
    final sync = ChatSync(
      api: api,
      outbox: outbox,
      readImageBytes: (_) async => Uint8List.fromList([1, 2, 3]),
    );

    await outbox.add(_turn('cm_1', imagePath: '/cache/photo.jpg'));

    final first = await sync.flush();
    expect(api.uploadCalls, 1);
    expect(first.hasQueued, isTrue);
    expect((await outbox.load()).single.uploadId, 'up_1');

    api.sendError = null;
    final second = await sync.flush();

    expect(api.uploadCalls, 1);
    expect(api.sentIds, ['cm_1', 'cm_1']);
    expect(second.sent, hasLength(1));
    expect(await outbox.load(), isEmpty);
  });

  test('a missing local image becomes a failed turn and is not sent', () async {
    final outbox = Outbox(_MemoryStorage());
    final api = _FakeChatApi();
    final sync = ChatSync(
      api: api,
      outbox: outbox,
      readImageBytes: (_) async =>
          throw const ImageUnavailable('/cache/evicted.jpg'),
    );

    await outbox.add(_turn('cm_1', imagePath: '/cache/evicted.jpg'));

    final report = await sync.flush();

    expect(api.uploadCalls, 0);
    expect(api.sentIds, isEmpty);
    expect(report.remaining.single.state, 'failed');
    expect(report.remaining.single.retryable, isFalse);
    expect(report.hasQueued, isFalse);
  });

  test('one conversation is created for several queued turns', () async {
    final outbox = Outbox(_MemoryStorage());
    final api = _FakeChatApi();
    final sync = ChatSync(
      api: api,
      outbox: outbox,
      readImageBytes: (_) async => Uint8List.fromList([1]),
    );

    await outbox.add(_turn('cm_1'));
    await outbox.add(_turn('cm_2'));

    final report = await sync.flush();

    expect(api.createCalls, 1);
    expect(api.sentIds, ['cm_1', 'cm_2']);
    expect(report.sent, hasLength(2));
  });

  test('a text-only turn never uploads an image', () async {
    final outbox = Outbox(_MemoryStorage());
    final api = _FakeChatApi();
    final sync = ChatSync(
      api: api,
      outbox: outbox,
      readImageBytes: (_) async => Uint8List.fromList([1]),
    );

    await outbox.add(_turn('cm_1', text: 'yellowing between the veins'));

    final report = await sync.flush();

    expect(api.uploadCalls, 0);
    expect(api.sentImages.single, isNull);
    expect(report.sent.single.result.userMessage.text, 'yellowing between the veins');
  });
}

QueuedTurn _turn(String clientMessageId, {String? imagePath, String? text}) {
  return QueuedTurn(
    clientMessageId: clientMessageId,
    text: text ?? 'brown spots',
    imagePath: imagePath,
    imageFilename: imagePath == null ? null : 'photo.jpg',
    imageContentType: imagePath == null ? null : 'image/jpeg',
    queuedAt: DateTime.utc(2026, 11, 6),
  );
}

class _MemoryStorage implements OutboxStorage {
  String? value;

  @override
  Future<String?> read() async => value;

  @override
  Future<void> write(String value) async {
    this.value = value;
  }
}

class _FakeChatApi implements ChatApi {
  int createCalls = 0;
  int uploadCalls = 0;
  final List<String> sentIds = <String>[];
  final List<String?> sentTexts = <String?>[];
  final List<ImageReference?> sentImages = <ImageReference?>[];
  ApiException? sendError;

  @override
  Future<String> createConversation() async {
    createCalls++;
    return 'conv_1';
  }

  @override
  Future<UploadDescriptor> uploadImage({
    required Uint8List bytes,
    required String filename,
    required String contentType,
  }) async {
    uploadCalls++;
    return const UploadDescriptor(
      uploadId: 'up_1',
      filename: 'photo.jpg',
      contentType: 'image/jpeg',
      contentHash: 'sha256:abc',
      width: 100,
      height: 100,
      qualityResult: 'pass',
      previewUrl: '/v1/uploads/up_1',
      sizeBytes: 3,
      qualityGateVersion: 'demo-quality-0.1',
    );
  }

  @override
  Future<SendResult> sendMessage({
    required String conversationId,
    required String clientMessageId,
    String? text,
    ImageReference? image,
  }) async {
    sentIds.add(clientMessageId);
    sentTexts.add(text);
    sentImages.add(image);
    if (sendError != null) {
      throw sendError!;
    }

    return SendResult(
      userMessage: Message(
        messageId: 'msg_$clientMessageId',
        conversationId: conversationId,
        role: 'user',
        kind: image == null ? 'text' : 'image',
        text: text,
        clientMessageId: clientMessageId,
      ),
      assistantMessage: Message(
        messageId: 'msg_reply_$clientMessageId',
        conversationId: conversationId,
        role: 'assistant',
        kind: 'assessment',
        text: 'Assistive photo assessment, not a diagnosis.',
      ),
    );
  }
}

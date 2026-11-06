/// Upload/send and outbox-flush orchestration for the chat.
///
/// The image is always uploaded first; the JSON message only carries the
/// resulting `upload_id`. A queued turn keeps its `client_message_id`, so a
/// retry is idempotent on the server (CHAT-03 / CHAT-04).
library;

import 'dart:io';
import 'dart:typed_data';

import 'api_client.dart';
import 'outbox.dart';

class ImageUnavailable implements Exception {
  const ImageUnavailable(this.path);

  final String path;

  @override
  String toString() => 'The photo at $path is no longer available.';
}

typedef ImageBytesReader = Future<Uint8List> Function(String path);

Future<Uint8List> readFileBytes(String path) async {
  final file = File(path);
  if (!await file.exists()) {
    throw ImageUnavailable(path);
  }
  return file.readAsBytes();
}

class SentTurn {
  const SentTurn({required this.turn, required this.result});

  final QueuedTurn turn;
  final SendResult result;
}

class OutboxFlushResult {
  const OutboxFlushResult({
    required this.sent,
    required this.remaining,
    required this.errors,
  });

  final List<SentTurn> sent;
  final List<QueuedTurn> remaining;
  final List<String> errors;

  bool get hasQueued => remaining.any(
    (turn) => turn.state == 'queued' && turn.retryable,
  );
}

class ChatSync {
  ChatSync({
    required ChatApi api,
    required Outbox outbox,
    ImageBytesReader? readImageBytes,
  }) : _api = api,
       _outbox = outbox,
       _readImageBytes = readImageBytes ?? readFileBytes;

  final ChatApi _api;
  final Outbox _outbox;
  final ImageBytesReader _readImageBytes;

  /// Upload (if needed) and send one turn. `onTurnUpdated` is called whenever
  /// the turn gains a conversation id or an upload id, so the caller can persist
  /// that progress before the next retry.
  Future<SendResult> deliver(
    QueuedTurn turn, {
    String? conversationId,
    void Function(QueuedTurn turn)? onTurnUpdated,
  }) async {
    var current = turn;

    var activeConversationId = current.conversationId ?? conversationId;
    activeConversationId ??= await _api.createConversation();
    if (current.conversationId != activeConversationId) {
      current = current.copyWith(conversationId: activeConversationId);
      onTurnUpdated?.call(current);
    }

    if (current.hasImage && current.uploadId == null) {
      final bytes = await _readImageBytes(current.imagePath!);
      final descriptor = await _api.uploadImage(
        bytes: bytes,
        filename: current.imageFilename ?? 'photo.jpg',
        contentType: current.imageContentType ?? 'image/jpeg',
      );
      current = current.copyWith(
        uploadId: descriptor.uploadId,
        uploadContentHash: descriptor.contentHash,
        imageFilename: descriptor.filename,
        imageContentType: descriptor.contentType,
      );
      onTurnUpdated?.call(current);
    }

    return _api.sendMessage(
      conversationId: activeConversationId,
      clientMessageId: current.clientMessageId,
      text: current.text,
      image: current.uploadId == null
          ? null
          : ImageReference(
              uploadId: current.uploadId!,
              filename: current.imageFilename,
              contentType: current.imageContentType,
              contentHash: current.uploadContentHash,
            ),
    );
  }

  /// Deliver every retryable turn in order. Failed turns stay in the outbox so
  /// the user can see and delete them; they are never presented as a reply.
  Future<OutboxFlushResult> flush({
    String? conversationId,
    void Function(SentTurn sent)? onSent,
    void Function(QueuedTurn turn)? onTurnUpdated,
  }) async {
    final turns = await _outbox.load();
    final sent = <SentTurn>[];
    final errors = <String>[];
    var activeConversationId = conversationId;

    for (var index = 0; index < turns.length; index++) {
      final original = turns[index];
      if (original.isFailed) {
        continue;
      }

      var current = original;
      try {
        final result = await deliver(
          original,
          conversationId: activeConversationId,
          onTurnUpdated: (updated) {
            current = updated;
            turns[index] = updated;
            onTurnUpdated?.call(updated);
          },
        );
        activeConversationId = current.conversationId ?? activeConversationId;
        turns.removeAt(index);
        index--;
        final delivered = SentTurn(turn: current, result: result);
        sent.add(delivered);
        onSent?.call(delivered);
      } on ImageUnavailable catch (error) {
        activeConversationId = current.conversationId ?? activeConversationId;
        current = current.copyWith(
          state: 'failed',
          retryable: false,
          lastError: error.toString(),
        );
        turns[index] = current;
        onTurnUpdated?.call(current);
        errors.add(error.toString());
      } on ApiException catch (error) {
        activeConversationId = current.conversationId ?? activeConversationId;
        current = current.copyWith(
          state: error.retryable ? 'queued' : 'failed',
          retryable: error.retryable,
          lastError: error.toString(),
        );
        turns[index] = current;
        onTurnUpdated?.call(current);
        errors.add(error.toString());
        if (error.retryable) {
          // A server/network failure usually affects the whole connection.
          // Stop and let the next flush or the user retry.
          break;
        }
      } catch (error) {
        activeConversationId = current.conversationId ?? activeConversationId;
        current = current.copyWith(
          state: 'queued',
          retryable: true,
          lastError: 'Network unavailable. Will retry when connected.',
        );
        turns[index] = current;
        onTurnUpdated?.call(current);
        errors.add('$error');
        break;
      }

      await _outbox.save(turns);
    }

    await _outbox.save(turns);
    return OutboxFlushResult(
      sent: List<SentTurn>.unmodifiable(sent),
      remaining: List<QueuedTurn>.unmodifiable(turns),
      errors: List<String>.unmodifiable(errors),
    );
  }
}

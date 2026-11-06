/// Durable, client-side outbox for chat turns.
///
/// The outbox is the offline contract from spec 08 §10 / CHAT-04: a turn is
/// saved locally, shown as `queued`, and resent on reconnect with the same
/// `client_message_id`. The image is *not* stored in JSON; only the local file
/// path is, because the bytes are uploaded separately before the message.
library;

import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

const String outboxStorageKey = 'ps03.chat.outbox.v1';

/// One user turn waiting to be delivered to `/v1`.
class QueuedTurn {
  const QueuedTurn({
    required this.clientMessageId,
    this.text,
    this.imagePath,
    this.imageFilename,
    this.imageContentType,
    this.uploadId,
    this.uploadContentHash,
    this.conversationId,
    required this.queuedAt,
    this.state = 'queued',
    this.retryable = true,
    this.lastError,
  });

  factory QueuedTurn.fromJson(Map<String, dynamic> json) => QueuedTurn(
    clientMessageId: json['client_message_id'] as String? ?? '',
    text: json['text'] as String?,
    imagePath: json['image_path'] as String?,
    imageFilename: json['image_filename'] as String?,
    imageContentType: json['image_content_type'] as String?,
    uploadId: json['upload_id'] as String?,
    uploadContentHash: json['upload_content_hash'] as String?,
    conversationId: json['conversation_id'] as String?,
    queuedAt:
        DateTime.tryParse(json['queued_at'] as String? ?? '') ??
        DateTime.now().toUtc(),
    state: json['state'] as String? ?? 'queued',
    retryable: json['retryable'] as bool? ?? true,
    lastError: json['last_error'] as String?,
  );

  final String clientMessageId;
  final String? text;
  final String? imagePath;
  final String? imageFilename;
  final String? imageContentType;

  /// Set after the image bytes have been uploaded once. Persisting it prevents
  /// a retry from creating a second upload for the same turn.
  final String? uploadId;
  final String? uploadContentHash;

  final String? conversationId;
  final DateTime queuedAt;

  /// `queued` or `failed`. A failed turn is kept so the user can delete it.
  final String state;
  final bool retryable;
  final String? lastError;

  bool get hasImage => imagePath != null && imagePath!.isNotEmpty;
  bool get isFailed => state == 'failed' || !retryable;

  Map<String, dynamic> toJson() => {
    'client_message_id': clientMessageId,
    'text': text,
    'image_path': imagePath,
    'image_filename': imageFilename,
    'image_content_type': imageContentType,
    'upload_id': uploadId,
    'upload_content_hash': uploadContentHash,
    'conversation_id': conversationId,
    'queued_at': queuedAt.toUtc().toIso8601String(),
    'state': state,
    'retryable': retryable,
    'last_error': lastError,
  };

  QueuedTurn copyWith({
    String? text,
    String? imagePath,
    String? imageFilename,
    String? imageContentType,
    String? uploadId,
    String? uploadContentHash,
    String? conversationId,
    DateTime? queuedAt,
    String? state,
    bool? retryable,
    Object? lastError = _unset,
  }) => QueuedTurn(
    clientMessageId: clientMessageId,
    text: text ?? this.text,
    imagePath: imagePath ?? this.imagePath,
    imageFilename: imageFilename ?? this.imageFilename,
    imageContentType: imageContentType ?? this.imageContentType,
    uploadId: uploadId ?? this.uploadId,
    uploadContentHash: uploadContentHash ?? this.uploadContentHash,
    conversationId: conversationId ?? this.conversationId,
    queuedAt: queuedAt ?? this.queuedAt,
    state: state ?? this.state,
    retryable: retryable ?? this.retryable,
    lastError: identical(lastError, _unset)
        ? this.lastError
        : lastError as String?,
  );
}

const Object _unset = Object();

/// Storage seam so the queue can be tested without platform channels.
abstract interface class OutboxStorage {
  Future<String?> read();
  Future<void> write(String value);
}

class SharedPreferencesOutboxStorage implements OutboxStorage {
  SharedPreferencesOutboxStorage({this.key = outboxStorageKey});

  final String key;

  @override
  Future<String?> read() async {
    final preferences = await SharedPreferences.getInstance();
    return preferences.getString(key);
  }

  @override
  Future<void> write(String value) async {
    final preferences = await SharedPreferences.getInstance();
    await preferences.setString(key, value);
  }
}

class Outbox {
  Outbox(this._storage);

  final OutboxStorage _storage;

  Future<List<QueuedTurn>> load() async {
    final raw = await _storage.read();
    if (raw == null || raw.trim().isEmpty) {
      return <QueuedTurn>[];
    }

    try {
      final decoded = jsonDecode(raw);
      if (decoded is! List<dynamic>) {
        return <QueuedTurn>[];
      }
      return decoded
          .whereType<Map<String, dynamic>>()
          .map(QueuedTurn.fromJson)
          .where((turn) => turn.clientMessageId.isNotEmpty)
          .toList();
    } on FormatException {
      // A corrupt queue is treated as empty rather than crashing the chat.
      return <QueuedTurn>[];
    }
  }

  Future<void> save(List<QueuedTurn> turns) => _storage.write(
    jsonEncode(turns.map((turn) => turn.toJson()).toList(growable: false)),
  );

  Future<List<QueuedTurn>> add(QueuedTurn turn) async {
    final turns = await load();
    turns.removeWhere((item) => item.clientMessageId == turn.clientMessageId);
    turns.add(turn);
    await save(turns);
    return turns;
  }

  Future<List<QueuedTurn>> update(QueuedTurn turn) async {
    final turns = await load();
    final index = turns.indexWhere(
      (item) => item.clientMessageId == turn.clientMessageId,
    );
    if (index < 0) {
      turns.add(turn);
    } else {
      turns[index] = turn;
    }
    await save(turns);
    return turns;
  }

  Future<List<QueuedTurn>> remove(String clientMessageId) async {
    final turns = await load();
    turns.removeWhere((item) => item.clientMessageId == clientMessageId);
    await save(turns);
    return turns;
  }
}

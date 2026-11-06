/// Typed client for the PS-03 `/v1` API.
///
/// The mobile app is an API-only client: it never talks to the database.
/// Errors follow the problem-details envelope in `final/TRD.md` §7.2.
library;

import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

/// Base URL of the API.
///
/// Override at build time:
/// `flutter run --dart-define=API_BASE_URL=https://staging.example/api`
///
/// The default points at the host machine from an Android emulator.
const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

class ApiException implements Exception {
  ApiException(
    this.status,
    this.code,
    this.detail,
    this.requestId, {
    bool? retryable,
  }) : retryable =
           retryable ?? (status >= 500 || status == 408 || status == 429);

  final int status;
  final String code;
  final String? detail;
  final String? requestId;
  final bool retryable;

  @override
  String toString() => '$status $code${detail == null ? '' : ' — $detail'}';
}

class Health {
  Health.fromJson(Map<String, dynamic> json)
    : status = json['status'] as String? ?? 'unknown',
      service = json['service'] as String? ?? 'unknown',
      version = json['version'] as String? ?? 'unknown',
      environment = json['environment'] as String? ?? 'unknown';

  final String status;
  final String service;
  final String version;
  final String environment;
}

class Candidate {
  const Candidate({
    required this.label,
    this.displayName,
    required this.score,
  });

  factory Candidate.fromJson(Map<String, dynamic> json) => Candidate(
    label: json['label'] as String? ?? 'unknown',
    displayName: json['display_name'] as String?,
    score: (json['score'] as num?)?.toDouble() ?? 0,
  );

  final String label;
  final String? displayName;
  final double score;
}

class Assessment {
  const Assessment({
    required this.state,
    this.reasonCode,
    this.reasonText,
    this.qualityFlag,
    this.qualityFlags = const [],
    this.candidates = const [],
    this.confidenceBand,
    this.calibrated = false,
    required this.modelVersion,
    this.generatedAt,
    this.isDemo = true,
    this.observationId,
    this.errorCode,
    this.retryable = false,
  });

  factory Assessment.fromJson(Map<String, dynamic> json) => Assessment(
    state: json['state'] as String? ?? 'failed',
    reasonCode: json['reason_code'] as String?,
    reasonText: json['reason_text'] as String?,
    qualityFlag: json['quality_flag'] as String?,
    qualityFlags: (json['quality_flags'] as List<dynamic>? ?? const [])
        .whereType<String>()
        .toList(growable: false),
    candidates: (json['candidates'] as List<dynamic>? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(Candidate.fromJson)
        .toList(growable: false),
    confidenceBand: json['confidence_band'] as String?,
    calibrated: json['calibrated'] as bool? ?? false,
    modelVersion: json['model_version'] as String? ?? 'unknown',
    generatedAt: DateTime.tryParse(json['generated_at'] as String? ?? ''),
    isDemo: json['is_demo'] as bool? ?? true,
    observationId: json['observation_id'] as String?,
    errorCode: json['error_code'] as String?,
    retryable: json['retryable'] as bool? ?? false,
  );

  final String state;
  final String? reasonCode;
  final String? reasonText;
  final String? qualityFlag;
  final List<String> qualityFlags;
  final List<Candidate> candidates;
  final String? confidenceBand;
  final bool calibrated;
  final String modelVersion;
  final DateTime? generatedAt;
  final bool isDemo;
  final String? observationId;
  final String? errorCode;
  final bool retryable;
}

class UploadedImage {
  const UploadedImage({
    required this.uploadId,
    required this.filename,
    required this.contentType,
    required this.contentHash,
    required this.width,
    required this.height,
    required this.qualityResult,
    this.qualityFlags = const [],
    required this.previewUrl,
  });

  factory UploadedImage.fromJson(Map<String, dynamic> json) => UploadedImage(
    uploadId: json['upload_id'] as String? ?? '',
    filename: json['filename'] as String? ?? 'upload',
    contentType: json['content_type'] as String? ?? 'application/octet-stream',
    contentHash: json['content_hash'] as String? ?? '',
    width: (json['width'] as num?)?.toInt() ?? 0,
    height: (json['height'] as num?)?.toInt() ?? 0,
    qualityResult: json['quality_result'] as String? ?? 'unknown',
    qualityFlags: (json['quality_flags'] as List<dynamic>? ?? const [])
        .whereType<String>()
        .toList(growable: false),
    previewUrl: json['preview_url'] as String? ?? '',
  );

  final String uploadId;
  final String filename;
  final String contentType;
  final String contentHash;
  final int width;
  final int height;
  final String qualityResult;
  final List<String> qualityFlags;
  final String previewUrl;
}

class UploadDescriptor extends UploadedImage {
  const UploadDescriptor({
    required super.uploadId,
    required super.filename,
    required super.contentType,
    required super.contentHash,
    required super.width,
    required super.height,
    required super.qualityResult,
    super.qualityFlags,
    required super.previewUrl,
    required this.sizeBytes,
    required this.qualityGateVersion,
    this.createdAt,
    this.isDemo = true,
  });

  factory UploadDescriptor.fromJson(Map<String, dynamic> json) =>
      UploadDescriptor(
        uploadId: json['upload_id'] as String? ?? '',
        filename: json['filename'] as String? ?? 'upload',
        contentType:
            json['content_type'] as String? ?? 'application/octet-stream',
        contentHash: json['content_hash'] as String? ?? '',
        width: (json['width'] as num?)?.toInt() ?? 0,
        height: (json['height'] as num?)?.toInt() ?? 0,
        qualityResult: json['quality_result'] as String? ?? 'unknown',
        qualityFlags: (json['quality_flags'] as List<dynamic>? ?? const [])
            .whereType<String>()
            .toList(growable: false),
        previewUrl: json['preview_url'] as String? ?? '',
        sizeBytes: (json['size_bytes'] as num?)?.toInt() ?? 0,
        qualityGateVersion: json['quality_gate_version'] as String? ?? 'unknown',
        createdAt: DateTime.tryParse(json['created_at'] as String? ?? ''),
        isDemo: json['is_demo'] as bool? ?? true,
      );

  final int sizeBytes;
  final String qualityGateVersion;
  final DateTime? createdAt;
  final bool isDemo;
}

/// A reference to an image already uploaded through `POST /v1/uploads`.
/// Raw bytes never travel in the JSON message body.
class ImageReference {
  const ImageReference({
    required this.uploadId,
    this.filename,
    this.contentType,
    this.contentHash,
  });

  final String uploadId;
  final String? filename;
  final String? contentType;
  final String? contentHash;

  Map<String, dynamic> toJson() => {
    'upload_id': uploadId,
    'filename': filename,
    'content_type': contentType,
    'content_hash': contentHash,
  };
}

class Message {
  const Message({
    required this.messageId,
    required this.conversationId,
    required this.role,
    required this.kind,
    this.text,
    this.clientMessageId,
    this.observationId,
    this.image,
    this.assessment,
    this.nextSteps = const [],
    this.createdAt,
    this.isDemo = false,
  });

  factory Message.fromJson(Map<String, dynamic> json) => Message(
    messageId: json['message_id'] as String? ?? '',
    conversationId: json['conversation_id'] as String? ?? '',
    role: json['role'] as String? ?? 'assistant',
    kind: json['kind'] as String? ?? 'text',
    text: json['text'] as String?,
    clientMessageId: json['client_message_id'] as String?,
    observationId: json['observation_id'] as String?,
    image: json['image'] is Map<String, dynamic>
        ? UploadedImage.fromJson(json['image'] as Map<String, dynamic>)
        : null,
    assessment: json['assessment'] is Map<String, dynamic>
        ? Assessment.fromJson(json['assessment'] as Map<String, dynamic>)
        : null,
    nextSteps: (json['next_steps'] as List<dynamic>? ?? const [])
        .whereType<String>()
        .toList(growable: false),
    createdAt: DateTime.tryParse(json['created_at'] as String? ?? ''),
    isDemo: json['is_demo'] as bool? ?? false,
  );

  final String messageId;
  final String conversationId;
  final String role;
  final String kind;
  final String? text;
  final String? clientMessageId;
  final String? observationId;
  final UploadedImage? image;
  final Assessment? assessment;
  final List<String> nextSteps;
  final DateTime? createdAt;
  final bool isDemo;
}

class SendResult {
  const SendResult({
    required this.userMessage,
    required this.assistantMessage,
  });

  factory SendResult.fromJson(Map<String, dynamic> json) => SendResult(
    userMessage: Message.fromJson(
      json['user_message'] as Map<String, dynamic>? ?? const {},
    ),
    assistantMessage: Message.fromJson(
      json['assistant_message'] as Map<String, dynamic>? ?? const {},
    ),
  );

  final Message userMessage;
  final Message assistantMessage;
}

class ApiClient {
  ApiClient({http.Client? client, String? baseUrl})
    : _client = client ?? http.Client(),
      _baseUrl = baseUrl ?? apiBaseUrl;

  final http.Client _client;
  final String _baseUrl;

  Future<Health> health() async {
    final json = await _get('/health');
    return Health.fromJson(json);
  }

  Future<String> createConversation() async {
    final json = await _post('/v1/conversations', {'title': 'Photo assessment'});
    return json['conversation_id'] as String;
  }

  Future<SendResult> sendMessage({
    required String conversationId,
    required String clientMessageId,
    String? text,
    ImageReference? image,
  }) async {
    final json = await _post(
      '/v1/conversations/$conversationId/messages',
      {
        'client_message_id': clientMessageId,
        'text': text,
        'image': image?.toJson(),
      },
      headers: {'Idempotency-Key': clientMessageId},
    );
    return SendResult.fromJson(json);
  }

  /// Upload raw image bytes. The backend validates the declared type, the real
  /// decode, the size ceiling and the demo quality gate before storing anything.
  /// The returned `upload_id` is what the chat message references.
  Future<UploadDescriptor> uploadImage({
    required Uint8List bytes,
    required String filename,
    required String contentType,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/v1/uploads'),
    )
      ..headers['Accept'] = 'application/json'
      ..headers['X-Request-ID'] = clientMessageIdForRequest()
      ..files.add(
        http.MultipartFile.fromBytes(
          'file',
          bytes,
          filename: filename,
          contentType: MediaType.parse(contentType),
        ),
      );

    final streamed = await _client.send(request);
    final response = await http.Response.fromStream(streamed);
    return UploadDescriptor.fromJson(_decode(response));
  }

  /// Turn a relative API path such as `/v1/uploads/up_x` into an absolute URL.
  String assetUrl(String path) {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    final base = _baseUrl.replaceFirst(RegExp(r'/$'), '');
    return path.startsWith('/') ? '$base$path' : '$base/$path';
  }

  Future<Map<String, dynamic>> _get(String path) async {
    final response = await _client.get(
      Uri.parse('$_baseUrl$path'),
      headers: {'Accept': 'application/json'},
    );
    return _decode(response);
  }

  Future<Map<String, dynamic>> _post(
    String path,
    Map<String, dynamic> body, {
    Map<String, String> headers = const {},
  }) async {
    final response = await _client.post(
      Uri.parse('$_baseUrl$path'),
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Request-ID': clientMessageIdForRequest(),
        ...headers,
      },
      body: jsonEncode(body),
    );
    return _decode(response);
  }

  Map<String, dynamic> _decode(http.Response response) {
    Map<String, dynamic>? decoded;
    if (response.body.isNotEmpty) {
      try {
        final value = jsonDecode(response.body);
        if (value is Map<String, dynamic>) {
          decoded = value;
        }
      } on FormatException {
        decoded = null;
      }
    }

    if (response.statusCode >= 400) {
      throw ApiException(
        response.statusCode,
        decoded?['code'] as String? ?? 'api_error',
        decoded?['detail'] as String? ?? decoded?['title'] as String?,
        decoded?['request_id'] as String?,
        retryable: decoded?['retryable'] as bool?,
      );
    }

    if (decoded == null) {
      throw ApiException(
        response.statusCode,
        'invalid_response',
        'The server returned an unreadable response.',
        null,
        retryable: true,
      );
    }

    return decoded;
  }

  void close() => _client.close();
}

/// A cheap, collision-resistant request id. The API mints one when absent,
/// but sending our own keeps logs joinable end to end.
String clientMessageIdForRequest() {
  final micros = DateTime.now().microsecondsSinceEpoch;
  final random = DateTime.now().hashCode.abs();
  return 'mob_${micros}_$random';
}

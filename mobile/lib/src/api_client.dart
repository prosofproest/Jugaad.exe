/// Typed client for the PS-03 `/v1` API.
///
/// The mobile app is an API-only client: it never talks to the database.
/// Errors follow the problem-details envelope in `final/TRD.md` §7.2.
library;

import 'dart:convert';

import 'package:http/http.dart' as http;

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
  ApiException(this.status, this.code, this.detail, this.requestId);

  final int status;
  final String code;
  final String? detail;
  final String? requestId;

  bool get retryable => status >= 500;

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

class SendResult {
  SendResult.fromJson(Map<String, dynamic> json)
    : replyText = (json['assistant_message'] as Map<String, dynamic>)['text'] as String?,
      isDemo = (json['assistant_message'] as Map<String, dynamic>)['is_demo'] as bool? ?? true;

  final String? replyText;
  final bool isDemo;
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
    required String text,
  }) async {
    final json = await _post(
      '/v1/conversations/$conversationId/messages',
      {'client_message_id': clientMessageId, 'text': text},
      headers: {'Idempotency-Key': clientMessageId},
    );
    return SendResult.fromJson(json);
  }

  Future<Map<String, dynamic>> _get(String path) async {
    final response = await _client.get(Uri.parse('$_baseUrl$path'));
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
        'Content-Type': 'application/json',
        'X-Request-ID': clientMessageIdForRequest(),
        ...headers,
      },
      body: jsonEncode(body),
    );
    return _decode(response);
  }

  Map<String, dynamic> _decode(http.Response response) {
    final decoded = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode >= 400) {
      throw ApiException(
        response.statusCode,
        decoded['code'] as String? ?? 'api_error',
        decoded['detail'] as String?,
        decoded['request_id'] as String?,
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

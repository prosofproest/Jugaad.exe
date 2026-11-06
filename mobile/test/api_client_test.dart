import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:ps03_mobile/src/api_client.dart';

void main() {
  test('uploadImage posts a multipart file to /v1/uploads', () async {
    final client = _RecordingClient(
      statusCode: 201,
      body: jsonEncode(_uploadDescriptorJson),
    );
    final api = ApiClient(client: client, baseUrl: 'http://example.test');

    final descriptor = await api.uploadImage(
      bytes: Uint8List.fromList([1, 2, 3]),
      filename: 'photo.jpg',
      contentType: 'image/jpeg',
    );

    final request = client.lastRequest as http.MultipartRequest;
    expect(request.method, 'POST');
    expect(request.url.toString(), 'http://example.test/v1/uploads');
    expect(request.files.single.field, 'file');
    expect(request.files.single.filename, 'photo.jpg');
    expect(request.files.single.contentType.mimeType, 'image/jpeg');
    expect(descriptor.uploadId, 'up_1');
    expect(descriptor.qualityResult, 'pass');
  });

  test('sendMessage references upload_id and sends the idempotency key',
      () async {
    final client = _RecordingClient(
      statusCode: 201,
      body: jsonEncode(_sendResultJson),
    );
    final api = ApiClient(client: client, baseUrl: 'http://example.test');

    await api.sendMessage(
      conversationId: 'conv_1',
      clientMessageId: 'cm_1',
      text: 'brown spots',
      image: const ImageReference(
        uploadId: 'up_1',
        filename: 'photo.jpg',
        contentType: 'image/jpeg',
        contentHash: 'sha256:abc',
      ),
    );

    final request = client.lastRequest as http.Request;
    expect(request.method, 'POST');
    expect(
      request.url.toString(),
      'http://example.test/v1/conversations/conv_1/messages',
    );
    expect(request.headers['Idempotency-Key'], 'cm_1');

    final body = jsonDecode(request.body) as Map<String, dynamic>;
    expect(body['client_message_id'], 'cm_1');
    expect(body['text'], 'brown spots');
    expect(
      (body['image'] as Map<String, dynamic>)['upload_id'],
      'up_1',
    );
  });

  test('a non-JSON error is surfaced as a retryable ApiException', () async {
    final client = _RecordingClient(
      statusCode: 502,
      body: '<html>bad gateway</html>',
    );
    final api = ApiClient(client: client, baseUrl: 'http://example.test');

    await expectLater(
      api.health(),
      throwsA(
        isA<ApiException>()
            .having((error) => error.status, 'status', 502)
            .having((error) => error.code, 'code', 'api_error')
            .having((error) => error.retryable, 'retryable', isTrue),
      ),
    );
  });
}

class _RecordingClient extends http.BaseClient {
  _RecordingClient({required this.statusCode, required this.body});

  final int statusCode;
  final String body;
  http.BaseRequest? lastRequest;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    lastRequest = request;
    return http.StreamedResponse(
      Stream<List<int>>.value(utf8.encode(body)),
      statusCode,
      headers: {'content-type': 'application/json'},
    );
  }
}

const Map<String, dynamic> _uploadDescriptorJson = {
  'upload_id': 'up_1',
  'filename': 'photo.jpg',
  'content_type': 'image/jpeg',
  'content_hash': 'sha256:abc',
  'size_bytes': 3,
  'width': 1,
  'height': 1,
  'quality_result': 'pass',
  'quality_flags': <String>[],
  'quality_gate_version': 'demo-quality-0.1',
  'preview_url': '/v1/uploads/up_1',
  'created_at': '2026-11-06T00:00:00Z',
  'is_demo': true,
};

const Map<String, dynamic> _sendResultJson = {
  'user_message': {
    'message_id': 'msg_1',
    'conversation_id': 'conv_1',
    'role': 'user',
    'kind': 'image',
    'text': 'brown spots',
    'client_message_id': 'cm_1',
    'created_at': '2026-11-06T00:00:00Z',
    'is_demo': false,
  },
  'assistant_message': {
    'message_id': 'msg_2',
    'conversation_id': 'conv_1',
    'role': 'assistant',
    'kind': 'assessment',
    'text': 'Assistive photo assessment, not a diagnosis.',
    'next_steps': ['request_review'],
    'created_at': '2026-11-06T00:00:01Z',
    'is_demo': true,
  },
};

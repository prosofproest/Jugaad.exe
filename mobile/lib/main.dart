import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'src/api_client.dart';
import 'src/chat_sync.dart';
import 'src/outbox.dart';

void main() => runApp(const Ps03App());

class Ps03App extends StatelessWidget {
  const Ps03App({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PS-03',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF9FE870)),
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final ApiClient _api = ApiClient();
  late Future<Health> _health = _api.health();

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }

  void _reload() {
    setState(() {
      _health = _api.health();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('PS-03')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          FutureBuilder<Health>(
            future: _health,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const ListTile(title: Text('Checking the API…'));
              }
              if (snapshot.hasError) {
                return Card(
                  child: ListTile(
                    leading: const Icon(Icons.cloud_off),
                    title: const Text('API unavailable'),
                    subtitle: Text('${snapshot.error}'),
                    trailing: TextButton(
                      onPressed: _reload,
                      child: const Text('Retry'),
                    ),
                  ),
                );
              }
              final health = snapshot.requireData;
              return Card(
                child: ListTile(
                  leading: const Icon(Icons.cloud_done),
                  title: Text('${health.service} ${health.version}'),
                  subtitle: Text('Environment: ${health.environment}'),
                ),
              );
            },
          ),
          const SizedBox(height: 8),
          const Card(
            child: ListTile(
              leading: Icon(Icons.eco),
              title: Text('Photo assessment'),
              subtitle: Text(
                'What might be visible on one plant. Assistive, not a diagnosis.',
              ),
            ),
          ),
          const Card(
            child: ListTile(
              leading: Icon(Icons.map),
              title: Text('Area outlook'),
              subtitle: Text(
                'A separate output for a whole area over a time window. Not available in this phase.',
              ),
            ),
          ),
          const SizedBox(height: 8),
          FilledButton(
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute<void>(builder: (_) => const ChatPage()),
              );
            },
            child: const Text('Open photo-assessment chat'),
          ),
          const SizedBox(height: 8),
          const Text(
            'Demo content: you can attach a photo, but the reply is a labelled '
            'template from the demo engine. No image model is connected in this '
            'phase.',
            style: TextStyle(fontSize: 12),
          ),
        ],
      ),
    );
  }
}

enum _BubbleStatus { sending, queued, failed, sent }

class _Bubble {
  const _Bubble({
    required this.id,
    required this.isUser,
    this.text,
    this.isDemo = false,
    this.imagePath,
    this.status = _BubbleStatus.sent,
    this.error,
    this.turn,
    this.assessment,
    this.nextSteps = const [],
  });

  final String id;
  final bool isUser;
  final String? text;
  final bool isDemo;
  final String? imagePath;
  final _BubbleStatus status;
  final String? error;
  final QueuedTurn? turn;
  final Assessment? assessment;
  final List<String> nextSteps;

  bool matches(String clientMessageId) =>
      id == clientMessageId || turn?.clientMessageId == clientMessageId;
}

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> with WidgetsBindingObserver {
  static const Duration _flushInterval = Duration(seconds: 15);
  static const int _maxImageBytes = 10 * 1024 * 1024;

  final ApiClient _api = ApiClient();
  final ImagePicker _picker = ImagePicker();
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scroll = ScrollController();
  final List<_Bubble> _messages = <_Bubble>[];

  late final Outbox _outbox;
  late final ChatSync _sync;
  Timer? _flushTimer;

  String? _conversationId;
  String? _draftImagePath;
  String? _draftImageName;
  String? _draftImageType;
  String? _error;
  bool _sending = false;
  bool _flushing = false;
  bool _loadingQueue = true;

  @override
  void initState() {
    super.initState();
    _outbox = Outbox(SharedPreferencesOutboxStorage());
    _sync = ChatSync(api: _api, outbox: _outbox);
    WidgetsBinding.instance.addObserver(this);
    unawaited(_loadQueue());
    _flushTimer = Timer.periodic(_flushInterval, (_) {
      unawaited(_flushQueue());
    });
  }

  @override
  void dispose() {
    _flushTimer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    _controller.dispose();
    _scroll.dispose();
    _api.close();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      unawaited(_flushQueue());
    }
  }

  Future<void> _loadQueue() async {
    final turns = await _outbox.load();
    if (!mounted) {
      return;
    }
    setState(() {
      for (final turn in turns) {
        final alreadyShown = _messages.any(
          (bubble) => bubble.matches(turn.clientMessageId),
        );
        if (!alreadyShown) {
          _messages.add(_bubbleFromTurn(turn));
        }
      }
      _loadingQueue = false;
    });
    if (turns.any((turn) => !turn.isFailed)) {
      unawaited(_flushQueue());
    }
    _scrollToBottom();
  }

  _Bubble _bubbleFromTurn(QueuedTurn turn) => _Bubble(
    id: turn.clientMessageId,
    isUser: true,
    text: turn.text,
    imagePath: turn.imagePath,
    status: turn.isFailed ? _BubbleStatus.failed : _BubbleStatus.queued,
    error: turn.lastError,
    turn: turn,
  );

  Future<void> _pickImage(ImageSource source) async {
    try {
      final picked = await _picker.pickImage(
        source: source,
        maxWidth: 1600,
        maxHeight: 1600,
        imageQuality: 85,
      );
      if (picked == null) {
        return;
      }

      final size = await picked.length();
      if (size > _maxImageBytes) {
        if (!mounted) {
          return;
        }
        setState(() => _error = 'Choose an image smaller than 10 MB.');
        return;
      }

      final contentType = _contentTypeFor(picked);
      if (contentType == null) {
        if (!mounted) {
          return;
        }
        setState(() => _error = 'Choose a JPEG, PNG or WebP image.');
        return;
      }

      if (!mounted) {
        return;
      }
      setState(() {
        _draftImagePath = picked.path;
        _draftImageName = picked.name.isEmpty ? 'photo.jpg' : picked.name;
        _draftImageType = contentType;
        _error = null;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() => _error = 'Could not open the camera or gallery. ($error)');
    }
  }

  String? _contentTypeFor(XFile file) {
    const allowed = <String>{'image/jpeg', 'image/png', 'image/webp'};
    final declared = file.mimeType?.toLowerCase();
    if (declared != null && allowed.contains(declared)) {
      return declared;
    }

    final name = file.name.toLowerCase();
    if (name.endsWith('.jpg') || name.endsWith('.jpeg')) {
      return 'image/jpeg';
    }
    if (name.endsWith('.png')) {
      return 'image/png';
    }
    if (name.endsWith('.webp')) {
      return 'image/webp';
    }
    return null;
  }

  Future<void> _showImageSourceSheet() async {
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.photo_camera),
              title: const Text('Take a photo'),
              onTap: () => Navigator.of(context).pop(ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Choose from gallery'),
              onTap: () => Navigator.of(context).pop(ImageSource.gallery),
            ),
          ],
        ),
      ),
    );
    if (source != null) {
      await _pickImage(source);
    }
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    final imagePath = _draftImagePath;
    if ((text.isEmpty && imagePath == null) || _sending || _flushing) {
      return;
    }

    final clientMessageId = clientMessageIdForRequest();
    final turn = QueuedTurn(
      clientMessageId: clientMessageId,
      text: text.isEmpty ? null : text,
      imagePath: imagePath,
      imageFilename: _draftImageName,
      imageContentType: _draftImageType,
      conversationId: _conversationId,
      queuedAt: DateTime.now().toUtc(),
    );

    setState(() {
      _sending = true;
      _error = null;
      _messages.add(
        _Bubble(
          id: clientMessageId,
          isUser: true,
          text: turn.text,
          imagePath: turn.imagePath,
          status: _BubbleStatus.sending,
          turn: turn,
        ),
      );
      _controller.clear();
      _draftImagePath = null;
      _draftImageName = null;
      _draftImageType = null;
    });
    _scrollToBottom();

    var current = turn;
    try {
      final result = await _sync.deliver(
        turn,
        conversationId: _conversationId,
        onTurnUpdated: (updated) {
          current = updated;
          _conversationId = updated.conversationId ?? _conversationId;
        },
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _removeBubble(clientMessageId);
        _addServerTurn(result, localImagePath: turn.imagePath);
      });
      _scrollToBottom();
    } on ImageUnavailable catch (error) {
      await _failTurn(current, '$error');
    } on ApiException catch (error) {
      if (error.retryable) {
        final queued = await _queueTurn(current);
        _markQueued(clientMessageId, queued);
      } else {
        await _failTurn(current, '$error');
      }
    } catch (error) {
      final queued = await _queueTurn(current);
      _markQueued(clientMessageId, queued);
    } finally {
      if (mounted) {
        setState(() => _sending = false);
      }
    }
  }

  /// Persist a non-retryable failure so the user can still see and delete it
  /// after a restart. A failed turn is never sent as if it were a reply.
  Future<void> _failTurn(QueuedTurn turn, String message) async {
    final failed = turn.copyWith(
      state: 'failed',
      retryable: false,
      lastError: message,
    );
    await _outbox.add(failed);
    _markFailed(turn.clientMessageId, message, turn: failed);
  }

  Future<QueuedTurn> _queueTurn(QueuedTurn turn) async {
    final queued = turn.copyWith(
      state: 'queued',
      retryable: true,
      lastError: null,
    );
    await _outbox.add(queued);
    return queued;
  }

  Future<void> _retry(QueuedTurn turn) async {
    if (_sending || _flushing) {
      return;
    }

    setState(() {
      _sending = true;
      _error = null;
      _replaceBubble(
        turn.clientMessageId,
        _Bubble(
          id: turn.clientMessageId,
          isUser: true,
          text: turn.text,
          imagePath: turn.imagePath,
          status: _BubbleStatus.sending,
          turn: turn,
        ),
      );
    });

    var current = turn.copyWith(
      state: 'queued',
      retryable: true,
      lastError: null,
    );
    try {
      final result = await _sync.deliver(
        current,
        conversationId: _conversationId,
        onTurnUpdated: (updated) {
          current = updated;
          _conversationId = updated.conversationId ?? _conversationId;
        },
      );
      await _outbox.remove(current.clientMessageId);
      if (!mounted) {
        return;
      }
      setState(() {
        _removeBubble(current.clientMessageId);
        _addServerTurn(result, localImagePath: current.imagePath);
      });
      _scrollToBottom();
    } on ImageUnavailable catch (error) {
      final failed = current.copyWith(
        state: 'failed',
        retryable: false,
        lastError: '$error',
      );
      await _outbox.update(failed);
      _markFailed(current.clientMessageId, '$error', turn: failed);
    } on ApiException catch (error) {
      if (error.retryable) {
        final queued = current.copyWith(
          state: 'queued',
          retryable: true,
          lastError: '$error',
        );
        await _outbox.update(queued);
        _markQueued(current.clientMessageId, queued);
      } else {
        final failed = current.copyWith(
          state: 'failed',
          retryable: false,
          lastError: '$error',
        );
        await _outbox.update(failed);
        _markFailed(current.clientMessageId, '$error', turn: failed);
      }
    } catch (error) {
      final queued = current.copyWith(
        state: 'queued',
        retryable: true,
        lastError: 'Network unavailable. Will retry when connected.',
      );
      await _outbox.update(queued);
      _markQueued(current.clientMessageId, queued);
    } finally {
      if (mounted) {
        setState(() => _sending = false);
      }
    }
  }

  Future<void> _delete(QueuedTurn turn) async {
    await _outbox.remove(turn.clientMessageId);
    if (!mounted) {
      return;
    }
    setState(() => _removeBubble(turn.clientMessageId));
  }

  Future<void> _flushQueue() async {
    if (_flushing || _sending) {
      return;
    }
    _flushing = true;
    try {
      final report = await _sync.flush(
        conversationId: _conversationId,
        onSent: (sent) {
          final conversationId = sent.result.userMessage.conversationId;
          if (conversationId.isNotEmpty) {
            _conversationId = conversationId;
          }
        },
        onTurnUpdated: (turn) {
          _conversationId = turn.conversationId ?? _conversationId;
        },
      );
      if (!mounted) {
        return;
      }
      setState(() {
        for (final sent in report.sent) {
          _removeBubble(sent.turn.clientMessageId);
          _addServerTurn(sent.result, localImagePath: sent.turn.imagePath);
        }
        for (final turn in report.remaining) {
          _updateBubbleFromTurn(turn);
        }
        if (report.hasQueued) {
          _error =
              'Some messages are still queued. They will be sent when the '
              'connection returns.';
        } else if (report.sent.isNotEmpty) {
          _error = null;
        }
      });
      if (report.sent.isNotEmpty) {
        _scrollToBottom();
      }
    } finally {
      _flushing = false;
    }
  }

  void _addServerTurn(SendResult result, {String? localImagePath}) {
    final user = result.userMessage;
    _messages.add(
      _Bubble(
        id: user.messageId,
        isUser: true,
        text: user.text,
        imagePath: localImagePath,
        status: _BubbleStatus.sent,
      ),
    );

    final assistant = result.assistantMessage;
    _messages.add(
      _Bubble(
        id: assistant.messageId,
        isUser: false,
        text: assistant.text,
        isDemo: assistant.isDemo,
        assessment: assistant.assessment,
        nextSteps: assistant.nextSteps,
        status: _BubbleStatus.sent,
      ),
    );
  }

  void _replaceBubble(String clientMessageId, _Bubble bubble) {
    final index = _messages.indexWhere(
      (item) => item.matches(clientMessageId),
    );
    if (index < 0) {
      _messages.add(bubble);
    } else {
      _messages[index] = bubble;
    }
  }

  void _removeBubble(String clientMessageId) {
    _messages.removeWhere((bubble) => bubble.matches(clientMessageId));
  }

  void _markQueued(String clientMessageId, QueuedTurn turn) {
    if (!mounted) {
      return;
    }
    setState(() {
      _replaceBubble(
        clientMessageId,
        _Bubble(
          id: clientMessageId,
          isUser: true,
          text: turn.text,
          imagePath: turn.imagePath,
          status: _BubbleStatus.queued,
          turn: turn,
        ),
      );
      _error =
          'You are offline or the server is unreachable. The message is '
          'queued and will be sent when connected.';
    });
  }

  void _markFailed(
    String clientMessageId,
    String message, {
    QueuedTurn? turn,
  }) {
    if (!mounted) {
      return;
    }
    setState(() {
      final index = _messages.indexWhere(
        (bubble) => bubble.matches(clientMessageId),
      );
      if (index >= 0) {
        final existing = _messages[index];
        _messages[index] = _Bubble(
          id: existing.id,
          isUser: true,
          text: existing.text,
          imagePath: existing.imagePath,
          status: _BubbleStatus.failed,
          error: message,
          turn: turn ?? existing.turn,
        );
      }
      _error = message;
    });
  }

  void _updateBubbleFromTurn(QueuedTurn turn) {
    _replaceBubble(turn.clientMessageId, _bubbleFromTurn(turn));
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scroll.hasClients) {
        return;
      }
      _scroll.jumpTo(_scroll.position.maxScrollExtent);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Photo assessment')),
      body: Column(
        children: [
          Expanded(
            child: _loadingQueue
                ? const Center(child: CircularProgressIndicator())
                : _messages.isEmpty
                ? const Center(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Text(
                        'Attach a photo or describe what you see on the plant. '
                        'A photo is uploaded first, then the message references '
                        'it.',
                        textAlign: TextAlign.center,
                      ),
                    ),
                  )
                : ListView.builder(
                    controller: _scroll,
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) => _MessageCard(
                      bubble: _messages[index],
                      onRetry: _retry,
                      onDelete: _delete,
                    ),
                  ),
          ),
          if (_error != null) _errorBanner(),
          _composer(),
        ],
      ),
    );
  }

  Widget _errorBanner() {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 8, 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline, size: 18, color: theme.colorScheme.error),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _error!,
              style: TextStyle(color: theme.colorScheme.error),
            ),
          ),
          IconButton(
            onPressed: () => setState(() => _error = null),
            icon: const Icon(Icons.close),
            tooltip: 'Dismiss',
          ),
        ],
      ),
    );
  }

  Widget _composer() {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (_draftImagePath != null) _draftPreview(),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                IconButton(
                  onPressed: _sending ? null : _showImageSourceSheet,
                  icon: const Icon(Icons.add_a_photo),
                  tooltip: 'Attach a photo',
                ),
                Expanded(
                  child: TextField(
                    controller: _controller,
                    maxLength: 1000,
                    minLines: 1,
                    maxLines: 4,
                    decoration: const InputDecoration(
                      labelText: 'Message (optional with a photo)',
                      hintText: 'Example: yellowing between the veins',
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                FilledButton(
                  onPressed: _sending || _flushing ? null : _send,
                  child: Text(_sending ? 'Sending…' : 'Send'),
                ),
              ],
            ),
            const Text(
              'Demo content: the reply is a labelled template from the demo '
              'engine, not a diagnosis.',
              style: TextStyle(fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  Widget _draftPreview() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          _LocalImage(path: _draftImagePath!, width: 72, height: 72),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _draftImageName ?? 'Photo attached',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          IconButton(
            onPressed: () => setState(() {
              _draftImagePath = null;
              _draftImageName = null;
              _draftImageType = null;
            }),
            icon: const Icon(Icons.close),
            tooltip: 'Remove photo',
          ),
        ],
      ),
    );
  }
}

class _MessageCard extends StatelessWidget {
  const _MessageCard({
    required this.bubble,
    required this.onRetry,
    required this.onDelete,
  });

  final _Bubble bubble;
  final Future<void> Function(QueuedTurn turn) onRetry;
  final Future<void> Function(QueuedTurn turn) onDelete;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final turn = bubble.turn;

    return Card(
      color: bubble.isUser
          ? theme.colorScheme.surfaceContainerHighest
          : null,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    bubble.isUser ? 'You' : 'Assistant',
                    style: theme.textTheme.titleSmall,
                  ),
                ),
                Wrap(
                  spacing: 4,
                  children: [
                    if (bubble.status == _BubbleStatus.sending)
                      const _StatusChip('sending'),
                    if (bubble.status == _BubbleStatus.queued)
                      const _StatusChip('queued'),
                    if (bubble.status == _BubbleStatus.failed)
                      const _StatusChip('failed'),
                    if (bubble.isDemo) const _StatusChip('demo'),
                  ],
                ),
              ],
            ),
            if (bubble.imagePath != null) ...[
              const SizedBox(height: 8),
              _LocalImage(path: bubble.imagePath!),
            ],
            if (bubble.text != null && bubble.text!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(bubble.text!),
            ],
            if (bubble.assessment != null) ...[
              const SizedBox(height: 8),
              _AssessmentCard(assessment: bubble.assessment!),
            ],
            if (!bubble.isUser && bubble.nextSteps.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                'Next safe steps: ${bubble.nextSteps.join(', ')}',
                style: theme.textTheme.bodySmall,
              ),
            ],
            if (bubble.status == _BubbleStatus.queued && turn != null) ...[
              const SizedBox(height: 8),
              const Text('Will be assessed when connected.'),
              TextButton(
                onPressed: () => unawaited(onRetry(turn)),
                child: const Text('Retry now'),
              ),
            ],
            if (bubble.status == _BubbleStatus.failed && turn != null) ...[
              if (bubble.error != null)
                Text(
                  bubble.error!,
                  style: TextStyle(color: theme.colorScheme.error),
                ),
              Row(
                children: [
                  TextButton(
                    onPressed: () => unawaited(onRetry(turn)),
                    child: const Text('Retry'),
                  ),
                  TextButton(
                    onPressed: () => unawaited(onDelete(turn)),
                    child: const Text('Delete'),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip(this.label);

  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: theme.colorScheme.secondaryContainer,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(label, style: theme.textTheme.labelSmall),
    );
  }
}

class _LocalImage extends StatelessWidget {
  const _LocalImage({
    required this.path,
    this.width = 160,
    this.height = 160,
  });

  final String path;
  final double width;
  final double height;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: Image.file(
        File(path),
        width: width,
        height: height,
        fit: BoxFit.cover,
        errorBuilder: (context, error, stackTrace) => Container(
          width: width,
          height: height,
          color: theme.colorScheme.surfaceContainerHighest,
          alignment: Alignment.center,
          child: const Icon(Icons.broken_image, size: 28),
        ),
      ),
    );
  }
}

class _AssessmentCard extends StatelessWidget {
  const _AssessmentCard({required this.assessment});

  final Assessment assessment;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final candidates = assessment.candidates
        .map((candidate) => candidate.displayName ?? candidate.label)
        .take(3)
        .join(', ');

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        border: Border.all(color: theme.colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Assistive photo assessment — not a diagnosis.'),
          const SizedBox(height: 4),
          Text('State: ${assessment.state}'),
          if (assessment.reasonText != null) Text(assessment.reasonText!),
          if (candidates.isNotEmpty) Text('Possibilities: $candidates'),
          Text(
            'Confidence: ${assessment.confidenceBand ?? 'not_calibrated'}',
          ),
          Text('Calibrated: ${assessment.calibrated ? 'yes' : 'no'}'),
          Text('Model: ${assessment.modelVersion}'),
          if (assessment.generatedAt != null)
            Text(
              'Generated: ${assessment.generatedAt!.toLocal().toIso8601String()}',
            ),
        ],
      ),
    );
  }
}

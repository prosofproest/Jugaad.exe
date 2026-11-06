import 'package:flutter/material.dart';

import 'src/api_client.dart';

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
            'Demo content: the chat returns a labelled template reply. '
            'No image model is connected in this phase.',
            style: TextStyle(fontSize: 12),
          ),
        ],
      ),
    );
  }
}

class _Bubble {
  const _Bubble({required this.text, required this.isUser, this.isDemo = false});

  final String text;
  final bool isUser;
  final bool isDemo;
}

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final ApiClient _api = ApiClient();
  final TextEditingController _controller = TextEditingController();
  final List<_Bubble> _messages = <_Bubble>[];

  String? _conversationId;
  String? _pendingText;
  String? _pendingId;
  String? _error;
  bool _sending = false;

  @override
  void dispose() {
    _controller.dispose();
    _api.close();
    super.dispose();
  }

  Future<void> _send(String text, {String? id}) async {
    final clientMessageId = id ?? clientMessageIdForRequest();
    setState(() {
      _sending = true;
      _error = null;
      _pendingText = text;
      _pendingId = clientMessageId;
    });

    try {
      final conversationId =
          _conversationId ??= await _api.createConversation();
      final result = await _api.sendMessage(
        conversationId: conversationId,
        clientMessageId: clientMessageId,
        text: text,
      );
      if (!mounted) {
        return;
      }

      setState(() {
        _messages.add(_Bubble(text: text, isUser: true));
        _messages.add(
          _Bubble(
            text: result.replyText ?? 'No reply text.',
            isUser: false,
            isDemo: result.isDemo,
          ),
        );
        _pendingText = null;
        _pendingId = null;
        _controller.clear();
      });
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() => _error = '$error');
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _error = 'Network unavailable. The message is kept; retry when connected. ($error)';
      });
    } finally {
      if (mounted) {
        setState(() => _sending = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Photo assessment')),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final bubble = _messages[index];
                return Card(
                  color: bubble.isUser
                      ? Theme.of(context).colorScheme.surfaceContainerHighest
                      : null,
                  child: ListTile(
                    title: Text(bubble.isUser ? 'You' : 'Assistant'),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(bubble.text),
                        if (bubble.isDemo)
                          const Padding(
                            padding: EdgeInsets.only(top: 4),
                            child: Text(
                              'demo',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                          ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                  if (_pendingText != null)
                    TextButton(
                      onPressed: _sending
                          ? null
                          : () => _send(_pendingText!, id: _pendingId),
                      child: const Text('Retry'),
                    ),
                ],
              ),
            ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      maxLength: 1000,
                      decoration: const InputDecoration(
                        labelText: 'Message',
                        hintText: 'Example: yellowing between the veins',
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  FilledButton(
                    onPressed: _sending
                        ? null
                        : () {
                            final text = _controller.text.trim();
                            if (text.isEmpty) {
                              return;
                            }
                            _send(text);
                          },
                    child: Text(_sending ? 'Sending…' : 'Send'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

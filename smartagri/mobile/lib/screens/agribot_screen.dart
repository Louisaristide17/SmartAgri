import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../services/api_service.dart';
import '../models/models.dart';
import '../widgets/common_widgets.dart';

class AgribotScreen extends StatefulWidget {
  const AgribotScreen({super.key});

  @override
  State<AgribotScreen> createState() => _AgribotScreenState();
}

class _AgribotScreenState extends State<AgribotScreen> {
  final _api = ApiService();
  final _msgCtrl     = TextEditingController();
  final _scrollCtrl  = ScrollController();
  final List<ChatMessage> _messages = [];
  bool _sending   = false;
  bool _loading   = true;
  bool _showSugg  = true;   // Afficher suggestions si historique vide

  // ── Questions suggérées ────────────────────────────
  static const List<Map<String, String>> _suggestions = [
    {'icon': '🍫', 'text': 'Quels engrais pour le cacao en Côte d\'Ivoire ?'},
    {'icon': '🌾', 'text': 'Quelle est la meilleure période pour semer le riz ?'},
    {'icon': '🍠', 'text': 'Comment améliorer le rendement de l\'igname ?'},
    {'icon': '🥜', 'text': 'Mon anacarde a des maladies, que faire ?'},
    {'icon': '💧', 'text': 'Comment calculer le besoin en eau du maïs ?'},
    {'icon': '🌴', 'text': 'Conseils pour le palmier à huile au Sud CI ?'},
    {'icon': '📅', 'text': 'Quel est le calendrier cultural pour la Côte d\'Ivoire ?'},
    {'icon': '🦠', 'text': 'Comment lutter contre la pourriture brune du cacao ?'},
  ];

  @override
  void initState() {
    super.initState();
    _loadHistorique();
  }

  @override
  void dispose() {
    _msgCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadHistorique() async {
    setState(() => _loading = true);
    try {
      final list = await _api.getHistoriqueChat();
      setState(() {
        _messages.clear();
        _messages.addAll(list.map((e) => ChatMessage.fromJson(e)));
        _loading  = false;
        _showSugg = _messages.isEmpty;
      });
      _scrollToBottom();
    } catch (_) {
      setState(() { _loading = false; });
      _showWelcome();
    }
  }

  void _showWelcome() {
    if (_messages.isEmpty) {
      setState(() {
        _messages.add(ChatMessage(
          role: 'assistant',
          content: '👋 Bonjour ! Je suis **AgriBot**, votre assistant agricole pour la 🇨🇮 Côte d\'Ivoire.\n\n'
              'Je peux vous aider sur :\n'
              '• 🍫 Le cacao, café et anacarde\n'
              '• 🌾 Le maïs, riz, manioc et igname\n'
              '• 💧 L\'irrigation et la pluviométrie locale\n'
              '• 🌿 Les engrais et la fertilité des sols\n'
              '• 📅 Les calendriers culturaux (Sud, Centre, Nord CI)\n'
              '• 🦠 Les maladies et ravageurs locaux\n\n'
              'Posez-moi votre question !',
          createdAt: DateTime.now(),
        ));
        _showSugg = true;
      });
    }
  }

  Future<void> _send(String text) async {
    final content = text.trim();
    if (content.isEmpty) return;
    _msgCtrl.clear();

    setState(() {
      _messages.add(ChatMessage(role: 'user', content: content, createdAt: DateTime.now()));
      _sending  = true;
      _showSugg = false;
    });
    _scrollToBottom();

    try {
      final resp = await _api.sendMessage(content);
      final msg  = ChatMessage.fromJson(resp);
      setState(() {
        _messages.add(msg);
        _sending = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _messages.add(ChatMessage(
            role: 'assistant',
            content: '❌ Erreur : ${e.message}',
            createdAt: DateTime.now()));
        _sending = false;
      });
    } catch (_) {
      setState(() {
        _messages.add(ChatMessage(
            role: 'assistant',
            content: '❌ Serveur inaccessible. Vérifiez votre connexion.',
            createdAt: DateTime.now()));
        _sending = false;
      });
    }
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _clearHistory() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('🗑️ Effacer la conversation'),
        content: const Text('Voulez-vous supprimer tout l\'historique ?',
            style: TextStyle(fontSize: 14)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false),
              child: const Text('Annuler')),
          ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.red, minimumSize: Size.zero,
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10)),
              child: const Text('Effacer')),
        ],
      ),
    );
    if (ok == true) {
      await _api.clearHistoriqueChat();
      setState(() { _messages.clear(); _showSugg = true; });
      _showWelcome();
      if (mounted) showSnack(context, 'Conversation effacée.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.gray50,
      appBar: _buildAppBar(),
      body: Column(
        children: [
          // Messages
          Expanded(child: _buildMessages()),

          // Suggestions (si affichées)
          if (_showSugg && !_loading) _buildSuggestions(),

          // Zone de saisie
          _buildInputZone(),
        ],
      ),
    );
  }

  // ── AppBar ────────────────────────────────────────
  AppBar _buildAppBar() {
    return AppBar(
      backgroundColor: AppColors.green700,
      foregroundColor: AppColors.white,
      titleSpacing: 0,
      title: Row(children: [
        Container(
          width: 36, height: 36,
          decoration: BoxDecoration(
            color: Colors.white24, borderRadius: BorderRadius.circular(18)),
          child: const Center(child: Text('👵🏻', style: TextStyle(fontSize: 18))),
        ),
        const SizedBox(width: 10),
        Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('AgriBot',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800,
                color: AppColors.white)),
          Row(children: [
            Container(width: 7, height: 7,
              decoration: BoxDecoration(
                color: const Color(0xFF22C55E),
                borderRadius: BorderRadius.circular(3.5),
              )),
            const SizedBox(width: 5),
            const Text('En ligne · Assistant IA',
              style: TextStyle(fontSize: 11, color: Colors.white70)),
          ]),
        ]),
      ]),
      actions: [
        IconButton(
          icon: const Icon(Icons.delete_outline, color: Colors.white70),
          tooltip: 'Effacer la conversation',
          onPressed: _clearHistory,
        ),
      ],
    );
  }

  // ── Zone messages ─────────────────────────────────
  Widget _buildMessages() {
    if (_loading) {
      return const Center(child: CircularProgressIndicator(color: AppColors.green500));
    }

    return ListView.builder(
      controller: _scrollCtrl,
      padding: const EdgeInsets.fromLTRB(12, 16, 12, 8),
      itemCount: _messages.length + (_sending ? 1 : 0),
      itemBuilder: (_, i) {
        if (i == _messages.length) return _TypingIndicator();
        return _MessageBubble(message: _messages[i]);
      },
    );
  }

  // ── Suggestions rapides ───────────────────────────
  Widget _buildSuggestions() {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
      color: AppColors.gray50,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(left: 4, bottom: 8),
            child: Text('💡 Questions fréquentes',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700,
                  color: AppColors.gray500)),
          ),
          SizedBox(
            height: 88,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: _suggestions.length,
              itemBuilder: (_, i) {
                final s = _suggestions[i];
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: GestureDetector(
                    onTap: () => _send(s['text']!),
                    child: Container(
                      width: 160,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.white,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppColors.green200),
                        boxShadow: [BoxShadow(
                          color: Colors.black.withOpacity(0.04),
                          blurRadius: 4, offset: const Offset(0, 2))],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(s['icon']!, style: const TextStyle(fontSize: 20)),
                          Text(s['text']!,
                            style: const TextStyle(fontSize: 12,
                                fontWeight: FontWeight.w500, color: AppColors.gray700),
                            maxLines: 2, overflow: TextOverflow.ellipsis),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  // ── Zone de saisie ────────────────────────────────
  Widget _buildInputZone() {
    return Container(
      padding: EdgeInsets.fromLTRB(12, 8, 12,
          MediaQuery.of(context).padding.bottom + 8),
      decoration: BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.gray200)),
        boxShadow: [BoxShadow(
          color: Colors.black.withOpacity(0.06),
          blurRadius: 8, offset: const Offset(0, -2))],
      ),
      child: Row(children: [
        Expanded(
          child: TextField(
            controller: _msgCtrl,
            minLines: 1, maxLines: 3,
            textInputAction: TextInputAction.send,
            onSubmitted: _send,
            decoration: InputDecoration(
              hintText: 'Posez votre question agricole…',
              hintStyle: const TextStyle(fontSize: 14, color: AppColors.gray400),
              filled: true, fillColor: AppColors.gray50,
              contentPadding: const EdgeInsets.symmetric(
                  horizontal: 16, vertical: 12),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(24),
                borderSide: BorderSide.none),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(24),
                borderSide: const BorderSide(color: AppColors.gray200)),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(24),
                borderSide: const BorderSide(color: AppColors.green500, width: 1.5)),
            ),
          ),
        ),
        const SizedBox(width: 8),
        // Bouton envoyer
        GestureDetector(
          onTap: _sending ? null : () => _send(_msgCtrl.text),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            width: 48, height: 48,
            decoration: BoxDecoration(
              gradient: _sending ? null : AppColors.primaryGradient,
              color: _sending ? AppColors.gray300 : null,
              borderRadius: BorderRadius.circular(24),
              boxShadow: _sending ? null : [BoxShadow(
                color: AppColors.green500.withOpacity(0.35),
                blurRadius: 8, offset: const Offset(0, 3))],
            ),
            child: _sending
                ? const Center(child: SizedBox(width: 20, height: 20,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: AppColors.white)))
                : const Center(child: Icon(Icons.send_rounded,
                    color: AppColors.white, size: 22)),
          ),
        ),
      ]),
    );
  }
}

// ── Bulle de message ──────────────────────────────────────────────
class _MessageBubble extends StatelessWidget {
  final ChatMessage message;
  const _MessageBubble({required this.message});

  // Rendu simple du markdown (**gras**, • liste)
  List<TextSpan> _parseContent(String content) {
    final spans = <TextSpan>[];
    final parts  = content.split('**');
    for (int i = 0; i < parts.length; i++) {
      if (i % 2 == 1) {
        spans.add(TextSpan(text: parts[i],
            style: const TextStyle(fontWeight: FontWeight.w700)));
      } else {
        spans.add(TextSpan(text: parts[i]));
      }
    }
    return spans;
  }

  @override
  Widget build(BuildContext context) {
    final isUser = message.isUser;
    final time = message.createdAt != null
        ? '${message.createdAt!.hour.toString().padLeft(2,'0')}:${message.createdAt!.minute.toString().padLeft(2,'0')}'
        : '';

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          // Avatar bot
          if (!isUser) ...[
            Container(
              width: 32, height: 32,
              decoration: BoxDecoration(
                color: AppColors.green100, borderRadius: BorderRadius.circular(16)),
              child: const Center(child: Text('👵🏻', style: TextStyle(fontSize: 16))),
            ),
            const SizedBox(width: 8),
          ],

          // Bulle
          Flexible(child: Column(
            crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
            children: [
              Container(
                constraints: BoxConstraints(
                  maxWidth: MediaQuery.of(context).size.width * 0.75),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: isUser ? AppColors.green500 : AppColors.white,
                  borderRadius: BorderRadius.circular(18).copyWith(
                    bottomRight: isUser ? const Radius.circular(4) : null,
                    bottomLeft: !isUser ? const Radius.circular(4) : null,
                  ),
                  border: isUser ? null : Border.all(color: AppColors.gray200),
                  boxShadow: [BoxShadow(
                    color: Colors.black.withOpacity(0.06),
                    blurRadius: 4, offset: const Offset(0, 2))],
                ),
                child: RichText(
                  text: TextSpan(
                    style: TextStyle(
                      fontSize: 14,
                      color: isUser ? AppColors.white : AppColors.gray800,
                      height: 1.5,
                    ),
                    children: _parseContent(message.content),
                  ),
                ),
              ),
              const SizedBox(height: 3),
              Text(time,
                style: const TextStyle(fontSize: 10, color: AppColors.gray400)),
            ],
          )),

          // Avatar user
          if (isUser) ...[
            const SizedBox(width: 8),
            Container(
              width: 32, height: 32,
              decoration: BoxDecoration(
                gradient: AppColors.primaryGradient,
                borderRadius: BorderRadius.circular(16)),
              child: const Center(child: Text('👤',
                  style: TextStyle(fontSize: 14))),
            ),
          ],
        ],
      ),
    );
  }
}

// ── Indicateur de frappe ──────────────────────────────────────────
class _TypingIndicator extends StatefulWidget {
  @override
  State<_TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<_TypingIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 900))
      ..repeat(reverse: true);
  }
  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(children: [
        Container(
          width: 32, height: 32,
          decoration: BoxDecoration(
              color: AppColors.green100,
              borderRadius: BorderRadius.circular(16)),
          child: const Center(child: Text('👵🏻', style: TextStyle(fontSize: 16)))),
        const SizedBox(width: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.white, borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.gray200)),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            _Dot(delay: 0, ctrl: _ctrl),
            const SizedBox(width: 5),
            _Dot(delay: 0.2, ctrl: _ctrl),
            const SizedBox(width: 5),
            _Dot(delay: 0.4, ctrl: _ctrl),
          ]),
        ),
      ]),
    );
  }
}

class _Dot extends StatelessWidget {
  final double delay;
  final AnimationController ctrl;
  const _Dot({required this.delay, required this.ctrl});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: ctrl,
      builder: (_, __) {
        final val = Curves.easeInOut.transform(
            ((ctrl.value - delay).clamp(0.0, 1.0)));
        return Transform.translate(
          offset: Offset(0, -4 * val),
          child: Container(
            width: 8, height: 8,
            decoration: BoxDecoration(
              color: AppColors.green500, borderRadius: BorderRadius.circular(4))),
        );
      },
    );
  }
}

extension on AppColors {
  static const Color gray800  = Color(0xFF1F2937);
  static const Color green200 = Color(0xFFB7E4C7);
}

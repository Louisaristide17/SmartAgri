import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../services/api_service.dart';
import '../widgets/common_widgets.dart';

class LoginScreen extends StatefulWidget {
  final VoidCallback onLoginSuccess;
  const LoginScreen({super.key, required this.onLoginSuccess});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;
  bool _loading = false;

  // ── Connexion ──
  final _loginKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController(text: 'demo@smartagri.com');
  final _pwdCtrl   = TextEditingController(text: 'Demo1234!');
  bool _showPwd    = false;

  // ── Inscription ──
  final _regKey    = GlobalKey<FormState>();
  final _fnCtrl    = TextEditingController();
  final _lnCtrl    = TextEditingController();
  final _regEmailCtrl = TextEditingController();
  final _regPwdCtrl   = TextEditingController();
  final _phoneCtrl    = TextEditingController();
  bool _showRegPwd    = false;
  String _selectedRole = 'agriculteur';

  final _api = ApiService();

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabs.dispose();
    _emailCtrl.dispose(); _pwdCtrl.dispose();
    _fnCtrl.dispose(); _lnCtrl.dispose();
    _regEmailCtrl.dispose(); _regPwdCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  // ── Connexion ──────────────────────────────────────
  Future<void> _login() async {
    if (!_loginKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await _api.login(_emailCtrl.text.trim(), _pwdCtrl.text);
      widget.onLoginSuccess();
    } on ApiException catch (e) {
      if (mounted) showSnack(context, e.message, error: true);
    } catch (_) {
      if (mounted) showSnack(context, 'Impossible de joindre le serveur.', error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  // ── Inscription ────────────────────────────────────
  Future<void> _register() async {
    if (!_regKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await _api.register(
        firstname: _fnCtrl.text.trim(),
        lastname:  _lnCtrl.text.trim(),
        email:     _regEmailCtrl.text.trim(),
        password:  _regPwdCtrl.text,
        phone:     _phoneCtrl.text.trim().isEmpty ? null : _phoneCtrl.text.trim(),
        role:      _selectedRole,
      );
      widget.onLoginSuccess();
    } on ApiException catch (e) {
      if (mounted) showSnack(context, e.message, error: true);
    } catch (_) {
      if (mounted) showSnack(context, 'Impossible de joindre le serveur.', error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.green900,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            children: [
              // ── Hero branding ──
              _buildHero(),
              // ── Carte formulaire ──
              _buildFormCard(),
            ],
          ),
        ),
      ),
    );
  }

  // ── Hero ──────────────────────────────────────────
  Widget _buildHero() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(24, 40, 24, 32),
      decoration: const BoxDecoration(
        gradient: AppColors.heroGradient,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Logo
          Row(children: [
            Container(
              width: 52, height: 52,
              decoration: BoxDecoration(
                color: AppColors.green100,
                borderRadius: BorderRadius.circular(14),
              ),
              child: const Center(
                child: Text('🌱', style: TextStyle(fontSize: 28)),
              ),
            ),
            const SizedBox(width: 12),
            const Text('SmartAgri',
              style: TextStyle(
                fontSize: 28, fontWeight: FontWeight.w800,
                color: AppColors.white, letterSpacing: -0.5)),
          ]),
          const SizedBox(height: 24),
          const Text('Cultivez l\'intelligence,\nrécoltez la performance.',
            style: TextStyle(
              fontSize: 22, fontWeight: FontWeight.w700,
              color: AppColors.white, height: 1.3)),
          const SizedBox(height: 12),
          Text('La plateforme qui transforme vos données agricoles en décisions gagnantes.',
            style: TextStyle(
              fontSize: 14, color: Colors.white.withOpacity(0.75), height: 1.5)),
          const SizedBox(height: 20),
          // Features pills
          Wrap(spacing: 8, runSpacing: 8, children: [
            _pill('📊 Prédiction IA'),
            _pill('🗺️ Parcelles GPS'),
            _pill('👵🏻 AgriBot'),
            _pill('🌦️ Météo'),
          ]),
        ],
      ),
    );
  }

  Widget _pill(String label) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
    decoration: BoxDecoration(
      color: Colors.white.withOpacity(0.15),
      borderRadius: BorderRadius.circular(999),
      border: Border.all(color: Colors.white.withOpacity(0.3)),
    ),
    child: Text(label,
      style: const TextStyle(
        fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.white)),
  );

  // ── Carte formulaire ──────────────────────────────
  Widget _buildFormCard() {
    return Container(
      width: double.infinity,
      decoration: const BoxDecoration(
        color: AppColors.gray50,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: Column(
        children: [
          const SizedBox(height: 8),
          // Handle
          Container(width: 40, height: 4,
            decoration: BoxDecoration(
              color: AppColors.gray300,
              borderRadius: BorderRadius.circular(2))),
          const SizedBox(height: 16),

          // Onglets
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 20),
            decoration: BoxDecoration(
              color: AppColors.gray100,
              borderRadius: BorderRadius.circular(12),
            ),
            child: TabBar(
              controller: _tabs,
              indicator: BoxDecoration(
                color: AppColors.white,
                borderRadius: BorderRadius.circular(10),
                boxShadow: [BoxShadow(
                  color: Colors.black.withOpacity(0.08),
                  blurRadius: 4, offset: const Offset(0, 2))],
              ),
              indicatorSize: TabBarIndicatorSize.tab,
              labelColor: AppColors.green700,
              unselectedLabelColor: AppColors.gray500,
              labelStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
              unselectedLabelStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
              dividerColor: Colors.transparent,
              tabs: const [
                Tab(text: 'Connexion'),
                Tab(text: 'Inscription'),
              ],
            ),
          ),
          const SizedBox(height: 4),

          // Contenu onglets
          SizedBox(
            height: 520,
            child: TabBarView(
              controller: _tabs,
              children: [_buildLoginForm(), _buildRegisterForm()],
            ),
          ),

          // Compte démo
          Container(
            margin: const EdgeInsets.fromLTRB(20, 0, 20, 20),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.blueBg,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.blue.withOpacity(0.3)),
            ),
            child: Row(children: [
              const Text('🔑', style: TextStyle(fontSize: 18)),
              const SizedBox(width: 10),
              Expanded(child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Compte démo',
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700,
                        color: Color(0xFF1E40AF))),
                  const SizedBox(height: 2),
                  Text('demo@smartagri.com  ·  Demo1234!',
                    style: TextStyle(fontSize: 12, color: AppColors.blue.withOpacity(0.8))),
                ],
              )),
              TextButton(
                onPressed: () {
                  _emailCtrl.text = 'demo@smartagri.com';
                  _pwdCtrl.text   = 'Demo1234!';
                  showSnack(context, 'Identifiants pré-remplis !');
                },
                style: TextButton.styleFrom(
                  minimumSize: Size.zero,
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                child: const Text('Utiliser',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700,
                      color: Color(0xFF1E40AF))),
              ),
            ]),
          ),
        ],
      ),
    );
  }

  // ── Formulaire connexion ──────────────────────────
  Widget _buildLoginForm() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
      child: Form(
        key: _loginKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Bon retour 👋',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800,
                  color: AppColors.gray900)),
            const SizedBox(height: 4),
            const Text('Connectez-vous à votre espace SmartAgri',
              style: TextStyle(fontSize: 13, color: AppColors.gray500)),
            const SizedBox(height: 24),

            SmartTextField(
              label: 'Adresse e-mail',
              hint: 'vous@exemple.com',
              prefixIcon: '✉️',
              controller: _emailCtrl,
              keyboardType: TextInputType.emailAddress,
              validator: (v) {
                if (v == null || v.isEmpty) return 'E-mail requis';
                if (!v.contains('@')) return 'E-mail invalide';
                return null;
              },
            ),
            const SizedBox(height: 16),

            SmartTextField(
              label: 'Mot de passe',
              hint: '••••••••',
              prefixIcon: '🔒',
              controller: _pwdCtrl,
              obscure: !_showPwd,
              suffixWidget: IconButton(
                icon: Icon(_showPwd ? Icons.visibility_off : Icons.visibility,
                    color: AppColors.gray400),
                onPressed: () => setState(() => _showPwd = !_showPwd),
              ),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Mot de passe requis';
                return null;
              },
            ),
            const SizedBox(height: 8),

            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: () => showSnack(context,
                    'Réinitialisation par e-mail — à connecter au backend.'),
                child: const Text('Mot de passe oublié ?'),
              ),
            ),
            const SizedBox(height: 8),

            PrimaryButton(
              label: 'Se connecter',
              icon: '🚀',
              loading: _loading,
              onTap: _login,
            ),
          ],
        ),
      ),
    );
  }

  // ── Formulaire inscription ────────────────────────
  Widget _buildRegisterForm() {
    final roles = [
      {'value': 'agriculteur',  'label': '🧑‍🌾 Agriculteur'},
      {'value': 'cooperative',  'label': '🤝 Coopérative'},
      {'value': 'conseiller',   'label': '👨‍💼 Conseiller'},
      {'value': 'chercheur',    'label': '🔬 Chercheur'},
    ];

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
      child: Form(
        key: _regKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Créer un compte 🌿',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800,
                  color: AppColors.gray900)),
            const SizedBox(height: 4),
            const Text('Rejoignez des milliers d\'agriculteurs',
              style: TextStyle(fontSize: 13, color: AppColors.gray500)),
            const SizedBox(height: 20),

            Row(children: [
              Expanded(child: SmartTextField(
                label: 'Prénom', hint: 'Jean', controller: _fnCtrl,
                validator: (v) => v!.isEmpty ? 'Requis' : null,
              )),
              const SizedBox(width: 12),
              Expanded(child: SmartTextField(
                label: 'Nom', hint: 'Diallo', controller: _lnCtrl,
                validator: (v) => v!.isEmpty ? 'Requis' : null,
              )),
            ]),
            const SizedBox(height: 14),

            SmartTextField(
              label: 'E-mail', hint: 'vous@exemple.com', prefixIcon: '✉️',
              controller: _regEmailCtrl,
              keyboardType: TextInputType.emailAddress,
              validator: (v) {
                if (v!.isEmpty) return 'E-mail requis';
                if (!v.contains('@')) return 'E-mail invalide';
                return null;
              },
            ),
            const SizedBox(height: 14),

            SmartTextField(
              label: 'Téléphone (optionnel)', hint: '+225 07 00 00 00 00',
              prefixIcon: '📞', controller: _phoneCtrl,
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 14),

            // Sélecteur de rôle avec grandes tuiles tactiles
            const Text('Vous êtes',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600,
                  color: AppColors.gray700)),
            const SizedBox(height: 8),
            GridView.count(
              crossAxisCount: 2, shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 10, mainAxisSpacing: 10,
              childAspectRatio: 2.8,
              children: roles.map((r) {
                final selected = _selectedRole == r['value'];
                return GestureDetector(
                  onTap: () => setState(() => _selectedRole = r['value']!),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 150),
                    decoration: BoxDecoration(
                      color: selected ? AppColors.green100 : AppColors.gray100,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: selected ? AppColors.green500 : AppColors.gray200,
                        width: selected ? 2 : 1,
                      ),
                    ),
                    child: Center(
                      child: Text(r['label']!,
                        style: TextStyle(
                          fontSize: 13, fontWeight: FontWeight.w600,
                          color: selected ? AppColors.green700 : AppColors.gray600,
                        ),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 14),

            SmartTextField(
              label: 'Mot de passe', hint: 'Min. 8 caractères', prefixIcon: '🔒',
              controller: _regPwdCtrl, obscure: !_showRegPwd,
              suffixWidget: IconButton(
                icon: Icon(_showRegPwd ? Icons.visibility_off : Icons.visibility,
                    color: AppColors.gray400),
                onPressed: () => setState(() => _showRegPwd = !_showRegPwd),
              ),
              validator: (v) {
                if (v!.isEmpty) return 'Mot de passe requis';
                if (v.length < 8) return 'Minimum 8 caractères';
                return null;
              },
            ),
            const SizedBox(height: 20),

            PrimaryButton(
              label: 'Créer mon compte',
              icon: '🌱',
              loading: _loading,
              onTap: _register,
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

extension on AppColors {
  static Color get gray600 => const Color(0xFF4B5563);
}

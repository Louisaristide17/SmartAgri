import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../services/api_service.dart';
import '../models/models.dart';
import '../widgets/common_widgets.dart';

class HomeScreen extends StatefulWidget {
  final VoidCallback onLogout;
  const HomeScreen({super.key, required this.onLogout});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _api = ApiService();
  UserModel? _user;
  List<ParcelleModel> _parcelles = [];
  List<PredictionModel> _predictions = [];
  MeteoModel? _meteo;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    setState(() => _loading = true);
    try {
      final userJson = await ApiService.getUser();
      if (userJson != null) _user = UserModel.fromJson(userJson);

      final results = await Future.wait([
        _api.getParcelles(),
        _api.getHistoriquePredictions(),
        _api.getMeteo('Dakar'),
      ]);

      setState(() {
        _parcelles   = (results[0] as List).map((e) => ParcelleModel.fromJson(e)).toList();
        _predictions = (results[1] as List).map((e) => PredictionModel.fromJson(e)).toList();
        _meteo       = MeteoModel.fromJson(results[2] as Map<String, dynamic>);
        _loading     = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  String _greeting() {
    final h = DateTime.now().hour;
    if (h < 12) return 'Bonjour';
    if (h < 18) return 'Bon après-midi';
    return 'Bonsoir';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.gray50,
      body: RefreshIndicator(
        onRefresh: _loadAll,
        color: AppColors.green500,
        child: CustomScrollView(
          slivers: [
            _buildAppBar(),
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 100),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  const SizedBox(height: 16),
                  _buildStats(),
                  const SizedBox(height: 20),
                  _buildQuickActions(context),
                  const SizedBox(height: 20),
                  _buildMeteoCard(),
                  const SizedBox(height: 20),
                  _buildParcellesSection(context),
                  const SizedBox(height: 20),
                  _buildPredictionsSection(),
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── AppBar dégradé ────────────────────────────────
  Widget _buildAppBar() {
    return SliverAppBar(
      expandedHeight: 170,
      pinned: true,
      backgroundColor: AppColors.green700,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: const BoxDecoration(gradient: AppColors.heroGradient),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(children: [
                        const Text('🌱', style: TextStyle(fontSize: 22)),
                        const SizedBox(width: 8),
                        const Text('SmartAgri',
                          style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800,
                              color: AppColors.white)),
                      ]),
                      Row(children: [
                        // Avatar
                        GestureDetector(
                          onTap: _showProfileSheet,
                          child: CircleAvatar(
                            radius: 20,
                            backgroundColor: AppColors.green300,
                            child: Text(
                              _user?.initials ?? 'U',
                              style: const TextStyle(
                                fontWeight: FontWeight.w800,
                                color: AppColors.green900,
                                fontSize: 14),
                            ),
                          ),
                        ),
                      ]),
                    ],
                  ),
                  const SizedBox(height: 16),
                  if (_user != null) ...[
                    Text('${_greeting()}, ${_user!.firstname} 👋',
                      style: const TextStyle(
                        fontSize: 22, fontWeight: FontWeight.w800,
                        color: AppColors.white)),
                    const SizedBox(height: 4),
                    Text(_formattedDate(),
                      style: TextStyle(
                        fontSize: 13,
                        color: Colors.white.withOpacity(0.75))),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  String _formattedDate() {
    final now = DateTime.now();
    const months = ['jan','fév','mar','avr','mai','juin','juil','aoû','sep','oct','nov','déc'];
    const days   = ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'];
    return '${days[now.weekday - 1]} ${now.day} ${months[now.month - 1]} ${now.year}';
  }

  // ── Stats ─────────────────────────────────────────
  Widget _buildStats() {
    final avgRendement = _predictions.isEmpty
        ? '–'
        : '${(_predictions.map((p) => p.rendementPredit).reduce((a, b) => a + b) / _predictions.length).toStringAsFixed(1)} t/ha';

    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.55,
      children: [
        _loading
            ? const SkeletonBox(width: double.infinity, height: 90, radius: 16)
            : StatCard(
                icon: '🗺️',
                value: '${_parcelles.length}',
                label: 'Parcelles actives',
                trend: _parcelles.isNotEmpty ? '${_parcelles.length} parcelle(s)' : 'Aucune',
                bgColor: AppColors.green100,
              ),
        _loading
            ? const SkeletonBox(width: double.infinity, height: 90, radius: 16)
            : StatCard(
                icon: '🌾',
                value: avgRendement,
                label: 'Rendement moyen',
                trend: '↑ En hausse',
                bgColor: AppColors.orangeBg,
              ),
        _loading
            ? const SkeletonBox(width: double.infinity, height: 90, radius: 16)
            : StatCard(
                icon: '🌡️',
                value: _meteo != null ? '${_meteo!.temperature}°C' : '–',
                label: 'Température Dakar',
                trend: _meteo?.description ?? '',
                bgColor: AppColors.blueBg,
              ),
        _loading
            ? const SkeletonBox(width: double.infinity, height: 90, radius: 16)
            : StatCard(
                icon: '🔮',
                value: '${_predictions.length}',
                label: 'Prédictions',
                bgColor: AppColors.purpleBg,
              ),
      ],
    );
  }

  // ── Actions rapides ───────────────────────────────
  Widget _buildQuickActions(BuildContext context) {
    final actions = [
      {'icon': '🗺️', 'label': 'Parcelles',  'index': 1},
      {'icon': '🔮', 'label': 'Prédire',    'index': 2},
      {'icon': '🌦️', 'label': 'Météo',      'index': 3},
      {'icon': '👵🏻', 'label': 'AgriBot',    'index': 4},
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SectionTitle(title: '⚡ Accès rapide'),
        const SizedBox(height: 12),
        Row(
          children: actions.map((a) {
            return Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: _QuickBtn(
                  icon: a['icon'] as String,
                  label: a['label'] as String,
                  onTap: () {
                    // Signaler à MainScreen de changer d'onglet
                    final nav = context.findAncestorStateOfType<MainScreenState>();
                    nav?.setTab(a['index'] as int);
                  },
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  // ── Météo carte ───────────────────────────────────
  Widget _buildMeteoCard() {
    if (_loading) {
      return const SkeletonBox(width: double.infinity, height: 100, radius: 16);
    }
    if (_meteo == null) return const SizedBox.shrink();

    return SmartCard(
      child: Row(
        children: [
          Text(_meteo!.emojiIcon, style: const TextStyle(fontSize: 48)),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_meteo!.ville,
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700,
                      color: AppColors.gray900)),
                Text(_meteo!.description,
                  style: const TextStyle(fontSize: 13, color: AppColors.gray500)),
                const SizedBox(height: 6),
                Row(children: [
                  _meteoDetail('💧', '${_meteo!.humidite}%'),
                  const SizedBox(width: 14),
                  _meteoDetail('🌬️', '${_meteo!.vent} km/h'),
                ]),
              ],
            ),
          ),
          Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
            Text('${_meteo!.temperature}°',
              style: const TextStyle(fontSize: 36, fontWeight: FontWeight.w800,
                  color: AppColors.green700)),
            Text('Ressenti ${_meteo!.ressenti}°',
              style: const TextStyle(fontSize: 11, color: AppColors.gray400)),
          ]),
        ],
      ),
    );
  }

  Widget _meteoDetail(String icon, String val) => Row(children: [
    Text(icon, style: const TextStyle(fontSize: 13)),
    const SizedBox(width: 4),
    Text(val, style: const TextStyle(fontSize: 12, color: AppColors.gray600)),
  ]);

  // ── Parcelles section ─────────────────────────────
  Widget _buildParcellesSection(BuildContext context) {
    return Column(
      children: [
        SectionTitle(
          title: '🗺️ Mes parcelles',
          action: 'Voir tout',
          onAction: () {
            final nav = context.findAncestorStateOfType<MainScreenState>();
            nav?.setTab(1);
          },
        ),
        const SizedBox(height: 12),
        if (_loading)
          ...List.generate(2, (_) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: SkeletonBox(width: double.infinity, height: 80, radius: 14),
          ))
        else if (_parcelles.isEmpty)
          EmptyState(
            icon: '🗺️', title: 'Aucune parcelle',
            subtitle: 'Ajoutez votre première parcelle agricole',
            buttonLabel: '+ Ajouter',
            onButton: () {
              final nav = context.findAncestorStateOfType<MainScreenState>();
              nav?.setTab(1);
            },
          )
        else
          ..._parcelles.take(3).map((p) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: _ParcelleRow(parcelle: p),
          )),
      ],
    );
  }

  // ── Prédictions récentes ──────────────────────────
  Widget _buildPredictionsSection() {
    if (_predictions.isEmpty) return const SizedBox.shrink();
    return Column(
      children: [
        const SectionTitle(title: '🔮 Prédictions récentes'),
        const SizedBox(height: 12),
        ..._predictions.take(3).map((p) => Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: SmartCard(
            padding: const EdgeInsets.all(14),
            child: Row(children: [
              Text(p.culture == 'mais' ? '🌽' : p.culture == 'riz' ? '🌾' : '🌱',
                style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 12),
              Expanded(child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(p.culture.substring(0,1).toUpperCase() + p.culture.substring(1),
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                  Text('${p.superficie} ha · ${p.typeSol}',
                    style: const TextStyle(fontSize: 12, color: AppColors.gray400)),
                ],
              )),
              Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                Text('${p.rendementPredit.toStringAsFixed(1)} t/ha',
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800,
                      color: AppColors.green700)),
                if (p.confiance != null)
                  Text('${p.confiance!.toStringAsFixed(0)}% fiable',
                    style: const TextStyle(fontSize: 11, color: AppColors.gray400)),
              ]),
            ]),
          ),
        )),
      ],
    );
  }

  // ── Profile bottom sheet ──────────────────────────
  void _showProfileSheet() {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(width: 40, height: 4,
              decoration: BoxDecoration(
                color: AppColors.gray300,
                borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 20),
            CircleAvatar(
              radius: 36, backgroundColor: AppColors.green100,
              child: Text(_user?.initials ?? 'U',
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800,
                    color: AppColors.green700))),
            const SizedBox(height: 12),
            Text(_user?.fullName ?? '',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700,
                  color: AppColors.gray900)),
            Text(_user?.email ?? '',
              style: const TextStyle(fontSize: 13, color: AppColors.gray500)),
            const SizedBox(height: 4),
            SmartBadge(label: _user?.role ?? '', color: AppColors.green100,
                textColor: AppColors.green700),
            const SizedBox(height: 24),
            const Divider(),
            ListTile(
              leading: const Text('🚪', style: TextStyle(fontSize: 22)),
              title: const Text('Se déconnecter',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600,
                    color: AppColors.red)),
              onTap: () async {
                Navigator.pop(context);
                await _api.logout();
                widget.onLogout();
              },
            ),
          ],
        ),
      ),
    );
  }
}

// ── Widget bouton action rapide ───────────────────────────────────
class _QuickBtn extends StatelessWidget {
  final String icon;
  final String label;
  final VoidCallback onTap;

  const _QuickBtn({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: AppColors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.gray200),
          boxShadow: [BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 6, offset: const Offset(0, 2))],
        ),
        child: Column(children: [
          Text(icon, style: const TextStyle(fontSize: 26)),
          const SizedBox(height: 6),
          Text(label,
            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600,
                color: AppColors.gray700),
            textAlign: TextAlign.center),
        ]),
      ),
    );
  }
}

// ── Ligne de parcelle ─────────────────────────────────────────────
class _ParcelleRow extends StatelessWidget {
  final ParcelleModel parcelle;
  const _ParcelleRow({required this.parcelle});

  @override
  Widget build(BuildContext context) {
    return SmartCard(
      padding: const EdgeInsets.all(14),
      child: Row(children: [
        Container(
          width: 46, height: 46,
          decoration: BoxDecoration(
            color: AppColors.green100, borderRadius: BorderRadius.circular(12)),
          child: Center(
            child: Text(parcelle.cultureIcon, style: const TextStyle(fontSize: 22))),
        ),
        const SizedBox(width: 12),
        Expanded(child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(parcelle.nom,
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700,
                  color: AppColors.gray900)),
            const SizedBox(height: 2),
            Text('${parcelle.superficie} ha · ${parcelle.typeSol} · ${parcelle.ville ?? "–"}',
              style: const TextStyle(fontSize: 12, color: AppColors.gray400)),
          ],
        )),
        SmartBadge(
          label: parcelle.statutLabel,
          color: parcelle.statut == 'active' ? AppColors.green100
              : parcelle.statut == 'recoltee' ? AppColors.blueBg
              : AppColors.yellowBg,
          textColor: parcelle.statut == 'active' ? AppColors.green700
              : parcelle.statut == 'recoltee' ? AppColors.blue
              : AppColors.yellow,
        ),
      ]),
    );
  }
}

extension on AppColors {
  static const Color gray600 = Color(0xFF4B5563);
}

// ── Exposition de l'état de MainScreen ───────────────────────────
// (déclaré ici pour éviter les dépendances circulaires)
abstract class MainScreenState extends State<StatefulWidget> {
  void setTab(int index);
}

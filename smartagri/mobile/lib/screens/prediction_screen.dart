import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../services/api_service.dart';
import '../models/models.dart';
import '../widgets/common_widgets.dart';

class PredictionScreen extends StatefulWidget {
  const PredictionScreen({super.key});

  @override
  State<PredictionScreen> createState() => _PredictionScreenState();
}

class _PredictionScreenState extends State<PredictionScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;
  final _api = ApiService();

  // ── Valeurs des sliders ──
  String  _culture   = 'mais';
  String  _sol       = 'sableux';
  double  _superficie = 1.0;
  double  _pluv      = 450;
  double  _temp      = 26;
  double  _engrais   = 50;

  PredictionModel? _result;
  bool _loading     = false;
  bool _loadingHist = true;
  List<PredictionModel> _historique = [];

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 2, vsync: this);
    _loadHistorique();
    _loadMeteoTemp();
  }

  @override
  void dispose() { _tabs.dispose(); super.dispose(); }

  Future<void> _loadMeteoTemp() async {
    try {
      final m = await _api.getMeteo('Dakar');
      final meteo = MeteoModel.fromJson(m);
      setState(() => _temp = meteo.temperature.clamp(10, 45).toDouble());
    } catch (_) {}
  }

  Future<void> _loadHistorique() async {
    setState(() => _loadingHist = true);
    try {
      final list = await _api.getHistoriquePredictions();
      setState(() {
        _historique = list.map((e) => PredictionModel.fromJson(e)).toList();
        _loadingHist = false;
      });
    } catch (_) {
      setState(() => _loadingHist = false);
    }
  }

  Future<void> _predict() async {
    setState(() => _loading = true);
    try {
      final data = await _api.predict({
        'culture':      _culture,
        'type_sol':     _sol,
        'superficie':   _superficie,
        'pluviometrie': _pluv,
        'temperature':  _temp,
        'engrais_kg':   _engrais,
      });
      setState(() {
        _result = PredictionModel.fromJson(data);
        _loading = false;
      });
      // Passer à l'onglet résultat
      _tabs.animateTo(0);
      _loadHistorique();
      showSnack(context, 'Prédiction calculée avec succès !');
    } on ApiException catch (e) {
      setState(() => _loading = false);
      showSnack(context, e.message, error: true);
    } catch (e) {
      setState(() => _loading = false);
      showSnack(context, 'Impossible de joindre le serveur.', error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.gray50,
      appBar: AppBar(
        title: const Text('🔮 Prédiction IA'),
        backgroundColor: AppColors.white,
        bottom: TabBar(
          controller: _tabs,
          labelColor: AppColors.green700,
          unselectedLabelColor: AppColors.gray400,
          indicatorColor: AppColors.green500,
          indicatorWeight: 3,
          tabs: const [
            Tab(text: 'Résultat'),
            Tab(text: 'Paramètres'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabs,
        children: [_buildResultTab(), _buildFormTab()],
      ),
    );
  }

  // ══ Onglet RÉSULTAT ═══════════════════════════════
  Widget _buildResultTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 100),
      child: Column(
        children: [
          // Résultat principal
          _result == null ? _buildEmptyResult() : _buildResult(),
          const SizedBox(height: 24),

          // Historique
          SectionTitle(
            title: '🕐 Mes prédictions',
            action: 'Rafraîchir',
            onAction: _loadHistorique,
          ),
          const SizedBox(height: 12),
          _loadingHist
              ? Column(children: List.generate(3, (_) => Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: SkeletonBox(width: double.infinity, height: 70, radius: 12),
                )))
              : _historique.isEmpty
                  ? const EmptyState(
                      icon: '🔮',
                      title: 'Aucune prédiction',
                      subtitle: 'Allez dans "Paramètres" pour lancer votre première prédiction.',
                    )
                  : Column(children: _historique.take(8).map((p) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: _HistoriqueRow(prediction: p),
                    )).toList()),
        ],
      ),
    );
  }

  Widget _buildEmptyResult() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(28),
      decoration: BoxDecoration(
        gradient: AppColors.heroGradient,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(children: [
        const Text('🔮', style: TextStyle(fontSize: 56)),
        const SizedBox(height: 12),
        const Text('Prêt à prédire',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800,
              color: AppColors.white)),
        const SizedBox(height: 8),
        Text('Allez dans "Paramètres", ajustez les curseurs\npuis appuyez sur Prédire.',
          style: TextStyle(fontSize: 13, color: Colors.white.withOpacity(0.75),
              height: 1.5),
          textAlign: TextAlign.center),
        const SizedBox(height: 20),
        OutlinedButton.icon(
          onPressed: () => _tabs.animateTo(1),
          icon: const Text('⚙️'),
          label: const Text('Configurer'),
          style: OutlinedButton.styleFrom(
            foregroundColor: AppColors.white,
            side: const BorderSide(color: AppColors.white, width: 1.5),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
      ]),
    );
  }

  Widget _buildResult() {
    final r = _result!;
    final conf = r.confiance ?? 80;
    final icon = r.culture == 'mais' ? '🌽' : r.culture == 'riz' ? '🌾'
        : r.culture == 'arachide' ? '🥜' : '🌱';

    // Conseils dynamiques
    final tips = <String>[];
    if (_pluv < 400) tips.add('💧 Pluviométrie faible — envisagez l\'irrigation');
    if (_pluv > 1200) tips.add('🌧️ Excès de pluie — vérifiez le drainage');
    if (_temp > 35) tips.add('🌡️ Trop chaud — arrosez tôt le matin');
    if (_engrais < 20) tips.add('🌿 Augmentez les engrais pour plus de rendement');
    if (r.rendementPredit > 4) tips.add('✅ Excellent rendement prévu !');
    if (r.rendementPredit < 1.5) tips.add('⚠️ Rendement faible — consultez AgriBot');

    return Column(children: [
      // Card résultat principal
      Container(
        width: double.infinity,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          gradient: AppColors.heroGradient,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Column(children: [
          Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            Text(icon, style: const TextStyle(fontSize: 32)),
            const SizedBox(width: 10),
            Text(r.culture[0].toUpperCase() + r.culture.substring(1),
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600,
                  color: AppColors.white)),
          ]),
          const SizedBox(height: 16),
          const Text('Rendement prédit',
            style: TextStyle(fontSize: 13, color: Colors.white70)),
          const SizedBox(height: 4),
          Text('${r.rendementPredit.toStringAsFixed(2)}',
            style: const TextStyle(fontSize: 56, fontWeight: FontWeight.w900,
                color: AppColors.white, height: 1)),
          const Text('tonnes / hectare',
            style: TextStyle(fontSize: 14, color: Colors.white70)),
          const SizedBox(height: 20),

          // Barre de confiance
          Row(children: [
            Expanded(child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Fiabilité : ${conf.toStringAsFixed(0)}%',
                  style: const TextStyle(fontSize: 13, color: Colors.white70)),
                const SizedBox(height: 6),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: conf / 100,
                    backgroundColor: Colors.white24,
                    valueColor: const AlwaysStoppedAnimation(AppColors.green300),
                    minHeight: 8,
                  ),
                ),
              ],
            )),
          ]),
          const SizedBox(height: 16),

          // Stats
          Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
            _rStat('💧', '${r.pluviometrie.toInt()} mm'),
            _rStat('🌡️', '${r.temperature}°C'),
            _rStat('🌿', '${r.engraisKg.toInt()} kg/ha'),
            _rStat('📐', '${r.superficie} ha'),
          ]),
        ]),
      ),

      // Conseils
      if (tips.isNotEmpty) ...[
        const SizedBox(height: 16),
        SmartCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('💡 Conseils personnalisés',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700,
                    color: AppColors.gray900)),
              const SizedBox(height: 10),
              ...tips.map((t) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(children: [
                  const SizedBox(width: 4),
                  Expanded(child: Text(t,
                    style: const TextStyle(fontSize: 13, color: AppColors.gray700,
                        height: 1.4))),
                ]),
              )),
            ],
          ),
        ),
      ],

      const SizedBox(height: 16),
      OutlinedButton.icon(
        onPressed: () => _tabs.animateTo(1),
        icon: const Text('🔄'),
        label: const Text('Modifier les paramètres'),
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(double.infinity, 48)),
      ),
    ]);
  }

  Widget _rStat(String icon, String val) => Column(children: [
    Text(icon, style: const TextStyle(fontSize: 16)),
    const SizedBox(height: 4),
    Text(val, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700,
        color: Colors.white70)),
  ]);

  // ══ Onglet PARAMÈTRES ════════════════════════════
  Widget _buildFormTab() {
    final cultures = {
      'mais': '🌽 Maïs', 'riz': '🌾 Riz', 'arachide': '🥜 Arachide',
      'sorgho': '🌿 Sorgho', 'mil': '🌿 Mil',
      'coton': '☁️ Coton', 'manioc': '🥔 Manioc',
    };
    final sols = {
      'sableux': 'Sableux', 'argileux': 'Argileux',
      'limoneux': 'Limoneux', 'lateritique': 'Latéritique',
    };

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 120),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Info météo contextuelle
          _MeteoContext(temp: _temp),
          const SizedBox(height: 20),

          SmartCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('🌱 Culture et sol',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700,
                      color: AppColors.gray900)),
                const SizedBox(height: 16),

                // Culture grid
                GridView.count(
                  crossAxisCount: 3, shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisSpacing: 8, mainAxisSpacing: 8,
                  childAspectRatio: 2,
                  children: cultures.entries.map((e) {
                    final sel = _culture == e.key;
                    return GestureDetector(
                      onTap: () => setState(() => _culture = e.key),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 150),
                        decoration: BoxDecoration(
                          color: sel ? AppColors.green100 : AppColors.gray100,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(
                            color: sel ? AppColors.green500 : AppColors.gray200,
                            width: sel ? 2 : 1,
                          ),
                        ),
                        child: Center(child: Text(e.value,
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                              color: sel ? AppColors.green700 : AppColors.gray500),
                          textAlign: TextAlign.center)),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 16),

                // Sol
                const Text('Type de sol',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600,
                      color: AppColors.gray700)),
                const SizedBox(height: 8),
                Row(children: sols.entries.map((e) {
                  final sel = _sol == e.key;
                  return Expanded(child: Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: GestureDetector(
                      onTap: () => setState(() => _sol = e.key),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 150),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                        decoration: BoxDecoration(
                          color: sel ? AppColors.green100 : AppColors.gray100,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(
                            color: sel ? AppColors.green500 : AppColors.gray200,
                            width: sel ? 2 : 1,
                          ),
                        ),
                        child: Center(child: Text(e.value,
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600,
                              color: sel ? AppColors.green700 : AppColors.gray500),
                          textAlign: TextAlign.center)),
                      ),
                    ),
                  ));
                }).toList()),

                const SizedBox(height: 16),
                // Superficie
                _SliderField(
                  label: '📐 Superficie',
                  value: _superficie,
                  min: 0.1, max: 20, divisions: 199,
                  unit: 'ha',
                  minLabel: '0.1 ha',
                  maxLabel: '20 ha',
                  onChanged: (v) => setState(() => _superficie = v),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          SmartCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('🌦️ Conditions climatiques',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700,
                      color: AppColors.gray900)),
                const SizedBox(height: 16),
                _SliderField(
                  label: '💧 Pluviométrie',
                  value: _pluv,
                  min: 0, max: 2000, divisions: 200,
                  unit: 'mm',
                  minLabel: 'Sec',
                  maxLabel: 'Très humide',
                  onChanged: (v) => setState(() => _pluv = v),
                ),
                const SizedBox(height: 16),
                _SliderField(
                  label: '🌡️ Température',
                  value: _temp,
                  min: 10, max: 45, divisions: 70,
                  unit: '°C',
                  minLabel: 'Frais',
                  maxLabel: 'Très chaud',
                  onChanged: (v) => setState(() => _temp = v),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          SmartCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('🌿 Intrants agricoles',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700,
                      color: AppColors.gray900)),
                const SizedBox(height: 16),
                _SliderField(
                  label: '🌿 Engrais',
                  value: _engrais,
                  min: 0, max: 200, divisions: 40,
                  unit: 'kg/ha',
                  minLabel: 'Sans engrais',
                  maxLabel: 'Intensif',
                  onChanged: (v) => setState(() => _engrais = v),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          PrimaryButton(
            label: 'Lancer la prédiction IA',
            icon: '🔮',
            loading: _loading,
            onTap: _predict,
          ),
        ],
      ),
    );
  }
}

// ── Contexte météo ────────────────────────────────────────────────
class _MeteoContext extends StatelessWidget {
  final double temp;
  const _MeteoContext({required this.temp});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.blueBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.blue.withOpacity(0.2)),
      ),
      child: Row(children: [
        const Text('🌤️', style: TextStyle(fontSize: 24)),
        const SizedBox(width: 12),
        Expanded(child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Météo actuelle prise en compte',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700,
                  color: Color(0xFF1E40AF))),
            Text('Température réelle Dakar : ${temp.toStringAsFixed(0)}°C pré-remplie',
              style: const TextStyle(fontSize: 12, color: Color(0xFF3B82F6))),
          ],
        )),
      ]),
    );
  }
}

// ── Slider avec affichage de valeur ──────────────────────────────
class _SliderField extends StatelessWidget {
  final String label;
  final double value;
  final double min, max;
  final int divisions;
  final String unit;
  final String minLabel, maxLabel;
  final ValueChanged<double> onChanged;

  const _SliderField({
    required this.label,
    required this.value,
    required this.min,
    required this.max,
    required this.divisions,
    required this.unit,
    required this.minLabel,
    required this.maxLabel,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text(label,
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600,
                color: AppColors.gray700)),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            decoration: BoxDecoration(
              color: AppColors.green100,
              borderRadius: BorderRadius.circular(999),
            ),
            child: Text(
              unit == 'ha'
                  ? '${value.toStringAsFixed(1)} $unit'
                  : '${value.toStringAsFixed(0)} $unit',
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800,
                  color: AppColors.green700)),
          ),
        ]),
        Slider(value: value, min: min, max: max,
          divisions: divisions, onChanged: onChanged),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Text(minLabel,
              style: const TextStyle(fontSize: 10, color: AppColors.gray400)),
            Text(maxLabel,
              style: const TextStyle(fontSize: 10, color: AppColors.gray400)),
          ]),
        ),
      ],
    );
  }
}

// ── Ligne historique ──────────────────────────────────────────────
class _HistoriqueRow extends StatelessWidget {
  final PredictionModel prediction;
  const _HistoriqueRow({required this.prediction});

  @override
  Widget build(BuildContext context) {
    final p = prediction;
    final icon = p.culture == 'mais' ? '🌽' : p.culture == 'riz' ? '🌾'
        : p.culture == 'arachide' ? '🥜' : '🌱';
    return SmartCard(
      padding: const EdgeInsets.all(12),
      child: Row(children: [
        Text(icon, style: const TextStyle(fontSize: 24)),
        const SizedBox(width: 12),
        Expanded(child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(p.culture[0].toUpperCase() + p.culture.substring(1),
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700,
                  color: AppColors.gray900)),
            Text('${p.superficie} ha · ${p.typeSol} · ${p.pluviometrie.toInt()}mm · ${p.temperature}°C',
              style: const TextStyle(fontSize: 11, color: AppColors.gray400)),
          ],
        )),
        Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Text('${p.rendementPredit.toStringAsFixed(2)} t/ha',
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800,
                color: AppColors.green700)),
          if (p.confiance != null)
            Text('${p.confiance!.toStringAsFixed(0)}%',
              style: const TextStyle(fontSize: 11, color: AppColors.gray400)),
        ]),
      ]),
    );
  }
}

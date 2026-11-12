import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../services/api_service.dart';
import '../models/models.dart';
import '../widgets/common_widgets.dart';

class MeteoScreen extends StatefulWidget {
  const MeteoScreen({super.key});

  @override
  State<MeteoScreen> createState() => _MeteoScreenState();
}

class _MeteoScreenState extends State<MeteoScreen> {
  final _api = ApiService();
  final _searchCtrl = TextEditingController();
  String _ville = 'Dakar';
  MeteoModel? _meteo;
  List<PrevisionJour> _previsions = [];
  bool _loading = true;

  final List<String> _villes = [
    'Abidjan', 'Yamoussoukro', 'Bouaké', 'Daloa', 'San-Pédro',
    'Korhogo', 'Man', 'Gagnoa',
  ];

  @override
  void initState() { super.initState(); _load('Abidjan'); }

  @override
  void dispose() { _searchCtrl.dispose(); super.dispose(); }

  Future<void> _load(String ville) async {
    setState(() { _loading = true; _ville = ville; });
    try {
      final results = await Future.wait([
        _api.getMeteo(ville),
        _api.getPrevisions(ville),
      ]);
      final meteoData = results[0] as Map<String, dynamic>;
      final prevData  = results[1] as Map<String, dynamic>;

      setState(() {
        _meteo = MeteoModel.fromJson(meteoData);
        _previsions = (prevData['previsions'] as List)
            .map((e) => PrevisionJour.fromJson(e))
            .toList();
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
      if (mounted) showSnack(context, 'Météo indisponible pour $ville', error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.gray50,
      body: RefreshIndicator(
        onRefresh: () => _load(_ville),
        color: AppColors.green500,
        child: CustomScrollView(
          slivers: [
            _buildAppBar(),
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 100),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  const SizedBox(height: 16),
                  _buildVillesRapides(),
                  const SizedBox(height: 16),
                  _buildCurrentCard(),
                  const SizedBox(height: 20),
                  const SectionTitle(title: '📅 Prévisions 6 jours'),
                  const SizedBox(height: 12),
                  _buildPrevisions(),
                  const SizedBox(height: 20),
                  _buildAgroConseils(),
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── AppBar avec recherche ─────────────────────────
  Widget _buildAppBar() {
    return SliverAppBar(
      pinned: true,
      backgroundColor: AppColors.green700,
      expandedHeight: 80,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          color: AppColors.green700,
          alignment: Alignment.bottomCenter,
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
          child: SafeArea(
            child: Row(children: [
              const Text('🌦️', style: TextStyle(fontSize: 22)),
              const SizedBox(width: 8),
              const Text('Météo Agricole',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800,
                    color: AppColors.white)),
              const Spacer(),
              // Recherche
              GestureDetector(
                onTap: _showSearchSheet,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.white24,
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Row(children: [
                    const Icon(Icons.search, size: 16, color: AppColors.white),
                    const SizedBox(width: 6),
                    Text(_ville,
                      style: const TextStyle(fontSize: 13, color: AppColors.white,
                          fontWeight: FontWeight.w600)),
                  ]),
                ),
              ),
            ]),
          ),
        ),
      ),
    );
  }

  // ── Villes rapides ────────────────────────────────
  Widget _buildVillesRapides() {
    return SizedBox(
      height: 40,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: _villes.length,
        itemBuilder: (_, i) {
          final v = _villes[i];
          final sel = v == _ville;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: GestureDetector(
              onTap: () => _load(v),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 150),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                decoration: BoxDecoration(
                  color: sel ? AppColors.green500 : AppColors.white,
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(
                    color: sel ? AppColors.green500 : AppColors.gray300),
                  boxShadow: sel ? [BoxShadow(
                    color: AppColors.green500.withOpacity(0.3),
                    blurRadius: 6)] : null,
                ),
                child: Text(v,
                  style: TextStyle(
                    fontSize: 13, fontWeight: FontWeight.w600,
                    color: sel ? AppColors.white : AppColors.gray600)),
              ),
            ),
          );
        },
      ),
    );
  }

  // ── Météo actuelle ────────────────────────────────
  Widget _buildCurrentCard() {
    if (_loading) {
      return const SkeletonBox(width: double.infinity, height: 180, radius: 20);
    }
    if (_meteo == null) return const SizedBox.shrink();
    final m = _meteo!;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: AppColors.heroGradient,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(children: [
        // Ville + heure
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(m.ville,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800,
                  color: AppColors.white)),
            Text(m.description,
              style: TextStyle(fontSize: 13, color: Colors.white.withOpacity(0.75))),
          ]),
          Text(m.emojiIcon, style: const TextStyle(fontSize: 48)),
        ]),
        const SizedBox(height: 20),

        // Température grande
        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          Text('${m.temperature.toStringAsFixed(1)}°',
            style: const TextStyle(fontSize: 72, fontWeight: FontWeight.w900,
                color: AppColors.white, height: 1)),
        ]),
        Text('Ressenti ${m.ressenti.toStringAsFixed(0)}°C',
          style: TextStyle(fontSize: 13, color: Colors.white.withOpacity(0.7))),
        const SizedBox(height: 20),

        // Détails sur 4 colonnes
        Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
          _detail('💧', 'Humidité', '${m.humidite}%'),
          _detail('🌬️', 'Vent', '${m.vent.toStringAsFixed(0)} km/h'),
          _detail('📊', 'Pression', '${m.pression} hPa'),
          _detail('🌡️', 'Ressenti', '${m.ressenti.toStringAsFixed(0)}°C'),
        ]),
      ]),
    );
  }

  Widget _detail(String icon, String label, String val) => Column(children: [
    Text(icon, style: const TextStyle(fontSize: 18)),
    const SizedBox(height: 4),
    Text(val, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700,
        color: AppColors.white)),
    Text(label, style: TextStyle(fontSize: 10,
        color: Colors.white.withOpacity(0.65))),
  ]);

  // ── Prévisions ────────────────────────────────────
  Widget _buildPrevisions() {
    if (_loading) {
      return SizedBox(
        height: 120,
        child: ListView.builder(
          scrollDirection: Axis.horizontal,
          itemCount: 6,
          itemBuilder: (_, __) => Padding(
            padding: const EdgeInsets.only(right: 10),
            child: SkeletonBox(width: 80, height: 110, radius: 14),
          ),
        ),
      );
    }

    return SizedBox(
      height: 130,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: _previsions.length,
        itemBuilder: (_, i) {
          final p = _previsions[i];
          final isToday = i == 0;
          return Padding(
            padding: const EdgeInsets.only(right: 10),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: 85,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: isToday ? AppColors.green500 : AppColors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: isToday ? AppColors.green500 : AppColors.gray200),
                boxShadow: [BoxShadow(
                  color: Colors.black.withOpacity(0.06),
                  blurRadius: 6, offset: const Offset(0, 2))],
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  Text(p.label,
                    style: TextStyle(
                      fontSize: 11, fontWeight: FontWeight.w700,
                      color: isToday ? AppColors.white : AppColors.gray500)),
                  Text(p.emojiIcon, style: const TextStyle(fontSize: 24)),
                  Text('${p.temp.toStringAsFixed(0)}°',
                    style: TextStyle(
                      fontSize: 18, fontWeight: FontWeight.w800,
                      color: isToday ? AppColors.white : AppColors.gray900)),
                  Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                    Text('💧', style: const TextStyle(fontSize: 10)),
                    const SizedBox(width: 2),
                    Text('${p.pluie.toStringAsFixed(0)}mm',
                      style: TextStyle(fontSize: 10,
                          color: isToday ? Colors.white70 : AppColors.blue)),
                  ]),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  // ── Conseils agronomiques ─────────────────────────
  Widget _buildAgroConseils() {
    if (_meteo == null) return const SizedBox.shrink();
    final m = _meteo!;

    final conseils = <_AgroConseil>[];

    if (m.temperature > 35) {
      conseils.add(_AgroConseil('🌡️', 'Chaleur intense',
          'Arrosez tôt le matin ou en soirée. Évitez les travaux en plein soleil entre 11h et 16h.'));
    } else if (m.temperature < 20) {
      conseils.add(_AgroConseil('❄️', 'Températures fraîches',
          'Couvrez les jeunes plants sensibles. Reportez les semis de cultures tropicales.'));
    } else {
      conseils.add(_AgroConseil('🌡️', 'Température favorable',
          'Conditions thermiques idéales pour la croissance de la plupart des cultures.'));
    }

    if (m.humidite > 75) {
      conseils.add(_AgroConseil('🦠', 'Humidité élevée (${m.humidite}%)',
          'Risque de maladies fongiques. Surveillez vos plants et limitez les irrigations.'));
    } else if (m.humidite < 35) {
      conseils.add(_AgroConseil('🏜️', 'Air très sec (${m.humidite}%)',
          'Paillez vos parcelles pour limiter l\'évapotranspiration. Irriguez régulièrement.'));
    } else {
      conseils.add(_AgroConseil('💚', 'Humidité correcte',
          'Taux d\'humidité satisfaisant (${m.humidite}%). Conditions favorables aux cultures.'));
    }

    if (m.vent > 25) {
      conseils.add(_AgroConseil('🌬️', 'Vents forts (${m.vent.toStringAsFixed(0)} km/h)',
          'Évitez les traitements phytosanitaires. Protégez les jeunes plants.'));
    } else {
      conseils.add(_AgroConseil('🌬️', 'Vent modéré (${m.vent.toStringAsFixed(0)} km/h)',
          'Bonnes conditions pour les traitements foliaires et les pulvérisations.'));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SectionTitle(title: '🌱 Conseils agronomiques du jour'),
        const SizedBox(height: 12),
        ...conseils.map((c) => Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: SmartCard(
            child: Row(children: [
              Container(
                width: 48, height: 48,
                decoration: BoxDecoration(
                  color: AppColors.green50,
                  borderRadius: BorderRadius.circular(12)),
                child: Center(child: Text(c.icon,
                    style: const TextStyle(fontSize: 24))),
              ),
              const SizedBox(width: 14),
              Expanded(child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(c.title,
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700,
                        color: AppColors.gray900)),
                  const SizedBox(height: 4),
                  Text(c.text,
                    style: const TextStyle(fontSize: 12, color: AppColors.gray500,
                        height: 1.5)),
                ],
              )),
            ]),
          ),
        )),
      ],
    );
  }

  // ── Bottom sheet recherche ────────────────────────
  void _showSearchSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) => Padding(
        padding: EdgeInsets.fromLTRB(20, 16, 20,
            MediaQuery.of(context).viewInsets.bottom + 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(width: 40, height: 4,
              decoration: BoxDecoration(color: AppColors.gray300,
                  borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 16),
            const Text('Rechercher une ville',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 16),
            TextField(
              controller: _searchCtrl,
              autofocus: true,
              decoration: const InputDecoration(
                hintText: 'Ex: Bondoukou, Divo, Abengourou…',
                prefixIcon: Icon(Icons.search)),
              onSubmitted: (v) {
                if (v.trim().isNotEmpty) {
                  Navigator.pop(context);
                  _load(v.trim());
                }
              },
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  if (_searchCtrl.text.trim().isNotEmpty) {
                    Navigator.pop(context);
                    _load(_searchCtrl.text.trim());
                    _searchCtrl.clear();
                  }
                },
                child: const Text('Rechercher'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AgroConseil {
  final String icon, title, text;
  _AgroConseil(this.icon, this.title, this.text);
}

extension on AppColors {
  static const Color gray600 = Color(0xFF4B5563);
}

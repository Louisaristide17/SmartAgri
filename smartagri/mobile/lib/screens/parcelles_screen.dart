import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../services/api_service.dart';
import '../models/models.dart';
import '../widgets/common_widgets.dart';

class ParcellesScreen extends StatefulWidget {
  const ParcellesScreen({super.key});

  @override
  State<ParcellesScreen> createState() => _ParcellesScreenState();
}

class _ParcellesScreenState extends State<ParcellesScreen> {
  final _api = ApiService();
  List<ParcelleModel> _parcelles = [];
  bool _loading = true;
  String _search = '';
  String _filter = 'all';

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final list = await _api.getParcelles();
      setState(() {
        _parcelles = list.map((e) => ParcelleModel.fromJson(e)).toList();
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
      if (mounted) showSnack(context, 'Erreur de chargement', error: true);
    }
  }

  List<ParcelleModel> get _filtered {
    var list = _parcelles;
    if (_filter != 'all') {
      list = list.where((p) => p.statut == _filter || p.culture == _filter).toList();
    }
    if (_search.isNotEmpty) {
      list = list.where((p) =>
        p.nom.toLowerCase().contains(_search.toLowerCase()) ||
        p.culture.contains(_search.toLowerCase()) ||
        (p.ville ?? '').toLowerCase().contains(_search.toLowerCase())
      ).toList();
    }
    return list;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.gray50,
      appBar: AppBar(
        title: const Text('🗺️ Mes Parcelles'),
        backgroundColor: AppColors.white,
        actions: [
          TextButton.icon(
            icon: const Text('＋', style: TextStyle(fontSize: 18)),
            label: const Text('Ajouter'),
            style: TextButton.styleFrom(foregroundColor: AppColors.green500),
            onPressed: () => _showForm(context),
          ),
        ],
      ),
      body: Column(
        children: [
          // ── Barre de recherche ──
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              decoration: InputDecoration(
                hintText: 'Rechercher une parcelle…',
                prefixIcon: const Icon(Icons.search, color: AppColors.gray400),
                filled: true,
                fillColor: AppColors.white,
                contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: AppColors.gray200),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: AppColors.gray200),
                ),
              ),
              onChanged: (v) => setState(() => _search = v),
            ),
          ),

          // ── Filtres pills ──
          SizedBox(
            height: 44,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              children: [
                _FilterChip('Toutes',    'all'),
                _FilterChip('Actives',   'active'),
                _FilterChip('🌽 Maïs',  'mais'),
                _FilterChip('🌾 Riz',   'riz'),
                _FilterChip('🥜 Arachide','arachide'),
                _FilterChip('🌿 Mil',   'mil'),
              ].map((f) => Padding(
                padding: const EdgeInsets.only(right: 8),
                child: FilterChip(
                  label: Text(f.label),
                  selected: _filter == f.value,
                  onSelected: (_) => setState(() => _filter = f.value),
                  backgroundColor: AppColors.white,
                  selectedColor: AppColors.green100,
                  checkmarkColor: AppColors.green700,
                  labelStyle: TextStyle(
                    fontSize: 13, fontWeight: FontWeight.w600,
                    color: _filter == f.value ? AppColors.green700 : AppColors.gray500,
                  ),
                  side: BorderSide(
                    color: _filter == f.value ? AppColors.green500 : AppColors.gray200),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(999)),
                ),
              )).toList(),
            ),
          ),

          // ── Compteur ──
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
            child: Row(children: [
              Text('${_filtered.length} parcelle(s)',
                style: const TextStyle(fontSize: 13, color: AppColors.gray400,
                    fontWeight: FontWeight.w500)),
            ]),
          ),

          // ── Liste ──
          Expanded(
            child: _loading
                ? ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: 4,
                    itemBuilder: (_, __) => Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: SkeletonBox(width: double.infinity, height: 110, radius: 16),
                    ),
                  )
                : _filtered.isEmpty
                    ? EmptyState(
                        icon: '🗺️', title: 'Aucune parcelle',
                        subtitle: 'Appuyez sur "Ajouter" pour créer votre première parcelle.',
                        buttonLabel: '+ Ajouter une parcelle',
                        onButton: () => _showForm(context),
                      )
                    : RefreshIndicator(
                        onRefresh: _load,
                        color: AppColors.green500,
                        child: ListView.builder(
                          padding: const EdgeInsets.fromLTRB(16, 4, 16, 100),
                          itemCount: _filtered.length,
                          itemBuilder: (_, i) => Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: _ParcelleCard(
                              parcelle: _filtered[i],
                              onEdit:   () => _showForm(context, parcelle: _filtered[i]),
                              onDelete: () => _confirmDelete(context, _filtered[i]),
                              onPredict: () => _goPredict(_filtered[i]),
                            ),
                          ),
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  // ── Navigation vers prédiction ────────────────────
  void _goPredict(ParcelleModel p) {
    // Passer à l'onglet Prédiction avec les données pré-remplies
    final nav = context.findAncestorStateOfType<MainScreenState>();
    nav?.setTab(2);
  }

  // ── Confirmation suppression ──────────────────────
  Future<void> _confirmDelete(BuildContext context, ParcelleModel p) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('⚠️ Supprimer', style: TextStyle(fontSize: 18)),
        content: Text('Supprimer la parcelle "${p.nom}" ?\nCette action est irréversible.',
          style: const TextStyle(fontSize: 14, height: 1.5)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false),
            child: const Text('Annuler')),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.red, minimumSize: Size.zero,
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10)),
            child: const Text('Supprimer')),
        ],
      ),
    );
    if (ok == true) {
      try {
        await _api.deleteParcelle(p.id);
        showSnack(context, 'Parcelle supprimée.');
        _load();
      } catch (e) {
        showSnack(context, 'Erreur : $e', error: true);
      }
    }
  }

  // ── Formulaire ajouter/modifier ───────────────────
  void _showForm(BuildContext context, {ParcelleModel? parcelle}) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _ParcelleForm(
        parcelle: parcelle,
        onSave: (data) async {
          try {
            if (parcelle != null) {
              await _api.updateParcelle(parcelle.id, data);
              showSnack(context, 'Parcelle modifiée !');
            } else {
              await _api.createParcelle(data);
              showSnack(context, 'Parcelle ajoutée !');
            }
            _load();
          } catch (e) {
            showSnack(context, 'Erreur : $e', error: true);
          }
        },
      ),
    );
  }
}

// ── Chip filtre (helper struct) ───────────────────────────────────
class _FilterChip { final String label; final String value;
  const _FilterChip(this.label, this.value); }

// ── Carte parcelle ────────────────────────────────────────────────
class _ParcelleCard extends StatelessWidget {
  final ParcelleModel parcelle;
  final VoidCallback onEdit;
  final VoidCallback onDelete;
  final VoidCallback onPredict;

  const _ParcelleCard({
    required this.parcelle,
    required this.onEdit,
    required this.onDelete,
    required this.onPredict,
  });

  @override
  Widget build(BuildContext context) {
    final statBg = parcelle.statut == 'active' ? AppColors.green100
        : parcelle.statut == 'recoltee' ? AppColors.blueBg : AppColors.yellowBg;
    final statColor = parcelle.statut == 'active' ? AppColors.green700
        : parcelle.statut == 'recoltee' ? AppColors.blue : AppColors.yellow;

    return SmartCard(
      child: Column(
        children: [
          // ── En-tête ──
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 52, height: 52,
                decoration: BoxDecoration(
                  color: AppColors.green50,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppColors.green200)),
                child: Center(child: Text(parcelle.cultureIcon,
                    style: const TextStyle(fontSize: 26))),
              ),
              const SizedBox(width: 12),
              Expanded(child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(parcelle.nom,
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800,
                        color: AppColors.gray900)),
                  const SizedBox(height: 2),
                  Text(parcelle.ville?.isNotEmpty == true
                      ? parcelle.ville! : 'Localisation non renseignée',
                    style: const TextStyle(fontSize: 12, color: AppColors.gray400)),
                ],
              )),
              SmartBadge(label: parcelle.statutLabel, color: statBg, textColor: statColor),
            ],
          ),
          const SizedBox(height: 14),

          // ── Grille de détails ──
          Row(children: [
            _detail('🌱', 'Culture', parcelle.culture),
            _detail('📐', 'Superficie', '${parcelle.superficie} ha'),
            _detail('🌍', 'Sol', parcelle.typeSol),
          ]),
          const SizedBox(height: 14),

          // ── Actions ──
          Row(children: [
            Expanded(child: OutlinedButton.icon(
              onPressed: onPredict,
              icon: const Text('🔮', style: TextStyle(fontSize: 14)),
              label: const Text('Prédire', style: TextStyle(fontSize: 13)),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size(0, 40),
                side: const BorderSide(color: AppColors.green500),
                foregroundColor: AppColors.green700,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
            )),
            const SizedBox(width: 8),
            IconButton(
              onPressed: onEdit,
              icon: const Icon(Icons.edit_outlined, size: 20),
              style: IconButton.styleFrom(
                backgroundColor: AppColors.gray100,
                foregroundColor: AppColors.gray700,
              ),
            ),
            const SizedBox(width: 6),
            IconButton(
              onPressed: onDelete,
              icon: const Icon(Icons.delete_outline, size: 20),
              style: IconButton.styleFrom(
                backgroundColor: AppColors.redBg,
                foregroundColor: AppColors.red,
              ),
            ),
          ]),
        ],
      ),
    );
  }

  Widget _detail(String icon, String label, String value) {
    return Expanded(child: Column(children: [
      Text(icon, style: const TextStyle(fontSize: 16)),
      const SizedBox(height: 2),
      Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700,
          color: AppColors.gray900), textAlign: TextAlign.center),
      Text(label, style: const TextStyle(fontSize: 10, color: AppColors.gray400),
          textAlign: TextAlign.center),
    ]));
  }
}

extension on AppColors {
  static const Color gray600 = Color(0xFF4B5563);
  static const Color green200 = Color(0xFFB7E4C7);
}

// ── Formulaire modal ──────────────────────────────────────────────
class _ParcelleForm extends StatefulWidget {
  final ParcelleModel? parcelle;
  final Future<void> Function(Map<String, dynamic>) onSave;
  const _ParcelleForm({this.parcelle, required this.onSave});

  @override
  State<_ParcelleForm> createState() => _ParcelleFormState();
}

class _ParcelleFormState extends State<_ParcelleForm> {
  final _key = GlobalKey<FormState>();
  final _nomCtrl  = TextEditingController();
  final _supCtrl  = TextEditingController();
  final _villeCtrl= TextEditingController();
  final _descCtrl = TextEditingController();
  String _culture = 'mais';
  String _sol     = 'sableux';
  String _statut  = 'active';
  bool _saving    = false;

  @override
  void initState() {
    super.initState();
    if (widget.parcelle != null) {
      final p = widget.parcelle!;
      _nomCtrl.text   = p.nom;
      _supCtrl.text   = p.superficie.toString();
      _villeCtrl.text = p.ville ?? '';
      _descCtrl.text  = p.description ?? '';
      _culture = p.culture;
      _sol     = p.typeSol;
      _statut  = p.statut;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.parcelle != null;
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.fromLTRB(20, 16, 20,
          MediaQuery.of(context).viewInsets.bottom + 24),
      child: SingleChildScrollView(
        child: Form(
          key: _key,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(child: Container(width: 40, height: 4,
                decoration: BoxDecoration(color: AppColors.gray300,
                    borderRadius: BorderRadius.circular(2)))),
              const SizedBox(height: 16),
              Text(isEdit ? '✏️ Modifier la parcelle' : '🗺️ Nouvelle parcelle',
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800,
                    color: AppColors.gray900)),
              const SizedBox(height: 20),

              SmartTextField(label: 'Nom de la parcelle *', hint: 'Ex: Parcelle Nord',
                controller: _nomCtrl,
                validator: (v) => v!.isEmpty ? 'Nom requis' : null),
              const SizedBox(height: 14),

              Row(children: [
                Expanded(child: SmartTextField(
                  label: 'Superficie (ha) *', hint: 'Ex: 2.5',
                  controller: _supCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  validator: (v) {
                    if (v!.isEmpty) return 'Requis';
                    if (double.tryParse(v) == null) return 'Invalide';
                    return null;
                  })),
                const SizedBox(width: 12),
                Expanded(child: SmartTextField(
                  label: 'Ville / Zone', hint: 'Ex: Thiès',
                  controller: _villeCtrl)),
              ]),
              const SizedBox(height: 14),

              // Culture selector
              const Text('Culture *',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600,
                    color: AppColors.gray700)),
              const SizedBox(height: 8),
              _buildDropdown('Culture', _culture, {
                'mais': '🌽 Maïs', 'riz': '🌾 Riz', 'arachide': '🥜 Arachide',
                'sorgho': '🌿 Sorgho', 'mil': '🌿 Mil',
                'coton': '☁️ Coton', 'manioc': '🥔 Manioc',
              }, (v) => setState(() => _culture = v!)),
              const SizedBox(height: 14),

              const Text('Type de sol *',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600,
                    color: AppColors.gray700)),
              const SizedBox(height: 8),
              _buildDropdown('Sol', _sol, {
                'sableux': 'Sableux', 'argileux': 'Argileux',
                'limoneux': 'Limoneux', 'lateritique': 'Latéritique',
              }, (v) => setState(() => _sol = v!)),
              const SizedBox(height: 14),

              const Text('Statut',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600,
                    color: AppColors.gray700)),
              const SizedBox(height: 8),
              _buildDropdown('Statut', _statut, {
                'active': '✅ Active', 'en_repos': '⏸️ En repos', 'recoltee': '🏆 Récoltée',
              }, (v) => setState(() => _statut = v!)),
              const SizedBox(height: 14),

              SmartTextField(label: 'Description (optionnel)', hint: 'Notes…',
                controller: _descCtrl, maxLines: 2),
              const SizedBox(height: 24),

              PrimaryButton(
                label: isEdit ? 'Enregistrer les modifications' : 'Créer la parcelle',
                icon: isEdit ? '💾' : '🗺️',
                loading: _saving,
                onTap: _save,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDropdown(String hint, String value, Map<String, String> options,
      void Function(String?) onChanged) {
    return DropdownButtonFormField<String>(
      value: value,
      items: options.entries.map((e) => DropdownMenuItem(
        value: e.key,
        child: Text(e.value, style: const TextStyle(fontSize: 14)),
      )).toList(),
      onChanged: onChanged,
      decoration: InputDecoration(
        filled: true, fillColor: AppColors.gray50,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppColors.gray300)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppColors.gray300)),
      ),
    );
  }

  Future<void> _save() async {
    if (!_key.currentState!.validate()) return;
    setState(() => _saving = true);
    await widget.onSave({
      'nom':        _nomCtrl.text.trim(),
      'superficie': double.parse(_supCtrl.text),
      'culture':    _culture,
      'type_sol':   _sol,
      'statut':     _statut,
      'ville':      _villeCtrl.text.trim().isEmpty ? null : _villeCtrl.text.trim(),
      'description':_descCtrl.text.trim().isEmpty ? null : _descCtrl.text.trim(),
    });
    setState(() => _saving = false);
    if (mounted) Navigator.pop(context);
  }
}

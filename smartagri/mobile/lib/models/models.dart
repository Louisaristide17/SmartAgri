/// ================================================================
///  Modèles de données SmartAgri
/// ================================================================
import '../constants/ci_data.dart';

// ── Utilisateur ─────────────────────────────────────────────────
class UserModel {
  final int id;
  final String firstname;
  final String lastname;
  final String email;
  final String? phone;
  final String role;

  UserModel({
    required this.id,
    required this.firstname,
    required this.lastname,
    required this.email,
    this.phone,
    required this.role,
  });

  factory UserModel.fromJson(Map<String, dynamic> j) => UserModel(
    id:        j['id']        as int,
    firstname: j['firstname'] as String,
    lastname:  j['lastname']  as String,
    email:     j['email']     as String,
    phone:     j['phone']     as String?,
    role:      j['role']      as String? ?? 'agriculteur',
  );

  String get fullName => '$firstname $lastname';
  String get initials =>
      '${firstname.isNotEmpty ? firstname[0] : ''}${lastname.isNotEmpty ? lastname[0] : ''}'.toUpperCase();
}

// ── Parcelle ─────────────────────────────────────────────────────
class ParcelleModel {
  final int id;
  final String nom;
  final double superficie;
  final String typeSol;
  final String culture;
  final String? ville;
  final double? latitude;
  final double? longitude;
  final String statut;
  final String? description;
  final DateTime? createdAt;

  ParcelleModel({
    required this.id,
    required this.nom,
    required this.superficie,
    required this.typeSol,
    required this.culture,
    this.ville,
    this.latitude,
    this.longitude,
    required this.statut,
    this.description,
    this.createdAt,
  });

  factory ParcelleModel.fromJson(Map<String, dynamic> j) => ParcelleModel(
    id:         j['id']         as int,
    nom:        j['nom']        as String,
    superficie: (j['superficie'] as num).toDouble(),
    typeSol:    j['type_sol']   as String,
    culture:    j['culture']    as String,
    ville:      j['ville']      as String?,
    latitude:   (j['latitude']  as num?)?.toDouble(),
    longitude:  (j['longitude'] as num?)?.toDouble(),
    statut:     j['statut']     as String? ?? 'active',
    description:j['description'] as String?,
    createdAt:  j['created_at'] != null ? DateTime.tryParse(j['created_at']) : null,
  );

  Map<String, dynamic> toJson() => {
    'nom':        nom,
    'superficie': superficie,
    'type_sol':   typeSol,
    'culture':    culture,
    'ville':      ville,
    'latitude':   latitude,
    'longitude':  longitude,
    'statut':     statut,
    'description':description,
  };

  String get cultureIcon => CiData.emoji(culture);

  String get statutLabel {
    const labels = {'active': 'Active', 'en_repos': 'En repos', 'recoltee': 'Récoltée'};
    return labels[statut] ?? statut;
  }
}

// ── Prédiction ───────────────────────────────────────────────────
class PredictionModel {
  final int id;
  final String culture;
  final double pluviometrie;
  final double temperature;
  final double engraisKg;
  final double superficie;
  final String typeSol;
  final double rendementPredit;
  final double? confiance;
  final DateTime? createdAt;
  final String? zone;           // zone agro-écologique (renvoyée à la prédiction)
  final String? avertissement;  // ex. culture peu adaptée à la zone

  PredictionModel({
    required this.id,
    required this.culture,
    required this.pluviometrie,
    required this.temperature,
    required this.engraisKg,
    required this.superficie,
    required this.typeSol,
    required this.rendementPredit,
    this.confiance,
    this.createdAt,
    this.zone,
    this.avertissement,
  });

  factory PredictionModel.fromJson(Map<String, dynamic> j) => PredictionModel(
    id:              j['id']               as int,
    culture:         j['culture']          as String,
    pluviometrie:    (j['pluviometrie']     as num).toDouble(),
    temperature:     (j['temperature']     as num).toDouble(),
    engraisKg:       (j['engrais_kg']      as num).toDouble(),
    superficie:      (j['superficie']      as num).toDouble(),
    typeSol:         j['type_sol']         as String,
    rendementPredit: (j['rendement_predit'] as num).toDouble(),
    confiance:       (j['confiance']        as num?)?.toDouble(),
    createdAt:       j['created_at'] != null ? DateTime.tryParse(j['created_at']) : null,
    zone:            j['zone']             as String?,
    avertissement:   j['avertissement']    as String?,
  );
}

// ── Météo ─────────────────────────────────────────────────────────
class MeteoModel {
  final String ville;
  final double temperature;
  final double ressenti;
  final int humidite;
  final String description;
  final String icone;
  final double vent;
  final int pression;

  MeteoModel({
    required this.ville,
    required this.temperature,
    required this.ressenti,
    required this.humidite,
    required this.description,
    required this.icone,
    required this.vent,
    required this.pression,
  });

  factory MeteoModel.fromJson(Map<String, dynamic> j) => MeteoModel(
    ville:       j['ville']       as String,
    temperature: (j['temperature'] as num).toDouble(),
    ressenti:    (j['ressenti']    as num).toDouble(),
    humidite:    (j['humidite']    as num).toInt(),
    description: j['description'] as String,
    icone:       j['icone']       as String? ?? '01d',
    vent:        (j['vent']        as num).toDouble(),
    pression:    (j['pression']    as num).toInt(),
  );

  String get emojiIcon {
    final code = icone.length >= 2 ? icone.substring(0, 2) : '01';
    const map = {
      '01': '☀️', '02': '⛅', '03': '☁️', '04': '☁️',
      '09': '🌧️','10': '🌦️','11': '⛈️','13': '❄️','50': '🌫️',
    };
    return map[code] ?? '🌤️';
  }
}

class PrevisionJour {
  final String label;
  final String date;
  final double temp;
  final double pluie;
  final String icone;

  PrevisionJour({
    required this.label,
    required this.date,
    required this.temp,
    required this.pluie,
    required this.icone,
  });

  factory PrevisionJour.fromJson(Map<String, dynamic> j) => PrevisionJour(
    label: j['label'] as String,
    date:  j['date']  as String,
    temp:  (j['temp'] as num).toDouble(),
    pluie: (j['pluie'] as num).toDouble(),
    icone: j['icone'] as String? ?? '01d',
  );

  String get emojiIcon {
    final code = icone.length >= 2 ? icone.substring(0, 2) : '01';
    const map = {
      '01': '☀️', '02': '⛅', '03': '☁️', '04': '☁️',
      '09': '🌧️','10': '🌦️','11': '⛈️','13': '❄️','50': '🌫️',
    };
    return map[code] ?? '🌤️';
  }
}

// ── Message Chat ─────────────────────────────────────────────────
class ChatMessage {
  final String role;    // 'user' | 'assistant'
  final String content;
  final DateTime? createdAt;

  ChatMessage({required this.role, required this.content, this.createdAt});

  factory ChatMessage.fromJson(Map<String, dynamic> j) => ChatMessage(
    role:      j['role']    as String,
    content:   j['content'] as String,
    createdAt: j['created_at'] != null ? DateTime.tryParse(j['created_at']) : null,
  );

  bool get isUser => role == 'user';
}

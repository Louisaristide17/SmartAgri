/// Données agro-climatiques de la Côte d'Ivoire (mêmes valeurs que l'API).
class CiData {
  CiData._();

  /// Cultures prises en charge : code API -> libellé affiché
  static const Map<String, String> cultures = {
    'cacao':    '🍫 Cacao',
    'cafe':     '☕ Café',
    'hevea':    '🌳 Hévéa',
    'palmier':  '🌴 Palmier',
    'anacarde': '🥜 Anacarde',
    'coton':    '☁️ Coton',
    'mais':     '🌽 Maïs',
    'riz':      '🌾 Riz',
    'manioc':   '🥔 Manioc',
    'igname':   '🍠 Igname',
    'arachide': '🥜 Arachide',
    'sorgho':   '🌿 Sorgho',
    'mil':      '🌿 Mil',
  };

  /// Types de sol : code API -> libellé affiché
  static const Map<String, String> sols = {
    'ferrallitique': 'Ferrallitique',
    'argileux':      'Argileux',
    'hydromorphe':   'Hydromorphe',
    'alluvionnaire': 'Alluvionnaire',
    'limoneux':      'Limoneux',
    'lateritique':   'Latéritique',
    'sableux':       'Sableux',
  };

  /// Villes ivoiriennes proposées (météo et zone agro-écologique)
  static const List<String> villes = [
    'Abidjan', 'Yamoussoukro', 'Bouaké', 'Daloa', 'San-Pédro', 'Korhogo',
    'Man', 'Gagnoa', 'Abengourou', 'Bondoukou', 'Divo', 'Soubré',
    'Odienné', 'Tabou',
  ];

  // Plages des curseurs (réalistes pour la Côte d'Ivoire)
  static const double pluvMin = 300,  pluvMax = 2500, pluvDefaut = 1200;
  static const double tempMin = 18,   tempMax = 38,   tempDefaut = 27;
  static const double engraisMin = 0, engraisMax = 300, engraisDefaut = 50;

  /// Emoji d'une culture (🌱 par défaut)
  static String emoji(String culture) {
    final label = cultures[culture];
    if (label == null) return '🌱';
    return label.split(' ').first;
  }

  /// Nom lisible d'une culture, sans l'emoji
  static String nomCulture(String culture) {
    final label = cultures[culture];
    if (label == null) {
      if (culture.isEmpty) return culture;
      return culture[0].toUpperCase() + culture.substring(1);
    }
    return label.substring(label.indexOf(' ') + 1);
  }
}

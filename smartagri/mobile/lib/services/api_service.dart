import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// URL de l'API backend FastAPI
const String kApiBase = 'https://smartagri-api-d3ga.onrender.com'; // API Render (prod)
// const String kApiBase = 'http://10.0.2.2:8000';   // Android emulator → localhost
// const String kApiBase = 'http://localhost:8000';  // Web / iOS
// const String kApiBase = 'http://192.168.1.XX:8000'; // Réseau local réel

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => message;
}

class ApiService {
  // ── Singleton ─────────────────────────────────────
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  // ── Token JWT ─────────────────────────────────────
  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('smartagri_token');
  }

  static Future<void> setToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('smartagri_token', token);
  }

  static Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('smartagri_token');
    await prefs.remove('smartagri_user');
  }

  static Future<Map<String, dynamic>?> getUser() async {
    final prefs = await SharedPreferences.getInstance();
    final str = prefs.getString('smartagri_user');
    if (str == null) return null;
    return jsonDecode(str) as Map<String, dynamic>;
  }

  static Future<void> setUser(Map<String, dynamic> user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('smartagri_user', jsonEncode(user));
  }

  static Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  // ── Requête de base ───────────────────────────────
  Future<dynamic> _request(
    String method,
    String path, {
    Map<String, dynamic>? body,
    bool auth = true,
  }) async {
    final uri = Uri.parse('$kApiBase$path');
    final headers = <String, String>{'Content-Type': 'application/json'};

    if (auth) {
      final token = await getToken();
      if (token != null) headers['Authorization'] = 'Bearer $token';
    }

    http.Response response;
    final bodyStr = body != null ? jsonEncode(body) : null;

    switch (method) {
      case 'GET':
        response = await http.get(uri, headers: headers)
            .timeout(const Duration(seconds: 15));
        break;
      case 'POST':
        response = await http.post(uri, headers: headers, body: bodyStr)
            .timeout(const Duration(seconds: 15));
        break;
      case 'PUT':
        response = await http.put(uri, headers: headers, body: bodyStr)
            .timeout(const Duration(seconds: 15));
        break;
      case 'DELETE':
        response = await http.delete(uri, headers: headers)
            .timeout(const Duration(seconds: 15));
        break;
      default:
        throw ApiException('Méthode HTTP inconnue : $method');
    }

    if (response.statusCode == 204) return null;

    // Décodage UTF-8 explicite
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return decoded;
    }

    // Gestion des erreurs
    final detail = decoded['detail'];
    final message = detail is List
        ? detail.map((e) => e['msg'] ?? e.toString()).join(', ')
        : detail?.toString() ?? 'Erreur serveur (${response.statusCode})';

    throw ApiException(message);
  }

  // ══════════════════════════════════════════════════
  //  AUTH
  // ══════════════════════════════════════════════════
  Future<Map<String, dynamic>> login(String email, String password) async {
    final data = await _request('POST', '/api/auth/login',
        body: {'email': email, 'password': password}, auth: false);
    await setToken(data['access_token']);
    await setUser(data['user']);
    return data;
  }

  Future<Map<String, dynamic>> register({
    required String firstname,
    required String lastname,
    required String email,
    required String password,
    String? phone,
    String role = 'agriculteur',
  }) async {
    final data = await _request('POST', '/api/auth/register', body: {
      'firstname': firstname,
      'lastname':  lastname,
      'email':     email,
      'password':  password,
      'phone':     phone,
      'role':      role,
    }, auth: false);
    await setToken(data['access_token']);
    await setUser(data['user']);
    return data;
  }

  Future<void> logout() async => clearToken();

  // ══════════════════════════════════════════════════
  //  PARCELLES
  // ══════════════════════════════════════════════════
  Future<List<dynamic>> getParcelles() async =>
      await _request('GET', '/api/parcelles/') as List;

  Future<Map<String, dynamic>> createParcelle(Map<String, dynamic> p) async =>
      await _request('POST', '/api/parcelles/', body: p);

  Future<Map<String, dynamic>> updateParcelle(int id, Map<String, dynamic> p) async =>
      await _request('PUT', '/api/parcelles/$id', body: p);

  Future<void> deleteParcelle(int id) async =>
      await _request('DELETE', '/api/parcelles/$id');

  // ══════════════════════════════════════════════════
  //  PRÉDICTION
  // ══════════════════════════════════════════════════
  Future<Map<String, dynamic>> predict(Map<String, dynamic> input) async =>
      await _request('POST', '/api/prediction/', body: input);

  Future<Map<String, dynamic>> getZoneGps(double lat, double lon) async =>
      await _request('GET', '/api/prediction/zone?latitude=$lat&longitude=$lon', auth: false);

  Future<List<dynamic>> getHistoriquePredictions() async =>
      await _request('GET', '/api/prediction/historique') as List;

  // ══════════════════════════════════════════════════
  //  MÉTÉO
  // ══════════════════════════════════════════════════
  Future<Map<String, dynamic>> getMeteo(String ville) async =>
      await _request('GET', '/api/meteo/${Uri.encodeComponent(ville)}', auth: false);

  Future<Map<String, dynamic>> getPrevisions(String ville) async =>
      await _request('GET', '/api/meteo/${Uri.encodeComponent(ville)}/previsions', auth: false);

  // ══════════════════════════════════════════════════
  //  AGRIBOT
  // ══════════════════════════════════════════════════
  Future<Map<String, dynamic>> sendMessage(String content) async =>
      await _request('POST', '/api/agribot/message', body: {'content': content});

  Future<List<dynamic>> getHistoriqueChat() async =>
      await _request('GET', '/api/agribot/historique') as List;

  Future<void> clearHistoriqueChat() async =>
      await _request('DELETE', '/api/agribot/historique');
}

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'constants/app_colors.dart';
import 'constants/app_theme.dart';
import 'services/api_service.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/parcelles_screen.dart';
import 'screens/prediction_screen.dart';
import 'screens/meteo_screen.dart';
import 'screens/agribot_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Orientation portrait uniquement (téléphone rural)
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Barre de statut transparente avec icônes sombres
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
  ));

  runApp(const SmartAgriApp());
}

class SmartAgriApp extends StatelessWidget {
  const SmartAgriApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SmartAgri',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.theme,
      home: const _AuthGate(),
    );
  }
}

// ── Portail d'authentification ────────────────────────────────────
class _AuthGate extends StatefulWidget {
  const _AuthGate();

  @override
  State<_AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<_AuthGate> {
  bool? _isLoggedIn;

  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    final logged = await ApiService.isLoggedIn();
    setState(() => _isLoggedIn = logged);
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoggedIn == null) {
      return const Scaffold(
        backgroundColor: AppColors.green900,
        body: Center(child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('🌱', style: TextStyle(fontSize: 64)),
            SizedBox(height: 16),
            Text('SmartAgri',
              style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800,
                  color: AppColors.white)),
            SizedBox(height: 32),
            CircularProgressIndicator(color: AppColors.green300),
          ],
        )),
      );
    }

    if (_isLoggedIn == false) {
      return LoginScreen(
        onLoginSuccess: () => setState(() => _isLoggedIn = true),
      );
    }

    return MainScreen(
      onLogout: () => setState(() => _isLoggedIn = false),
    );
  }
}

// ── Navigation principale avec barre du bas ───────────────────────
class MainScreen extends StatefulWidget {
  final VoidCallback onLogout;
  const MainScreen({super.key, required this.onLogout});

  @override
  State<MainScreen> createState() => MainScreenState();
}

class MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;

  // Permet aux autres écrans de changer d'onglet
  void setTab(int index) {
    setState(() => _currentIndex = index);
  }

  static const List<_NavItem> _navItems = [
    _NavItem(icon: '🏠', label: 'Accueil'),
    _NavItem(icon: '🗺️', label: 'Parcelles'),
    _NavItem(icon: '🔮', label: 'Prédire'),
    _NavItem(icon: '🌦️', label: 'Météo'),
    _NavItem(icon: '👵🏻', label: 'AgriBot'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: [
          HomeScreen(onLogout: widget.onLogout),
          const ParcellesScreen(),
          const PredictionScreen(),
          const MeteoScreen(),
          const AgribotScreen(),
        ],
      ),
      bottomNavigationBar: _buildNavBar(),
    );
  }

  Widget _buildNavBar() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.white,
        border: const Border(top: BorderSide(color: AppColors.gray200)),
        boxShadow: [BoxShadow(
          color: Colors.black.withOpacity(0.08),
          blurRadius: 16, offset: const Offset(0, -4))],
      ),
      child: SafeArea(
        child: SizedBox(
          height: 68,
          child: Row(
            children: List.generate(_navItems.length, (i) {
              final item = _navItems[i];
              final selected = _currentIndex == i;
              return Expanded(
                child: GestureDetector(
                  onTap: () => setState(() => _currentIndex = i),
                  behavior: HitTestBehavior.opaque,
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // Indicateur sélectionné
                        AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          width: selected ? 48 : 0,
                          height: selected ? 32 : 0,
                          decoration: BoxDecoration(
                            color: selected ? AppColors.green100 : Colors.transparent,
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Center(
                            child: Text(item.icon,
                              style: TextStyle(
                                fontSize: selected ? 20 : 22)),
                          ),
                        ),
                        if (!selected)
                          Text(item.icon, style: const TextStyle(fontSize: 22)),
                        const SizedBox(height: 3),
                        Text(item.label,
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                            color: selected ? AppColors.green700 : AppColors.gray400,
                          )),
                      ],
                    ),
                  ),
                ),
              );
            }),
          ),
        ),
      ),
    );
  }
}

class _NavItem {
  final String icon;
  final String label;
  const _NavItem({required this.icon, required this.label});
}

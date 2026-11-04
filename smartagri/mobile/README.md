# 📱 SmartAgri Mobile — Application Flutter

> Version mobile de la plateforme SmartAgri, conçue pour être simple, accessible et utilisable même dans les zones rurales.

---

## 🚀 Démarrage rapide

### Prérequis
- Flutter SDK ≥ 3.0 : https://flutter.dev/docs/get-started/install
- Android Studio ou VS Code avec extension Flutter
- Un émulateur Android ou un téléphone physique

### Lancer l'application

```bash
cd smartagri/mobile

# Installer les dépendances
flutter pub get

# Lancer sur émulateur (backend doit tourner sur http://localhost:8000)
flutter run

# Générer un APK de démonstration
flutter build apk --release
```

### Connecter au backend
Dans `lib/services/api_service.dart`, la constante `kApiBase` :

```dart
// Android Emulator → localhost
const String kApiBase = 'http://10.0.2.2:8000';

// Appareil physique sur le même réseau WiFi
const String kApiBase = 'http://192.168.1.XX:8000';  // IP de votre PC

// iOS Simulator
const String kApiBase = 'http://localhost:8000';
```

---

## 📂 Structure du projet

```
mobile/
├── lib/
│   ├── main.dart                 ← Entrée + navigation
│   ├── constants/
│   │   ├── app_colors.dart       ← Charte couleurs verte SmartAgri
│   │   └── app_theme.dart        ← Thème Material 3
│   ├── services/
│   │   └── api_service.dart      ← Client HTTP FastAPI
│   ├── models/
│   │   └── models.dart           ← User, Parcelle, Prediction, Meteo, Chat
│   ├── widgets/
│   │   └── common_widgets.dart   ← Boutons, cards, badges, toasts
│   └── screens/
│       ├── login_screen.dart     ← Connexion / Inscription
│       ├── home_screen.dart      ← Dashboard avec stats
│       ├── parcelles_screen.dart ← CRUD parcelles
│       ├── prediction_screen.dart← Prédiction IA avec sliders
│       ├── meteo_screen.dart     ← Météo + conseils agronomiques
│       └── agribot_screen.dart   ← Chat IA AgriBot
└── pubspec.yaml
```

---

## ✨ Fonctionnalités

| Écran       | Ce que l'agriculteur peut faire                        |
|-------------|--------------------------------------------------------|
| 🏠 Accueil  | Voir ses stats, la météo du jour, accès rapides        |
| 🗺️ Parcelles| Ajouter, modifier, supprimer ses parcelles              |
| 🔮 Prédire  | Estimer son rendement avec des curseurs simples         |
| 🌦️ Météo   | Consulter la météo de sa ville + conseils du jour       |
| 👵🏻 AgriBot  | Poser des questions à l'assistant IA                    |

---

## 🎨 Design accessible

- **Grandes zones tactiles** (min 54px) pour les doigts
- **Textes grands et lisibles** (14–22px)
- **Icônes emoji** universellement compréhensibles
- **Contrastes élevés** charte verte sur blanc
- **Navigation par pictogrammes** + libellés
- **Compte démo** pré-rempli d'un seul clic

---

## 🔑 Compte de démo

```
Email    : demo@smartagri.com
Mot de passe : Demo1234!
```

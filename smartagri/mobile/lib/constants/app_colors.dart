import 'package:flutter/material.dart';

/// Charte graphique SmartAgri — palette verte agricole
class AppColors {
  AppColors._();

  // ── Verts principaux ──────────────────────────────
  static const Color green900 = Color(0xFF1B4332);
  static const Color green700 = Color(0xFF2D6A4F);
  static const Color green500 = Color(0xFF40916C);
  static const Color green300 = Color(0xFF74C69D);
  static const Color green100 = Color(0xFFD8F3DC);
  static const Color green50  = Color(0xFFF0FDF4);

  // ── Couleurs fonctionnelles ───────────────────────
  static const Color orange   = Color(0xFFF4A261);
  static const Color orangeBg = Color(0xFFFFF3E0);
  static const Color blue     = Color(0xFF3B82F6);
  static const Color blueBg   = Color(0xFFEFF6FF);
  static const Color red      = Color(0xFFEF4444);
  static const Color redBg    = Color(0xFFFEE2E2);
  static const Color yellow   = Color(0xFFEAB308);
  static const Color yellowBg = Color(0xFFFEFCE8);
  static const Color purple   = Color(0xFF8B5CF6);
  static const Color purpleBg = Color(0xFFF5F3FF);

  // ── Neutres ───────────────────────────────────────
  static const Color white    = Color(0xFFFFFFFF);
  static const Color gray50   = Color(0xFFF9FAFB);
  static const Color gray100  = Color(0xFFF3F4F6);
  static const Color gray200  = Color(0xFFE5E7EB);
  static const Color gray300  = Color(0xFFD1D5DB);
  static const Color gray400  = Color(0xFF9CA3AF);
  static const Color gray500  = Color(0xFF6B7280);
  static const Color gray700  = Color(0xFF374151);
  static const Color gray900  = Color(0xFF111827);

  // ── Dégradé principal ─────────────────────────────
  static const LinearGradient primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [green500, green700],
  );

  static const LinearGradient heroGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [green700, green900],
  );
}

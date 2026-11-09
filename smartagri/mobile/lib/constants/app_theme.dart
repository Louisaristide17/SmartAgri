import 'package:flutter/material.dart';
import 'app_colors.dart';

class AppTheme {
  AppTheme._();

  static ThemeData get theme => ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.green500,
      primary:   AppColors.green500,
      secondary: AppColors.green300,
      surface:   AppColors.white,
      error:     AppColors.red,
    ),

    // ── Typographie grande et lisible pour usage rural ──
    fontFamily: 'Roboto',
    textTheme: const TextTheme(
      // Titres grands et clairs
      displayLarge:  TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: AppColors.gray900, height: 1.2),
      displayMedium: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: AppColors.gray900, height: 1.3),
      headlineLarge: TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: AppColors.gray900),
      headlineMedium:TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: AppColors.gray900),
      headlineSmall: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.gray900),
      // Corps de texte
      bodyLarge:     TextStyle(fontSize: 16, fontWeight: FontWeight.w400, color: AppColors.gray700, height: 1.6),
      bodyMedium:    TextStyle(fontSize: 14, fontWeight: FontWeight.w400, color: AppColors.gray700, height: 1.5),
      bodySmall:     TextStyle(fontSize: 12, fontWeight: FontWeight.w400, color: AppColors.gray500),
      // Labels
      labelLarge:    TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: AppColors.white),
      labelMedium:   TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: AppColors.gray700),
      labelSmall:    TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: AppColors.gray500),
    ),

    // ── AppBar ──
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.white,
      foregroundColor: AppColors.gray900,
      elevation: 0,
      scrolledUnderElevation: 1,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.w700,
        color: AppColors.gray900,
        fontFamily: 'Roboto',
      ),
    ),

    // ── Boutons ──
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.green500,
        foregroundColor: AppColors.white,
        minimumSize: const Size(double.infinity, 54),  // grand pour toucher rural
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
        elevation: 2,
      ),
    ),

    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.green500,
        side: const BorderSide(color: AppColors.green500, width: 1.5),
        minimumSize: const Size(double.infinity, 54),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),

    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: AppColors.green500,
        textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
      ),
    ),

    // ── Champs de texte ──
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.gray50,
      contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.gray300),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.gray300, width: 1.5),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.green500, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.red, width: 1.5),
      ),
      labelStyle: const TextStyle(color: AppColors.gray500, fontSize: 14),
      hintStyle: const TextStyle(color: AppColors.gray400, fontSize: 14),
    ),

    // ── Cards ──
    cardTheme: CardThemeData(
      color: AppColors.white,
      elevation: 2,
      shadowColor: Colors.black12,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 0),
    ),

    // ── Navigation bar ──
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: AppColors.white,
      indicatorColor: AppColors.green100,
      labelTextStyle: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.green700);
        }
        return const TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: AppColors.gray500);
      }),
      iconTheme: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return const IconThemeData(color: AppColors.green700, size: 26);
        }
        return const IconThemeData(color: AppColors.gray400, size: 24);
      }),
      elevation: 8,
      height: 70,
    ),

    // ── Scaffold ──
    scaffoldBackgroundColor: AppColors.gray50,

    // ── SnackBar ──
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      contentTextStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
    ),

    // ── Slider ──
    sliderTheme: const SliderThemeData(
      activeTrackColor: AppColors.green500,
      thumbColor: AppColors.green700,
      inactiveTrackColor: AppColors.green100,
      overlayColor: Color(0x2040916C),
      trackHeight: 6,
      thumbShape: RoundSliderThumbShape(enabledThumbRadius: 14),
    ),

    // ── Divider ──
    dividerTheme: const DividerThemeData(color: AppColors.gray200, thickness: 1),
  );
}

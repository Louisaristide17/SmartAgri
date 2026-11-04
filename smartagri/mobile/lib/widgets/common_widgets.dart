import 'package:flutter/material.dart';
import '../constants/app_colors.dart';

// ── Bouton principal grand ────────────────────────────────────────
class PrimaryButton extends StatelessWidget {
  final String label;
  final String? icon;
  final VoidCallback? onTap;
  final bool loading;
  final Color? color;

  const PrimaryButton({
    super.key,
    required this.label,
    this.icon,
    this.onTap,
    this.loading = false,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton(
        onPressed: loading ? null : onTap,
        style: ElevatedButton.styleFrom(
          backgroundColor: color ?? AppColors.green500,
          foregroundColor: AppColors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          elevation: 3,
        ),
        child: loading
            ? const SizedBox(
                width: 22, height: 22,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  color: AppColors.white,
                ),
              )
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (icon != null) ...[
                    Text(icon!, style: const TextStyle(fontSize: 20)),
                    const SizedBox(width: 10),
                  ],
                  Text(label,
                    style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.w700)),
                ],
              ),
      ),
    );
  }
}

// ── Card avec ombre légère ────────────────────────────────────────
class SmartCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets? padding;
  final VoidCallback? onTap;
  final Color? color;

  const SmartCard({
    super.key,
    required this.child,
    this.padding,
    this.onTap,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color ?? AppColors.white,
      borderRadius: BorderRadius.circular(16),
      elevation: 2,
      shadowColor: Colors.black12,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: padding ?? const EdgeInsets.all(16),
          child: child,
        ),
      ),
    );
  }
}

// ── Stat Card (dashboard) ─────────────────────────────────────────
class StatCard extends StatelessWidget {
  final String icon;
  final String value;
  final String label;
  final String? trend;
  final Color bgColor;

  const StatCard({
    super.key,
    required this.icon,
    required this.value,
    required this.label,
    this.trend,
    this.bgColor = AppColors.green100,
  });

  @override
  Widget build(BuildContext context) {
    return SmartCard(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 44, height: 44,
            decoration: BoxDecoration(
              color: bgColor,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: Text(icon, style: const TextStyle(fontSize: 22)),
            ),
          ),
          const SizedBox(height: 10),
          Text(value,
            style: const TextStyle(
              fontSize: 22, fontWeight: FontWeight.w800, color: AppColors.gray900)),
          const SizedBox(height: 2),
          Text(label,
            style: const TextStyle(fontSize: 12, color: AppColors.gray500)),
          if (trend != null) ...[
            const SizedBox(height: 4),
            Text(trend!,
              style: const TextStyle(
                fontSize: 11, fontWeight: FontWeight.w600,
                color: Color(0xFF16A34A))),
          ],
        ],
      ),
    );
  }
}

// ── Champ de formulaire avec label et icône ───────────────────────
class SmartTextField extends StatelessWidget {
  final String label;
  final String? hint;
  final String? prefixIcon;
  final TextEditingController? controller;
  final bool obscure;
  final Widget? suffixWidget;
  final TextInputType? keyboardType;
  final String? Function(String?)? validator;
  final void Function(String)? onChanged;
  final int? maxLines;

  const SmartTextField({
    super.key,
    required this.label,
    this.hint,
    this.prefixIcon,
    this.controller,
    this.obscure = false,
    this.suffixWidget,
    this.keyboardType,
    this.validator,
    this.onChanged,
    this.maxLines = 1,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
          style: const TextStyle(
            fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.gray700)),
        const SizedBox(height: 6),
        TextFormField(
          controller: controller,
          obscureText: obscure,
          keyboardType: keyboardType,
          validator: validator,
          onChanged: onChanged,
          maxLines: maxLines,
          style: const TextStyle(fontSize: 15, color: AppColors.gray900),
          decoration: InputDecoration(
            hintText: hint,
            prefixIcon: prefixIcon != null
                ? Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(prefixIcon!, style: const TextStyle(fontSize: 20)),
                  )
                : null,
            suffixIcon: suffixWidget,
          ),
        ),
      ],
    );
  }
}

// ── Badge coloré ─────────────────────────────────────────────────
class SmartBadge extends StatelessWidget {
  final String label;
  final Color color;
  final Color textColor;

  const SmartBadge({
    super.key,
    required this.label,
    this.color = AppColors.green100,
    this.textColor = AppColors.green700,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(label,
        style: TextStyle(
          fontSize: 11, fontWeight: FontWeight.w700, color: textColor)),
    );
  }
}

// ── Section titre ─────────────────────────────────────────────────
class SectionTitle extends StatelessWidget {
  final String title;
  final String? action;
  final VoidCallback? onAction;

  const SectionTitle({super.key, required this.title, this.action, this.onAction});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(title,
          style: const TextStyle(
            fontSize: 17, fontWeight: FontWeight.w700, color: AppColors.gray900)),
        if (action != null)
          TextButton(
            onPressed: onAction,
            child: Text(action!,
              style: const TextStyle(fontSize: 13, color: AppColors.green500)),
          ),
      ],
    );
  }
}

// ── Toast helper ─────────────────────────────────────────────────
void showSnack(BuildContext context, String message, {bool error = false}) {
  ScaffoldMessenger.of(context).clearSnackBars();
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Row(children: [
        Text(error ? '❌' : '✅', style: const TextStyle(fontSize: 16)),
        const SizedBox(width: 10),
        Expanded(child: Text(message,
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500))),
      ]),
      backgroundColor: error ? AppColors.red : const Color(0xFF166534),
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      margin: const EdgeInsets.all(16),
      duration: const Duration(seconds: 3),
    ),
  );
}

// ── Etat vide ─────────────────────────────────────────────────────
class EmptyState extends StatelessWidget {
  final String icon;
  final String title;
  final String subtitle;
  final String? buttonLabel;
  final VoidCallback? onButton;

  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.subtitle,
    this.buttonLabel,
    this.onButton,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(icon, style: const TextStyle(fontSize: 56)),
            const SizedBox(height: 16),
            Text(title,
              style: const TextStyle(
                fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.gray700),
              textAlign: TextAlign.center),
            const SizedBox(height: 8),
            Text(subtitle,
              style: const TextStyle(fontSize: 14, color: AppColors.gray400),
              textAlign: TextAlign.center),
            if (buttonLabel != null) ...[
              const SizedBox(height: 20),
              SizedBox(
                width: 200,
                child: PrimaryButton(label: buttonLabel!, onTap: onButton),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ── Skeleton loading ─────────────────────────────────────────────
class SkeletonBox extends StatefulWidget {
  final double width;
  final double height;
  final double radius;

  const SkeletonBox({
    super.key,
    required this.width,
    required this.height,
    this.radius = 8,
  });

  @override
  State<SkeletonBox> createState() => _SkeletonBoxState();
}

class _SkeletonBoxState extends State<SkeletonBox>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1200))
      ..repeat(reverse: true);
    _anim = Tween<double>(begin: 0.4, end: 1.0).animate(_ctrl);
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _anim,
      child: Container(
        width: widget.width, height: widget.height,
        decoration: BoxDecoration(
          color: AppColors.gray200,
          borderRadius: BorderRadius.circular(widget.radius),
        ),
      ),
    );
  }
}

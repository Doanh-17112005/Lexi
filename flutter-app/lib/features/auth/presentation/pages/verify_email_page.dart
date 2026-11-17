import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:lexilingo_app/core/theme/app_theme.dart';
import '../providers/auth_provider.dart';

class VerifyEmailPage extends StatefulWidget {
  const VerifyEmailPage({super.key, required this.token});

  final String? token;

  @override
  State<VerifyEmailPage> createState() => _VerifyEmailPageState();
}

class _VerifyEmailPageState extends State<VerifyEmailPage> {
  bool _isVerifying = true;
  bool _isVerified = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _verify());
  }

  Future<void> _verify() async {
    final token = widget.token;
    if (token == null || token.isEmpty) {
      setState(() => _isVerifying = false);
      return;
    }

    setState(() => _isVerifying = true);
    final success = await context.read<AuthProvider>().verifyEmail(token);
    if (!mounted) return;
    setState(() {
      _isVerifying = false;
      _isVerified = success;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final provider = context.watch<AuthProvider>();
    final hasToken = widget.token?.isNotEmpty ?? false;
    final isDark = theme.brightness == Brightness.dark;

    final message = _isVerifying
        ? 'auth.emailVerificationInProgress'.tr()
        : _isVerified
        ? 'auth.emailVerificationSuccess'.tr()
        : provider.errorMessage ?? 'auth.emailVerificationInvalid'.tr();

    return Scaffold(
      backgroundColor: isDark
          ? AppColors.accentMintDark
          : AppColors.backgroundLight,
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (_isVerifying)
                    const CircularProgressIndicator()
                  else
                    Icon(
                      _isVerified
                          ? Icons.verified_outlined
                          : Icons.error_outline,
                      size: 72,
                      color: _isVerified ? AppColors.accentMint : Colors.red,
                    ),
                  const SizedBox(height: 24),
                  Text(
                    message,
                    textAlign: TextAlign.center,
                    style: theme.textTheme.titleLarge,
                  ),
                  const SizedBox(height: 24),
                  if (!_isVerifying && !_isVerified && hasToken)
                    OutlinedButton(
                      onPressed: _verify,
                      child: Text('auth.emailVerificationRetry'.tr()),
                    ),
                  if (!_isVerifying)
                    TextButton(
                      onPressed: () => Navigator.of(
                        context,
                      ).popUntil((route) => route.isFirst),
                      child: Text('auth.emailVerificationBackToLogin'.tr()),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

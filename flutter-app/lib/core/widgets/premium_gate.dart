import 'package:flutter/material.dart';
import 'package:lexilingo_app/core/di/service_locator.dart';
import 'package:lexilingo_app/core/services/entitlement_service.dart';
import 'package:lexilingo_app/features/premium/presentation/screens/paywall_screen.dart';

/// Wraps any widget that requires a premium subscription.
/// Shows [child] for premium users, [lockedChild] (or a default lock UI)
/// for free users with a tap to open the paywall.
class PremiumGate extends StatefulWidget {
  final Widget child;
  final Widget? lockedChild;

  const PremiumGate({super.key, required this.child, this.lockedChild});

  @override
  State<PremiumGate> createState() => _PremiumGateState();
}

class _PremiumGateState extends State<PremiumGate> {
  bool? _isPremium;

  @override
  void initState() {
    super.initState();
    _check();
  }

  /// Asks the backend, which reads the row it synced from RevenueCat itself.
  ///
  /// If core DI is unavailable, remain locked. Local SDK state is never used
  /// as authorization; only the backend-synced entitlement may unlock UI.
  Future<void> _check() async {
    final value = sl.isRegistered<EntitlementService>()
        ? await sl<EntitlementService>().fetchCached()
        : false;
    if (mounted) setState(() => _isPremium = value);
  }

  @override
  Widget build(BuildContext context) {
    if (_isPremium == null && widget.lockedChild != null) {
      return _buildLockedContent();
    }
    if (_isPremium == null) return const SizedBox.shrink();
    if (_isPremium!) return widget.child;

    return _buildLockedContent();
  }

  Widget _buildLockedContent() {
    return GestureDetector(
      onTap: () async {
        final unlocked = await Navigator.of(
          context,
        ).push<bool>(MaterialPageRoute(builder: (_) => const PaywallScreen()));
        if (unlocked == true) _check();
      },
      child:
          widget.lockedChild ??
          ColoredBox(
            color: Colors.black12,
            child: Stack(
              alignment: Alignment.center,
              children: [
                widget.child,
                Container(
                  color: Colors.black.withValues(alpha: 0.5),
                  child: const Icon(
                    Icons.lock_rounded,
                    color: Colors.white,
                    size: 36,
                  ),
                ),
              ],
            ),
          ),
    );
  }
}

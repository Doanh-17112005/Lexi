import 'package:flutter/foundation.dart';
import 'package:url_launcher/url_launcher.dart';

/// Keeps local Web OAuth on the hostname Firebase authorizes by default.
///
/// Firebase treats `localhost` and `127.0.0.1` as different domains. Local
/// developers often open the latter from server logs, while Firebase projects
/// normally authorize only `localhost`.
class WebAuthOriginService {
  const WebAuthOriginService._();

  static Future<bool> redirectLoopbackToLocalhost() async {
    if (!kIsWeb || Uri.base.host != '127.0.0.1') {
      return false;
    }

    final localhostUri = Uri.base.replace(host: 'localhost');
    return launchUrl(localhostUri, webOnlyWindowName: '_self');
  }
}

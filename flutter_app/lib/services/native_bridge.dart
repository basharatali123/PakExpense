import 'package:flutter/services.dart';
import 'sms_parser.dart';
import 'database_helper.dart';

typedef OnMessageParsedCallback = void Function(ParsedResult parsed);

class NativeBridge {
  static const MethodChannel _channel = MethodChannel('com.pakexpense.app/native');
  static OnMessageParsedCallback? onMessageParsed;

  static void initialize() {
    _channel.setMethodCallHandler((call) async {
      if (call.method == 'onMessageReceived') {
        final data = Map<String, dynamic>.from(call.arguments);
        final body = data['body'] as String? ?? '';
        final sender = data['sender'] as String? ?? '';

        final parsed = PakistanSmsParser.parse(body, sender: sender);
        if (parsed != null) {
          final saved = await DatabaseHelper.instance.saveParsedResult(parsed);
          if (saved && onMessageParsed != null) {
            onMessageParsed!(parsed);
          }
        }
      }
    });
  }

  static Future<bool> openNotificationSettings() async {
    try {
      final res = await _channel.invokeMethod<bool>('openNotificationSettings');
      return res ?? false;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> isNotificationListenerEnabled() async {
    try {
      final res = await _channel.invokeMethod<bool>('isNotificationListenerEnabled');
      return res ?? false;
    } catch (_) {
      return false;
    }
  }
}

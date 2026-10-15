import 'package:flutter/material.dart';
import '../services/sms_parser.dart';
import '../services/database_helper.dart';
import '../services/native_bridge.dart';

class SmsParserScreen extends StatefulWidget {
  final VoidCallback onDataChanged;
  const SmsParserScreen({Key? key, required this.onDataChanged}) : super(key: key);

  @override
  State<SmsParserScreen> createState() => _SmsParserScreenState();
}

class _SmsParserScreenState extends State<SmsParserScreen> {
  final _smsController = TextEditingController();
  List<ParsedResult> _parsedList = [];
  bool _isNotificationListenerActive = false;

  @override
  void initState() {
    super.initState();
    _checkPermissions();
  }

  Future<void> _checkPermissions() async {
    try {
      final active = await NativeBridge.isNotificationListenerEnabled();
      if (!mounted) return;
      setState(() => _isNotificationListenerActive = active);
    } catch (_) {}
  }

  void _loadSampleSms() {
    setState(() {
      _smsController.text =
          'Rs 1,610.00 paid to DAEWOO on 16-10-2026 at 00:27:16. Fee: Rs 0.00, TID:727238040565\n\n'
          'PKR 8,371.00 charged at JINNAH PHARMACY for card used, from A/C xxx2120 (THOKAR NIAZ BAIG LHR) on 08-Oct-2026 at 05:08 TID:560755\n\n'
          'PKR 10,035.00 cash withdrawn from 1Link ATM from A/C xxx2120 THOKAR NIAZ BAIG LHR on 08-Oct-2026 at 05:24 TID:387289\n\n'
          'PKR 5,000.00 sent to BASHARAT ALI JAZZ-xxxCASH from your A/C xxx2120 on 12-Oct-2026 at 22:08 Fee: Rs.2.00 TID:353041\n\n'
          'Transferred Rs. 2000 to BILAL SHAH. Fee: Rs. 0. New balance is Rs. 8,500. Trx ID: 1029384756';
    });
    _parseText();
  }

  void _parseText() {
    final text = _smsController.text.trim();
    if (text.isEmpty) return;

    final blocks = text.split(RegExp(r'\n\s*\n+'));
    final results = <ParsedResult>[];

    for (var b in blocks) {
      final parsed = PakistanSmsParser.parse(b);
      if (parsed != null) results.add(parsed);
    }

    setState(() {
      _parsedList = results;
    });
  }

  Future<void> _saveAll() async {
    int imported = 0;
    int skipped = 0;

    for (var item in _parsedList) {
      final saved = await DatabaseHelper.instance.saveParsedResult(item);
      if (saved) {
        imported++;
      } else {
        skipped++;
      }
    }

    widget.onDataChanged();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Imported $imported transactions ($skipped duplicates skipped).'),
        backgroundColor: Colors.green,
      ),
    );

    setState(() {
      _parsedList.clear();
      _smsController.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Automation Service Banner
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: isDark ? const Color(0xFF1E293B) : Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.teal.withOpacity(0.3)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.bolt, color: Colors.amber, size: 20),
                  const SizedBox(width: 8),
                  const Text('Real-Time Android Auto-Capture', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                ],
              ),
              const SizedBox(height: 8),
              const Text(
                '• JazzCash (8558) SMS: Background Broadcast Receiver Active\n'
                '• Meezan Bank (8079) SMS: Background Broadcast Receiver Active',
                style: TextStyle(color: Colors.grey, fontSize: 11),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      '• EasyPaisa In-App Notifications: ${_isNotificationListenerActive ? "🟢 Active" : "🔴 Requires Access"}',
                      style: TextStyle(
                        color: _isNotificationListenerActive ? Colors.green : Colors.redAccent,
                        fontWeight: FontWeight.bold,
                        fontSize: 11,
                      ),
                    ),
                  ),
                  if (!_isNotificationListenerActive)
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.teal,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        textStyle: const TextStyle(fontSize: 11),
                      ),
                      onPressed: () async {
                        await NativeBridge.openNotificationSettings();
                        await _checkPermissions();
                      },
                      child: const Text('Grant Access'),
                    ),
                ],
              ),
            ],
          ),
        ),

        const SizedBox(height: 20),
        const Text('Paste or Test SMS Alerts', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
        const SizedBox(height: 8),

        TextField(
          controller: _smsController,
          maxLines: 5,
          decoration: InputDecoration(
            hintText: 'Paste incoming SMS from JazzCash (8558), Meezan (8079), or EasyPaisa...',
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
            filled: true,
            fillColor: isDark ? const Color(0xFF1E293B) : Colors.grey.shade100,
          ),
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0D9488), foregroundColor: Colors.white),
                icon: const Icon(Icons.flash_on, size: 18),
                label: const Text('Parse SMS'),
                onPressed: _parseText,
              ),
            ),
            const SizedBox(width: 8),
            OutlinedButton(
              onPressed: _loadSampleSms,
              child: const Text('Load Sample SMS'),
            ),
          ],
        ),

        const SizedBox(height: 20),
        if (_parsedList.isNotEmpty) ...[
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Parsed Results (${_parsedList.length})', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white),
                icon: const Icon(Icons.save, size: 16),
                label: const Text('Save to SQLite'),
                onPressed: _saveAll,
              ),
            ],
          ),
          const SizedBox(height: 10),
          ..._parsedList.map((p) {
            final isCredit = p.transType == 'Credit';
            return Card(
              margin: const EdgeInsets.only(bottom: 8),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: isCredit ? Colors.green.withOpacity(0.2) : Colors.red.withOpacity(0.2),
                  child: Text(isCredit ? '+' : '-', style: TextStyle(color: isCredit ? Colors.green : Colors.red, fontWeight: FontWeight.bold)),
                ),
                title: Text('${p.provider} • Rs. ${p.amount.toStringAsFixed(2)}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                subtitle: Text('👤 ${p.recipientOrSender}\n🏷️ ${p.category} | TID: ${p.refId}', style: const TextStyle(fontSize: 11)),
                trailing: Text(p.transType, style: TextStyle(color: isCredit ? Colors.green : Colors.red, fontWeight: FontWeight.bold)),
              ),
            );
          }),
        ],
      ],
    );
  }
}

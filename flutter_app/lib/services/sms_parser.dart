class ParsedResult {
  final String provider;
  final String transType; // 'Debit' or 'Credit'
  final double amount;
  final String dateStr;
  final String recipientOrSender;
  final String refId;
  final double fee;
  final double? balanceAfter;
  final String category;
  final String rawText;
  final String accountName;

  ParsedResult({
    required this.provider,
    required this.transType,
    required this.amount,
    required this.dateStr,
    required this.recipientOrSender,
    required this.refId,
    this.fee = 0.0,
    this.balanceAfter,
    required this.category,
    required this.rawText,
    required this.accountName,
  });
}

class PakistanSmsParser {
  static double cleanAmount(String? valStr) {
    if (valStr == null || valStr.isEmpty) return 0.0;
    String cleaned = valStr.replaceAll(RegExp(r'[^\d.]'), '');
    List<String> parts = cleaned.split('.');
    if (parts.length > 2) {
      cleaned = '${parts.sublist(0, parts.length - 1).join('')}.${parts.last}';
    }
    return double.tryParse(cleaned) ?? 0.0;
  }

  static String extractDateTime(String text, String defaultDate) {
    // 1. on DD-MM-YYYY at HH:MM:SS or on YYYY-MM-DD at HH:MM:SS
    final m1 = RegExp(r'on\s+(\d{2,4}[-/]\d{2}[-/]\d{2,4})\s+at\s+(\d{1,2}:\d{2}(?::\d{2})?)', caseSensitive: false).firstMatch(text);
    if (m1 != null) {
      String d = m1.group(1)!;
      String t = m1.group(2)!.substring(0, 5);
      return '$d $t';
    }

    // 2. on DD-Mon-YYYY at HH:MM
    final m2 = RegExp(r'on\s+(\d{1,2}-[A-Za-z]+-\d{4})\s+at\s+(\d{1,2}:\d{2})', caseSensitive: false).firstMatch(text);
    if (m2 != null) {
      return '${m2.group(1)} ${m2.group(2)}';
    }

    return defaultDate;
  }

  static String detectCategory(String text, String transType) {
    final lower = text.toLowerCase();

    if (['salary', 'payroll', 'dividend'].any((w) => lower.contains(w))) {
      return 'Salary / Income';
    }
    if (['k-electric', 'lesco', 'iesco', 'ssgc', 'sngpl', 'ptcl', 'bill payment', 'electricity bill', 'gas bill'].any((w) => lower.contains(w))) {
      return 'Bills & Utilities (KE/LESCO/SNGPL/PTCL)';
    }
    if (['atm', 'cash withdrawal', 'cash withdrawn', '1link atm'].any((w) => lower.contains(w))) {
      return 'Cash Withdrawal (ATM)';
    }
    if (['shell', 'pso', 'total parco', 'bykea', 'careem', 'indrive', 'uber', 'petrol', 'daewoo', 'niazi', 'faisal movers'].any((w) => lower.contains(w))) {
      return 'Fuel & Transport (Careem/Bykea/Shell/PSO)';
    }
    if (['foodpanda', 'kfc', 'mcdonald', 'subway', 'cheezious', 'chaye khana', 'cafe', 'restaurant'].any((w) => lower.contains(w))) {
      return 'Food & Dining';
    }
    if (['imtiaz', 'carrefour', 'al-fatah', 'metro', 'chase up', 'naheed', 'supermarket', 'mart'].any((w) => lower.contains(w))) {
      return 'Groceries & Supermarket';
    }
    if (['pharmacy', 'jinnah pharmacy', 'hospital', 'clinic', 'medical', 'chughtai', 'd-watson'].any((w) => lower.contains(w))) {
      return 'Health & Medical';
    }
    if (['easyload', 'prepaid load', 'mobile load', 'super card'].any((w) => lower.contains(w))) {
      return 'Mobile Load & Packages';
    }

    return transType == 'Credit' ? 'Money Transfer Received' : 'Money Transfer Sent';
  }

  static ParsedResult? parse(String text, {String sender = ''}) {
    text = text.trim();
    if (text.isEmpty) return null;

    final lower = text.toLowerCase();
    final senderLower = sender.trim().toLowerCase();
    final nowStr = DateTime.now().toString().substring(0, 16);

    // 1. JazzCash (8558)
    if (senderLower.contains('8558') || senderLower.contains('jazzcash') || lower.contains('jazzcash')) {
      return _parseJazzCash(text, nowStr);
    }

    // 2. Meezan Bank (8079 or 8267)
    if (senderLower.contains('8079') || senderLower.contains('8267') || lower.contains('meezan')) {
      return _parseMeezan(text, nowStr);
    }

    // 3. EasyPaisa (3737 or push notification)
    if (senderLower.contains('3737') || senderLower.contains('easypaisa') || lower.contains('easypaisa')) {
      return _parseEasyPaisa(text, nowStr);
    }

    // Fallbacks
    if (senderLower.contains('8558')) return _parseJazzCash(text, nowStr);
    if (senderLower.contains('8079') || senderLower.contains('8267')) return _parseMeezan(text, nowStr);
    if (senderLower.contains('3737')) return _parseEasyPaisa(text, nowStr);

    return null;
  }

  static ParsedResult? _parseJazzCash(String text, String defaultDate) {
    final lower = text.toLowerCase();
    String transType = 'Debit';
    double amount = 0.0;
    String refId = '';
    String recipient = 'JazzCash Service';
    double? balanceAfter;
    double fee = 0.0;
    String transDate = extractDateTime(text, defaultDate);

    // TID / Trx ID
    final trxMatch = RegExp(r'(?:Trx\s*ID|TID|T\.ID|Trx)\s*[:#]?\s*(\d+)', caseSensitive: false).firstMatch(text);
    if (trxMatch != null) refId = trxMatch.group(1)!;

    // Fee
    final feeMatch = RegExp(r'Fee\s*[:#]?\s*(?:Rs\.?|PKR)?\s*([\d,.]+)', caseSensitive: false).firstMatch(text);
    if (feeMatch != null) fee = cleanAmount(feeMatch.group(1));

    // Balance
    final balMatch = RegExp(r'(?:Balance|Bal|New Bal|New Balance)\s*[:#]?\s*(?:Rs\.?|PKR)?\s*([\d,.]+)', caseSensitive: false).firstMatch(text);
    if (balMatch != null) balanceAfter = cleanAmount(balMatch.group(1));

    // Amount
    final amtMatch = RegExp(r'(?:amount of\s+)?(?:Rs\.?|PKR)\s*([\d,.]+)', caseSensitive: false).firstMatch(text);
    if (amtMatch != null) amount = cleanAmount(amtMatch.group(1));

    if (lower.contains('received')) {
      transType = 'Credit';
      final m = RegExp(r'received\s+(?:Rs\.?|PKR)?\s*[\d,.]*\s+from\s+([^.]+?)(?:\s+in|\s+on|\.|$)', caseSensitive: false).firstMatch(text);
      if (m != null) {
        recipient = m.group(1)!.trim();
      } else if (lower.contains('via raast')) {
        recipient = 'Received via Raast';
      }
    } else if (['sent to', 'transferred to', 'paid to'].any((k) => lower.contains(k))) {
      transType = 'Debit';
      final m = RegExp(r'(?:sent to|transferred to|paid to)\s+([^.]+?)(?:\s+of\s+iban|\s+from|\s+on\s+\d|\s+at\s+\d|\s+fee|\.|$)', caseSensitive: false).firstMatch(text);
      if (m != null) recipient = m.group(1)!.trim();
    }

    if (amount <= 0) return null;
    final cat = detectCategory(text, transType);

    return ParsedResult(
      provider: 'JazzCash',
      transType: transType,
      amount: amount,
      dateStr: transDate,
      recipientOrSender: recipient,
      refId: refId,
      fee: fee,
      balanceAfter: balanceAfter,
      category: cat,
      rawText: text,
      accountName: 'JazzCash',
    );
  }

  static ParsedResult? _parseMeezan(String text, String defaultDate) {
    final lower = text.toLowerCase();
    String transType = lower.contains('credited') ? 'Credit' : 'Debit';

    final amtMatch = RegExp(r'(?:PKR|Rs\.?)\s*([\d,.]+)', caseSensitive: false).firstMatch(text);
    if (amtMatch == null) return null;
    double amount = cleanAmount(amtMatch.group(1));

    final balMatch = RegExp(r'(?:Available\s+Bal(?:ance)?\s+is\s+(?:PKR|Rs\.?)|Avail\s+Bal\s+(?:PKR|Rs\.?))\s*([\d,.]+)', caseSensitive: false).firstMatch(text);
    double? balanceAfter = balMatch != null ? cleanAmount(balMatch.group(1)) : null;

    final refMatch = RegExp(r'(?:Ref\s*[:#]?|Reference\s*[:#]?|TID\s*[:#]?)\s*([A-Za-z0-9]+)', caseSensitive: false).firstMatch(text);
    String refId = refMatch != null ? refMatch.group(1)! : '';

    final feeMatch = RegExp(r'Fee\s*[:#]?\s*(?:Rs\.?|PKR)?\s*([\d,.]+)', caseSensitive: false).firstMatch(text);
    double fee = feeMatch != null ? cleanAmount(feeMatch.group(1)) : 0.0;

    String transDate = extractDateTime(text, defaultDate);
    String recipient = 'Meezan Bank';

    if (lower.contains('charged at')) {
      final m = RegExp(r'charged\s+at\s+([^.]+?)\s+for\s+card\s+used', caseSensitive: false).firstMatch(text);
      if (m != null) recipient = m.group(1)!.trim();
    } else if (lower.contains('cash withdrawn')) {
      final m = RegExp(r'cash\s+withdrawn\s+from\s+([^.]+?)\s+from\s+A/C', caseSensitive: false).firstMatch(text);
      recipient = m != null ? m.group(1)!.trim() : '1Link ATM';
    } else if (lower.contains('sent to')) {
      final m = RegExp(r'sent\s+to\s+([^.]+?)\s+from\s+your\s+A/C', caseSensitive: false).firstMatch(text);
      if (m != null) recipient = m.group(1)!.trim();
    }

    if (amount <= 0) return null;
    final cat = detectCategory(text, transType);

    return ParsedResult(
      provider: 'Meezan Bank',
      transType: transType,
      amount: amount,
      dateStr: transDate,
      recipientOrSender: recipient,
      refId: refId,
      fee: fee,
      balanceAfter: balanceAfter,
      category: cat,
      rawText: text,
      accountName: 'Meezan Bank',
    );
  }

  static ParsedResult? _parseEasyPaisa(String text, String defaultDate) {
    final lower = text.toLowerCase();
    String transType = 'Debit';
    double amount = 0.0;
    String refId = '';
    String recipient = 'EasyPaisa Service';
    double? balanceAfter;
    double fee = 0.0;
    String transDate = extractDateTime(text, defaultDate);

    final trxMatch = RegExp(r'(?:Trx\s*ID|Trans\s*ID|TR\s*ID|TID)\s*[:#]?\s*(\d+)', caseSensitive: false).firstMatch(text);
    if (trxMatch != null) refId = trxMatch.group(1)!;

    final balMatch = RegExp(r'(?:new\s+balance\s+is|bal(?:ance)?\s*[:#]?)\s*(?:Rs\.?|PKR)?\s*([\d,.]+)', caseSensitive: false).firstMatch(text);
    if (balMatch != null) balanceAfter = cleanAmount(balMatch.group(1));

    final amtMatch = RegExp(r'(?:Rs\.?|PKR)\s*([\d,.]+)', caseSensitive: false).firstMatch(text);
    if (amtMatch != null) amount = cleanAmount(amtMatch.group(1));

    if (lower.contains('received')) {
      transType = 'Credit';
      final m = RegExp(r'received\s+(?:Rs\.?|PKR)?\s*[\d,.]*\s+from\s+([^.]+?)(?:\.|$)', caseSensitive: false).firstMatch(text);
      if (m != null) recipient = m.group(1)!.trim();
    } else if (lower.contains('transferred') || lower.contains('sent')) {
      transType = 'Debit';
      final m = RegExp(r'(?:transferred|sent)\s+(?:Rs\.?|PKR)?\s*[\d,.]*\s+to\s+([^.]+?)(?:\.|\s+fee|\s+new balance|$)', caseSensitive: false).firstMatch(text);
      if (m != null) recipient = m.group(1)!.trim();
    }

    if (amount <= 0) return null;
    final cat = detectCategory(text, transType);

    return ParsedResult(
      provider: 'EasyPaisa',
      transType: transType,
      amount: amount,
      dateStr: transDate,
      recipientOrSender: recipient,
      refId: refId,
      fee: fee,
      balanceAfter: balanceAfter,
      category: cat,
      rawText: text,
      accountName: 'EasyPaisa',
    );
  }
}

class AccountModel {
  final int? id;
  final String name;
  final String code;
  final String accountType;
  final String color;
  final double balance;

  AccountModel({
    this.id,
    required this.name,
    required this.code,
    required this.accountType,
    required this.color,
    required this.balance,
  });

  factory AccountModel.fromMap(Map<String, dynamic> map) {
    return AccountModel(
      id: map['id'],
      name: map['name'],
      code: map['code'] ?? '',
      accountType: map['account_type'],
      color: map['color'] ?? '#0D9488',
      balance: (map['balance'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'code': code,
      'account_type': accountType,
      'color': color,
      'balance': balance,
    };
  }
}

class CategoryModel {
  final int? id;
  final String name;
  final String categoryType;
  final String icon;

  CategoryModel({
    this.id,
    required this.name,
    required this.categoryType,
    required this.icon,
  });

  factory CategoryModel.fromMap(Map<String, dynamic> map) {
    return CategoryModel(
      id: map['id'],
      name: map['name'],
      categoryType: map['category_type'],
      icon: map['icon'] ?? '💵',
    );
  }
}

class TransactionModel {
  final int? id;
  final int accountId;
  final int? categoryId;
  final String transDate;
  final double amount;
  final String transType; // 'Debit' or 'Credit'
  final String recipientOrSender;
  final String description;
  final String refId;
  final double fee;
  final String rawText;
  final String sourceChannel;
  
  // Joined fields for display
  final String? accountName;
  final String? accountColor;
  final String? categoryName;
  final String? categoryIcon;

  TransactionModel({
    this.id,
    required this.accountId,
    this.categoryId,
    required this.transDate,
    required this.amount,
    required this.transType,
    required this.recipientOrSender,
    required this.description,
    required this.refId,
    this.fee = 0.0,
    this.rawText = '',
    this.sourceChannel = 'SMS',
    this.accountName,
    this.accountColor,
    this.categoryName,
    this.categoryIcon,
  });

  factory TransactionModel.fromMap(Map<String, dynamic> map) {
    return TransactionModel(
      id: map['id'],
      accountId: map['account_id'],
      categoryId: map['category_id'],
      transDate: map['trans_date'],
      amount: (map['amount'] as num).toDouble(),
      transType: map['trans_type'],
      recipientOrSender: map['recipient_or_sender'] ?? '',
      description: map['description'] ?? '',
      refId: map['ref_id'] ?? '',
      fee: (map['fee'] as num?)?.toDouble() ?? 0.0,
      rawText: map['raw_sms'] ?? '',
      sourceChannel: map['source_channel'] ?? 'Manual',
      accountName: map['account_name'],
      accountColor: map['account_color'],
      categoryName: map['category_name'],
      categoryIcon: map['category_icon'],
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'account_id': accountId,
      'category_id': categoryId,
      'trans_date': transDate,
      'amount': amount,
      'trans_type': transType,
      'recipient_or_sender': recipientOrSender,
      'description': description,
      'ref_id': refId,
      'fee': fee,
      'raw_sms': rawText,
      'source_channel': sourceChannel,
    };
  }
}

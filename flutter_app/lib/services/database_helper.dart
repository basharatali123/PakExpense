import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/transaction_model.dart';
import 'sms_parser.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;
  static Future<Database>? _dbFuture;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _dbFuture ??= _initDB('pak_finance.db');
    _database = await _dbFuture;
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDB,
    );
  }

  Future<void> _createDB(Database db, int version) async {
    await db.execute('''
      CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        code TEXT,
        account_type TEXT NOT NULL,
        color TEXT DEFAULT '#0D9488',
        balance REAL DEFAULT 0.0
      );
    ''');

    await db.execute('''
      CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category_type TEXT NOT NULL,
        icon TEXT DEFAULT '💵'
      );
    ''');

    await db.execute('''
      CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL,
        category_id INTEGER,
        trans_date TEXT NOT NULL,
        amount REAL NOT NULL,
        trans_type TEXT NOT NULL,
        recipient_or_sender TEXT,
        description TEXT,
        ref_id TEXT,
        fee REAL DEFAULT 0.0,
        raw_sms TEXT,
        source_channel TEXT DEFAULT 'Manual',
        FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
      );
    ''');

    // Seed default Pakistani accounts
    final accounts = [
      {'name': 'JazzCash', 'code': '8558', 'account_type': 'Wallet', 'color': '#E53935'},
      {'name': 'EasyPaisa', 'code': '3737', 'account_type': 'Wallet', 'color': '#43A047'},
      {'name': 'Meezan Bank', 'code': '8079', 'account_type': 'Islamic Bank', 'color': '#1B5E20'},
      {'name': 'HBL', 'code': '4250', 'account_type': 'Commercial Bank', 'color': '#004D40'},
      {'name': 'Bank Alfalah', 'code': '8222', 'account_type': 'Commercial Bank', 'color': '#C2185B'},
      {'name': 'SadaPay', 'code': 'SadaPay', 'account_type': 'Fintech', 'color': '#00E5FF'},
      {'name': 'Cash Wallet', 'code': 'CASH', 'account_type': 'Cash', 'color': '#7CB342'},
    ];

    for (var acc in accounts) {
      await db.insert('accounts', acc, conflictAlgorithm: ConflictAlgorithm.ignore);
    }

    // Seed default Pakistani categories
    final categories = [
      {'name': 'Bills & Utilities (KE/LESCO/SNGPL/PTCL)', 'category_type': 'Expense', 'icon': '💡'},
      {'name': 'Groceries & Supermarket', 'category_type': 'Expense', 'icon': '🛒'},
      {'name': 'Fuel & Transport (Careem/Bykea/Shell/PSO)', 'category_type': 'Expense', 'icon': '⛽'},
      {'name': 'Food & Dining', 'category_type': 'Expense', 'icon': '🍔'},
      {'name': 'Mobile Load & Packages', 'category_type': 'Expense', 'icon': '📱'},
      {'name': 'Health & Medical', 'category_type': 'Expense', 'icon': '💊'},
      {'name': 'Cash Withdrawal (ATM)', 'category_type': 'Expense', 'icon': '🏧'},
      {'name': 'Money Transfer Sent', 'category_type': 'Expense', 'icon': '📤'},
      {'name': 'Other Expenses', 'category_type': 'Expense', 'icon': '📦'},
      {'name': 'Salary / Income', 'category_type': 'Income', 'icon': '💰'},
      {'name': 'Money Transfer Received', 'category_type': 'Income', 'icon': '📥'},
      {'name': 'Other Income', 'category_type': 'Income', 'icon': '💵'},
    ];

    for (var cat in categories) {
      await db.insert('categories', cat, conflictAlgorithm: ConflictAlgorithm.ignore);
    }
  }

  Future<List<AccountModel>> getAccounts() async {
    final db = await database;
    final res = await db.query('accounts', orderBy: 'id ASC');
    return res.map((m) => AccountModel.fromMap(m)).toList();
  }

  Future<List<CategoryModel>> getCategories({String? type}) async {
    final db = await database;
    final res = type != null
        ? await db.query('categories', where: 'category_type = ?', whereArgs: [type], orderBy: 'name ASC')
        : await db.query('categories', orderBy: 'name ASC');
    return res.map((m) => CategoryModel.fromMap(m)).toList();
  }

  Future<int> addTransaction(TransactionModel tx) async {
    final db = await database;
    final id = await db.insert('transactions', tx.toMap());

    // Update account balance
    double delta = tx.transType == 'Debit' ? -tx.amount : tx.amount;
    if (tx.transType == 'Debit' && tx.fee > 0) delta -= tx.fee;

    await db.rawUpdate(
      'UPDATE accounts SET balance = balance + ? WHERE id = ?',
      [delta, tx.accountId],
    );

    return id;
  }

  Future<bool> deleteTransaction(int id) async {
    final db = await database;
    final rows = await db.query('transactions', where: 'id = ?', whereArgs: [id]);
    if (rows.isEmpty) return false;

    final tx = rows.first;
    final accountId = tx['account_id'] as int;
    final amount = (tx['amount'] as num).toDouble();
    final fee = (tx['fee'] as num?)?.toDouble() ?? 0.0;
    final type = tx['trans_type'] as String;

    double revertDelta = type == 'Debit' ? amount : -amount;
    if (type == 'Debit' && fee > 0) revertDelta += fee;

    await db.rawUpdate('UPDATE accounts SET balance = balance + ? WHERE id = ?', [revertDelta, accountId]);
    await db.delete('transactions', where: 'id = ?', whereArgs: [id]);
    return true;
  }

  Future<List<TransactionModel>> getTransactions({int limit = 100}) async {
    final db = await database;
    final res = await db.rawQuery('''
      SELECT 
        t.*,
        a.name AS account_name,
        a.color AS account_color,
        c.name AS category_name,
        c.icon AS category_icon
      FROM transactions t
      JOIN accounts a ON t.account_id = a.id
      LEFT JOIN categories c ON t.category_id = c.id
      ORDER BY t.trans_date DESC, t.id DESC
      LIMIT ?;
    ''', [limit]);

    return res.map((m) => TransactionModel.fromMap(m)).toList();
  }

  Future<bool> isDuplicate(String refId, double amount) async {
    if (refId.isEmpty) return false;
    final db = await database;
    final res = await db.query('transactions', where: 'ref_id = ?', whereArgs: [refId]);
    return res.isNotEmpty;
  }

  Future<bool> saveParsedResult(ParsedResult parsed) async {
    if (parsed.refId.isNotEmpty && await isDuplicate(parsed.refId, parsed.amount)) {
      return false; // Skip duplicate
    }

    final accounts = await getAccounts();
    int accountId = accounts.first.id!;
    for (var acc in accounts) {
      if (parsed.provider.toLowerCase().contains(acc.name.toLowerCase()) ||
          acc.name.toLowerCase().contains(parsed.provider.toLowerCase())) {
        accountId = acc.id!;
        break;
      }
    }

    final categories = await getCategories();
    int? categoryId;
    for (var cat in categories) {
      if (cat.name.toLowerCase() == parsed.category.toLowerCase()) {
        categoryId = cat.id;
        break;
      }
    }

    await addTransaction(TransactionModel(
      accountId: accountId,
      categoryId: categoryId,
      transDate: parsed.dateStr,
      amount: parsed.amount,
      transType: parsed.transType,
      recipientOrSender: parsed.recipientOrSender,
      description: '${parsed.provider} SMS/Push Alert',
      refId: parsed.refId,
      fee: parsed.fee,
      rawText: parsed.rawText,
      sourceChannel: 'SMS',
    ));

    // Update account balance directly if balanceAfter is present
    if (parsed.balanceAfter != null && parsed.balanceAfter! >= 0) {
      final db = await database;
      await db.update('accounts', {'balance': parsed.balanceAfter}, where: 'id = ?', whereArgs: [accountId]);
    }

    return true;
  }

  Future<Map<String, dynamic>> getDashboardSummary() async {
    try {
      final db = await database;
      final nowMonth = DateTime.now().toString().substring(0, 7); // YYYY-MM

      // Net worth
      final nwRes = await db.rawQuery('SELECT SUM(balance) as total FROM accounts;');
      double netWorth = 0.0;
      if (nwRes.isNotEmpty && nwRes.first['total'] != null) {
        netWorth = (nwRes.first['total'] as num).toDouble();
      }

      // Monthly Income
      final incRes = await db.rawQuery(
        "SELECT SUM(amount) as total FROM transactions WHERE trans_type = 'Credit' AND trans_date LIKE ?;",
        ['$nowMonth%'],
      );
      double income = 0.0;
      if (incRes.isNotEmpty && incRes.first['total'] != null) {
        income = (incRes.first['total'] as num).toDouble();
      }

      // Monthly Expense
      final expRes = await db.rawQuery(
        "SELECT SUM(amount + COALESCE(fee, 0)) as total FROM transactions WHERE trans_type = 'Debit' AND trans_date LIKE ?;",
        ['$nowMonth%'],
      );
      double expense = 0.0;
      if (expRes.isNotEmpty && expRes.first['total'] != null) {
        expense = (expRes.first['total'] as num).toDouble();
      }

      // Accounts
      final accounts = await getAccounts();

      return {
        'net_worth': netWorth,
        'monthly_income': income,
        'monthly_expense': expense,
        'net_savings': income - expense,
        'accounts': accounts,
      };
    } catch (e) {
      return {
        'net_worth': 0.0,
        'monthly_income': 0.0,
        'monthly_expense': 0.0,
        'net_savings': 0.0,
        'accounts': <AccountModel>[],
      };
    }
  }
}

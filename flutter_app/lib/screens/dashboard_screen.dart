import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/transaction_model.dart';
import '../services/database_helper.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final currencyFormat = NumberFormat.currency(locale: 'en_PK', symbol: 'Rs. ', decimalDigits: 2);
  bool _isLoading = true;
  double _netWorth = 0.0;
  double _monthlyIncome = 0.0;
  double _monthlyExpense = 0.0;
  List<AccountModel> _accounts = [];
  List<TransactionModel> _recentTxs = [];

  @override
  void initState() {
    super.initState();
    refreshData();
  }

  Future<void> refreshData() async {
    setState(() => _isLoading = true);
    final summary = await DatabaseHelper.instance.getDashboardSummary();
    final recent = await DatabaseHelper.instance.getTransactions(limit: 6);

    setState(() {
      _netWorth = summary['net_worth'];
      _monthlyIncome = summary['monthly_income'];
      _monthlyExpense = summary['monthly_expense'];
      _accounts = summary['accounts'];
      _recentTxs = recent;
      _isLoading = false;
    });
  }

  Color _hexToColor(String hex) {
    hex = hex.replaceAll('#', '');
    if (hex.length == 6) hex = 'FF$hex';
    return Color(int.tryParse(hex, radix: 16) ?? 0xFF0D9488);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return RefreshIndicator(
      onRefresh: refreshData,
      child: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
        children: [
          // Net Worth Card
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF0F766E), Color(0xFF14B8A6)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF0D9488).withOpacity(0.3),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '💎 Total Net Worth',
                  style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Text(
                  currencyFormat.format(_netWorth),
                  style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('📥 Income (Month)', style: TextStyle(color: Colors.white70, fontSize: 11)),
                          const SizedBox(height: 2),
                          Text(currencyFormat.format(_monthlyIncome), style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold)),
                        ],
                      ),
                    ),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('📤 Expense (Month)', style: TextStyle(color: Colors.white70, fontSize: 11)),
                          const SizedBox(height: 2),
                          Text(currencyFormat.format(_monthlyExpense), style: const TextStyle(color: Color(0xFFFFCDD2), fontSize: 14, fontWeight: FontWeight.bold)),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: 24),
          const Text(
            'Wallets & Bank Accounts',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),

          // Horizontal Accounts List
          SizedBox(
            height: 95,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: _accounts.length,
              itemBuilder: (context, index) {
                final acc = _accounts[index];
                final color = _hexToColor(acc.color);
                return Container(
                  width: 150,
                  margin: const EdgeInsets.only(right: 12),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF1E293B) : Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: color.withOpacity(0.3)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(acc.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          Container(
                            width: 8,
                            height: 8,
                            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
                          ),
                        ],
                      ),
                      Text(
                        currencyFormat.format(acc.balance),
                        style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 14),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),

          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Recent Activity', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              IconButton(icon: const Icon(Icons.refresh, size: 20), onPressed: refreshData),
            ],
          ),
          const SizedBox(height: 8),

          // Recent Activity Feed
          if (_recentTxs.isEmpty)
            Container(
              padding: const EdgeInsets.all(30),
              alignment: Alignment.center,
              child: const Text(
                'No transactions logged yet.\nIncoming SMS & EasyPaisa push notifications will appear here automatically!',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey, fontSize: 12),
              ),
            )
          else
            ..._recentTxs.map((tx) {
              final isCredit = tx.transType == 'Credit';
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                decoration: BoxDecoration(
                  color: isDark ? const Color(0xFF1E293B) : Colors.white,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  children: [
                    CircleAvatar(
                      backgroundColor: (isCredit ? Colors.green : Colors.red).withOpacity(0.15),
                      child: Text(tx.categoryIcon ?? (isCredit ? '📥' : '📤'), style: const TextStyle(fontSize: 16)),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            tx.recipientOrSender.isNotEmpty ? tx.recipientOrSender : (tx.description),
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 2),
                          Text(
                            '${tx.accountName ?? ''} • ${tx.transDate}',
                            style: const TextStyle(color: Colors.grey, fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                    Text(
                      '${isCredit ? '+' : '-'}${currencyFormat.format(tx.amount)}',
                      style: TextStyle(
                        color: isCredit ? Colors.green : Colors.red,
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }
}

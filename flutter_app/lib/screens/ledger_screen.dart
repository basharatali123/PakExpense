import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/transaction_model.dart';
import '../services/database_helper.dart';

class LedgerScreen extends StatefulWidget {
  final VoidCallback onDataChanged;
  const LedgerScreen({Key? key, required this.onDataChanged}) : super(key: key);

  @override
  State<LedgerScreen> createState() => _LedgerScreenState();
}

class _LedgerScreenState extends State<LedgerScreen> {
  final currencyFormat = NumberFormat.currency(locale: 'en_PK', symbol: 'Rs. ', decimalDigits: 2);
  List<TransactionModel> _transactions = [];
  List<TransactionModel> _filteredTransactions = [];
  final _searchController = TextEditingController();
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadTransactions();
  }

  Future<void> _loadTransactions() async {
    setState(() => _isLoading = true);
    final txs = await DatabaseHelper.instance.getTransactions(limit: 200);
    setState(() {
      _transactions = txs;
      _filteredTransactions = txs;
      _isLoading = false;
    });
  }

  void _onSearch(String query) {
    if (query.isEmpty) {
      setState(() => _filteredTransactions = _transactions);
      return;
    }
    final q = query.toLowerCase();
    setState(() {
      _filteredTransactions = _transactions.where((t) {
        return t.recipientOrSender.toLowerCase().contains(q) ||
            t.description.toLowerCase().contains(q) ||
            t.refId.toLowerCase().contains(q) ||
            (t.accountName?.toLowerCase().contains(q) ?? false);
      }).toList();
    });
  }

  Future<void> _deleteTx(int id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Transaction'),
        content: const Text('Delete this record? Its balance change will be reverted.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      await DatabaseHelper.instance.deleteTransaction(id);
      await _loadTransactions();
      widget.onDataChanged();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: TextField(
            controller: _searchController,
            onChanged: _onSearch,
            decoration: InputDecoration(
              prefixIcon: const Icon(Icons.search),
              hintText: 'Search merchant, note, or TID...',
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
              isDense: true,
            ),
          ),
        ),
        Expanded(
          child: _isLoading
              ? const Center(child: CircularProgressIndicator())
              : _filteredTransactions.isEmpty
                  ? const Center(child: Text('No transactions found.'))
                  : ListView.builder(
                      itemCount: _filteredTransactions.length,
                      itemBuilder: (context, index) {
                        final tx = _filteredTransactions[index];
                        final isCredit = tx.transType == 'Credit';

                        return Dismissible(
                          key: Key('tx_${tx.id}'),
                          direction: DismissDirection.endToStart,
                          background: Container(
                            color: Colors.red,
                            alignment: Alignment.centerRight,
                            padding: const EdgeInsets.only(right: 20),
                            child: const Icon(Icons.delete, color: Colors.white),
                          ),
                          onDismissed: (_) => _deleteTx(tx.id!),
                          child: ListTile(
                            leading: CircleAvatar(
                              backgroundColor: (isCredit ? Colors.green : Colors.red).withOpacity(0.15),
                              child: Text(tx.categoryIcon ?? (isCredit ? '📥' : '📤')),
                            ),
                            title: Text(
                              tx.recipientOrSender.isNotEmpty ? tx.recipientOrSender : tx.description,
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                            ),
                            subtitle: Text(
                              '${tx.accountName ?? ''} • ${tx.transDate}\n${tx.refId.isNotEmpty ? "TID: " + tx.refId : ""}',
                              style: const TextStyle(fontSize: 11, color: Colors.grey),
                            ),
                            trailing: Text(
                              '${isCredit ? '+' : '-'}${currencyFormat.format(tx.amount)}',
                              style: TextStyle(
                                color: isCredit ? Colors.green : Colors.red,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        );
                      },
                    ),
        ),
      ],
    );
  }
}

import 'package:flutter/material.dart';
import '../models/transaction_model.dart';
import '../services/database_helper.dart';

class QuickAddScreen extends StatefulWidget {
  final VoidCallback onDataChanged;
  const QuickAddScreen({Key? key, required this.onDataChanged}) : super(key: key);

  @override
  State<QuickAddScreen> createState() => _QuickAddScreenState();
}

class _QuickAddScreenState extends State<QuickAddScreen> {
  final _amountController = TextEditingController();
  final _noteController = TextEditingController();
  final _refController = TextEditingController();

  String _transType = 'Debit';
  int? _selectedAccountId;
  int? _selectedCategoryId;

  List<AccountModel> _accounts = [];
  List<CategoryModel> _categories = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadFormData();
  }

  Future<void> _loadFormData() async {
    try {
      final accs = await DatabaseHelper.instance.getAccounts();
      final cats = await DatabaseHelper.instance.getCategories();

      if (!mounted) return;
      setState(() {
        _accounts = accs;
        _categories = cats;
        if (accs.isNotEmpty) _selectedAccountId = accs.first.id;
        if (cats.isNotEmpty) _selectedCategoryId = cats.first.id;
        _isLoading = false;
      });
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _saveTransaction() async {
    final amtText = _amountController.text.trim().replaceAll(',', '');
    final amount = double.tryParse(amtText);

    if (amount == null || amount <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a valid amount.')),
      );
      return;
    }

    final tx = TransactionModel(
      accountId: _selectedAccountId!,
      categoryId: _selectedCategoryId,
      transDate: DateTime.now().toString().substring(0, 16),
      amount: amount,
      transType: _transType,
      recipientOrSender: _noteController.text.trim().isEmpty ? 'Manual Entry' : _noteController.text.trim(),
      description: 'Quick Add',
      refId: _refController.text.trim(),
      sourceChannel: 'Manual',
    );

    await DatabaseHelper.instance.addTransaction(tx);
    widget.onDataChanged();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Recorded $_transType of Rs. ${amount.toStringAsFixed(2)}!'),
        backgroundColor: Colors.teal,
      ),
    );

    _amountController.clear();
    _noteController.clear();
    _refController.clear();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Text('Quick Add Cash / Manual Transaction', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        const SizedBox(height: 16),

        // Type Segmented Button
        SegmentedButton<String>(
          segments: const [
            ButtonSegment(value: 'Debit', label: Text('Expense (Debit)')),
            ButtonSegment(value: 'Credit', label: Text('Income (Credit)')),
          ],
          selected: {_transType},
          onSelectionChanged: (set) => setState(() => _transType = set.first),
        ),
        const SizedBox(height: 16),

        // Amount Input
        TextField(
          controller: _amountController,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(
            labelText: 'Amount (PKR) *',
            prefixText: 'Rs. ',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 16),

        // Account Dropdown
        DropdownButtonFormField<int>(
          value: _selectedAccountId,
          decoration: const InputDecoration(labelText: 'Account / Wallet *', border: OutlineInputBorder()),
          items: _accounts.map((a) => DropdownMenuItem(value: a.id, child: Text(a.name))).toList(),
          onChanged: (val) => setState(() => _selectedAccountId = val),
        ),
        const SizedBox(height: 16),

        // Category Dropdown
        DropdownButtonFormField<int>(
          value: _selectedCategoryId,
          decoration: const InputDecoration(labelText: 'Category *', border: OutlineInputBorder()),
          items: _categories.map((c) => DropdownMenuItem(value: c.id, child: Text('${c.icon} ${c.name}'))).toList(),
          onChanged: (val) => setState(() => _selectedCategoryId = val),
        ),
        const SizedBox(height: 16),

        // Note / Merchant
        TextField(
          controller: _noteController,
          decoration: const InputDecoration(
            labelText: 'Merchant, Recipient or Note',
            hintText: 'e.g. Biryani, Grocery, ATM Cash',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 16),

        // Reference / TID
        TextField(
          controller: _refController,
          decoration: const InputDecoration(
            labelText: 'Reference / TID (Optional)',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 24),

        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF0D9488),
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
          onPressed: _saveTransaction,
          child: const Text('Save Transaction', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        ),
      ],
    );
  }
}

import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';
import 'screens/sms_parser_screen.dart';
import 'screens/ledger_screen.dart';
import 'screens/quick_add_screen.dart';
import 'services/native_bridge.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  FlutterError.onError = (details) {
    FlutterError.presentError(details);
    debugPrint('Flutter Error: ${details.exception}');
  };
  NativeBridge.initialize();
  runApp(const PakExpenseApp());
}

class PakExpenseApp extends StatelessWidget {
  const PakExpenseApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PakExpense',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      darkTheme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0F172A),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF0D9488),
          secondary: Color(0xFF14B8A6),
          surface: Color(0xFF1E293B),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0F172A),
          elevation: 0,
        ),
      ),
      home: const MainNavigationScreen(),
    );
  }
}

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({Key? key}) : super(key: key);

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;
  final GlobalKey<State> _dashboardKey = GlobalKey<State>();

  @override
  void initState() {
    super.initState();
    // Hook into Android native incoming message notifications
    NativeBridge.onMessageParsed = (parsed) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            '⚡ Auto-Logged ${parsed.provider} ${parsed.transType}: Rs. ${parsed.amount.toStringAsFixed(2)}',
          ),
          backgroundColor: Colors.teal,
        ),
      );
      setState(() {});
    };
  }

  void _triggerRefresh() {
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      const DashboardScreen(),
      SmsParserScreen(onDataChanged: _triggerRefresh),
      LedgerScreen(onDataChanged: _triggerRefresh),
      QuickAddScreen(onDataChanged: _triggerRefresh),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: const [
            Text('🇵🇰 PakExpense', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 19)),
            SizedBox(width: 8),
            Text(
              'JazzCash • EasyPaisa • Meezan',
              style: TextStyle(fontSize: 10, color: Colors.grey),
            ),
          ],
        ),
      ),
      body: screens[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (idx) => setState(() => _currentIndex = idx),
        backgroundColor: const Color(0xFF1E293B),
        indicatorColor: const Color(0xFF0D9488).withOpacity(0.3),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard, color: Color(0xFF14B8A6)), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.bolt_outlined), selectedIcon: Icon(Icons.bolt, color: Color(0xFF14B8A6)), label: 'SMS & Push'),
          NavigationDestination(icon: Icon(Icons.receipt_long_outlined), selectedIcon: Icon(Icons.receipt_long, color: Color(0xFF14B8A6)), label: 'Ledger'),
          NavigationDestination(icon: Icon(Icons.add_circle_outline), selectedIcon: Icon(Icons.add_circle, color: Color(0xFF14B8A6)), label: 'Quick Add'),
        ],
      ),
    );
  }
}

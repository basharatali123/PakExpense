# 📱 PakExpense Flutter Android App (`.apk`)

A native Android mobile application for tracking and consolidating transactions from:
- **JazzCash** (SMS Shortcode `8558`)
- **Meezan Bank** (SMS Shortcode `8079`)
- **EasyPaisa** (In-App Push Notifications & Shortcode `3737`)
- **Cash Wallet** & manual expense entry

---

## 🏗️ Architecture & How Auto-Reading Works

### 1. JazzCash (`8558`) & Meezan Bank (`8079`) SMS
- Handled by native Android `SmsReceiver.kt` declared with `RECEIVE_SMS` permission in `AndroidManifest.xml`.
- When an SMS arrives from `8558` or `8079`, the receiver intercepts it in the background, extracts the text, and delivers it to the Flutter parsing engine.

### 2. EasyPaisa In-App Push Notifications
- EasyPaisa does not send traditional SMS for most payments; instead, it sends an in-app push notification.
- Handled by `EasyPaisaNotificationListener.kt` (Android `NotificationListenerService`).
- Intercepts incoming push alerts from `com.telenor.pakistan.easypaisa`, extracts the title and amount, and saves it directly to the local SQLite database.

### 3. Local SQLite Database (`sqflite`)
- Stored directly on your Android phone's private storage (`pak_finance.db`).
- Works 100% offline with zero cloud latency.

---

## 🚀 How to Build the `.apk` File

### Method A: Automated Cloud Build (Recommended — No Setup Needed!)
We included a GitHub Actions workflow in `.github/workflows/build_apk.yml`:
1. Push this folder to your GitHub account (public or private repository).
2. Go to the **Actions** tab on GitHub.
3. It will automatically compile `app-release.apk` in ~2 minutes.
4. Download `app-release.apk` directly to your phone and tap **Install**!

### Method B: Build Locally with Flutter SDK
If you have Flutter installed on your PC:
```bash
cd flutter_app
flutter pub get
flutter build apk --release
```
The output `.apk` file will be created at:
```
flutter_app/build/app/outputs/flutter-apk/app-release.apk
```

---

## 📲 Setup on Your Android Phone After Installing `.apk`

1. **SMS Permission**:
   - When you open the app, tap **Allow** when Android asks for SMS permissions (so it can read JazzCash `8558` and Meezan `8079`).
2. **EasyPaisa Notification Access**:
   - Go to the **SMS & Push** tab in the app.
   - Tap **"Grant Access"**.
   - Android will open the **Device & App Notifications** settings screen.
   - Find **PakExpense** and toggle it **ON**.
3. **Done!**
   - Whenever you pay a Daewoo ticket, get charged at Jinnah Pharmacy, withdraw cash from an ATM, or receive money via Raast, PakExpense will automatically catch it and update your Net Worth and balances!

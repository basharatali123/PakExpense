package com.pakexpense.app

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log

class EasyPaisaNotificationListener : NotificationListenerService() {
    companion object {
        const val TAG = "EasyPaisaNotifListener"
        // EasyPaisa Android package name
        const val EASYPAISA_PACKAGE = "com.telenor.pakistan.easypaisa"
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        if (sbn == null) return

        val packageName = sbn.packageName ?: ""
        val extras = sbn.notification?.extras ?: return

        val title = extras.getString("android.title") ?: ""
        val text = extras.getCharSequence("android.text")?.toString() ?: ""

        Log.d(TAG, "Notification received from package: $packageName | Title: $title")

        // Intercept if from EasyPaisa or if title/body contains EasyPaisa transfer keywords
        val isEasyPaisa = packageName.equals(EASYPAISA_PACKAGE, ignoreCase = true) ||
            title.contains("easypaisa", ignoreCase = true) ||
            text.contains("easypaisa", ignoreCase = true)

        if (isEasyPaisa && text.isNotEmpty()) {
            val combinedText = "$title: $text"
            Log.d(TAG, "Captured EasyPaisa Push Notification! Forwarding to Flutter...")
            MainActivity.sendNotificationToFlutter(combinedText, "EasyPaisa")
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
        // Not needed for expense logging
    }
}

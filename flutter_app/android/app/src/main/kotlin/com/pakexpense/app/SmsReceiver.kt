package com.pakexpense.app

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.util.Log

class SmsReceiver : BroadcastReceiver() {
    companion object {
        const val TAG = "PakExpenseSmsReceiver"
        val PAK_SHORTCODES = listOf("8558", "8079", "3737", "8267", "4250", "8222")
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
            if (messages.isNullOrEmpty()) return

            val fullBody = StringBuilder()
            var sender = ""

            for (sms in messages) {
                fullBody.append(sms.messageBody)
                sender = sms.originatingAddress ?: ""
            }

            val cleanSender = sender.trim().lowercase()
            val cleanBody = fullBody.toString()

            Log.d(TAG, "Incoming SMS from: $cleanSender")

            // Check if sender matches Pakistani financial providers
            val isPakFinancial = PAK_SHORTCODES.any { cleanSender.contains(it) } ||
                cleanBody.contains("jazzcash", ignoreCase = true) ||
                cleanBody.contains("easypaisa", ignoreCase = true) ||
                cleanBody.contains("meezan", ignoreCase = true)

            if (isPakFinancial) {
                Log.d(TAG, "Captured Pakistani Financial SMS! Forwarding to Flutter...")
                MainActivity.sendSmsToFlutter(cleanBody, sender)
            }
        }
    }
}

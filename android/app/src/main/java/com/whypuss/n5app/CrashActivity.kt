package com.whypuss.n5app

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.os.Bundle
import android.widget.Button
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class CrashActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val crash = intent.getStringExtra("crash") ?: "Unknown crash"
        val fullLog = App.getAllLogs()

        setContentView(R.layout.activity_crash)

        findViewById<TextView>(R.id.crashLog).text = crash
        findViewById<TextView>(R.id.fullLog).text = fullLog

        findViewById<Button>(R.id.copyBtn).setOnClickListener {
            (getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager)
                .setPrimaryClip(ClipData.newPlainText("log", fullLog))
            Toast.makeText(this, "Copied!", Toast.LENGTH_SHORT).show()
        }
    }
}

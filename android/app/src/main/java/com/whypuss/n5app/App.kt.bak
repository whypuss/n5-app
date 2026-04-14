package com.whypuss.n5app

import android.app.Activity
import android.app.Application
import android.content.Intent
import android.os.Build
import android.widget.Toast
import java.io.PrintWriter
import java.io.StringWriter
import java.text.SimpleDateFormat
import java.util.*

class App : Application() {
    companion object {
        val logs = mutableListOf<LogEntry>()
        private const val MAX = 200

        data class LogEntry(val time: String, val tag: String, val msg: String, val level: String)
        private val tf = SimpleDateFormat("HH:mm:ss.SSS", Locale.US)

        fun d(tag: String, msg: String) = log("D", tag, msg)
        fun e(tag: String, msg: String) = log("E", tag, msg)
        private fun log(level: String, tag: String, msg: String) {
            synchronized(logs) {
                logs.add(LogEntry(tf.format(Date()), tag, msg, level))
                if (logs.size > MAX) logs.removeAt(0)
            }
            android.util.Log.println(
                when (level) { "D" -> android.util.Log.DEBUG else -> android.util.Log.ERROR
                }, tag, msg
            )
        }

        fun getAllLogs(): String {
            return buildString {
                append("═══ N5-App Logs ═══\n")
                append("Device: ${Build.MANUFACTURER} ${Build.MODEL}\n")
                append("Android: ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})\n\n")
                synchronized(logs) { logs.forEach { append("[${it.time}] ${it.level}/${it.tag}: ${it.msg}\n") } }
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        d("App", "N5-App starting...")

        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            val sw = StringWriter()
            throwable.printStackTrace(PrintWriter(sw))
            e("CRASH", "═══ CRASH ═══\n${throwable.javaClass.simpleName}: ${throwable.message}\n${sw}")
            try {
                startActivity(Intent(this, CrashActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    putExtra("crash", "${throwable.javaClass.simpleName}: ${throwable.message}\n${sw}")
                })
            } catch (ignored: Exception) {}
            java.lang.Process.killProcess(android.os.Process.myPid())
        }

        e("App", "Handler installed, ready")
    }
}

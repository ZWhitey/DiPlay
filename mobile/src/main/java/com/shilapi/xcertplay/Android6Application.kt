package com.shilapi.xcertplay

import android.app.Application
import android.os.Build
import java.io.File

/** Keep a local startup crash trace accessible to old head-unit file managers. */
class Android6Application : Application() {
    override fun onCreate() {
        super.onCreate()
        val previous = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, error ->
            try {
                val directory = getExternalFilesDir(null) ?: filesDir
                File(directory, "last-crash.txt").writeText(
                    "DiPlay Android 6 fix2\nSDK=${Build.VERSION.SDK_INT}\n" +
                        "Device=${Build.MANUFACTURER} ${Build.MODEL}\n" +
                        "Thread=${thread.name}\n" + error.stackTraceToString()
                )
            } catch (_: Throwable) { /* Preserve Android's original crash handling. */ }
            if (previous != null) previous.uncaughtException(thread, error)
            else {
                android.os.Process.killProcess(android.os.Process.myPid())
                kotlin.system.exitProcess(10)
            }
        }
    }
}

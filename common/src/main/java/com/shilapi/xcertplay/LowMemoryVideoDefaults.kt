package com.shilapi.xcertplay

import android.app.ActivityManager
import android.content.Context
import android.os.Build

internal object LowMemoryVideoDefaults {
    fun directOutput(context: Context): Boolean {
        if (Build.VERSION.SDK_INT > 23) return false
        return runCatching {
            val manager = context.getSystemService(Context.ACTIVITY_SERVICE) as? ActivityManager ?: return false
            val memory = ActivityManager.MemoryInfo()
            manager.getMemoryInfo(memory)
            manager.isLowRamDevice || memory.totalMem in 1..(1536L * 1024 * 1024)
        }.getOrDefault(false)
    }
}

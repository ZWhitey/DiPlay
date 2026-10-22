package com.shilapi.xcertplay

import android.app.ActivityManager
import android.content.Context
import android.media.MediaFormat
import android.os.Build
import com.shilapi.xcertplay.media.MtkDecoderTuning

/** Video defaults for Android 6 head units with little memory; a saved preference always wins. */
internal object LowMemoryVideoDefaults {
    fun directOutput(context: Context): Boolean = lowMemoryAndroid6(context)

    /** Old MTK OMX decoders hold frames back for reordering unless asked not to; falls back on refusal. */
    fun mtkDecoderTuning(context: Context): Boolean = lowMemoryAndroid6(context) &&
        MtkDecoderTuning.legacyAcodecDecoderName(MediaFormat.MIMETYPE_VIDEO_AVC) != null

    private fun lowMemoryAndroid6(context: Context): Boolean {
        if (Build.VERSION.SDK_INT > Build.VERSION_CODES.M) return false
        return runCatching {
            val manager = context.getSystemService(Context.ACTIVITY_SERVICE) as? ActivityManager ?: return false
            val memory = ActivityManager.MemoryInfo()
            manager.getMemoryInfo(memory)
            manager.isLowRamDevice || memory.totalMem in 1..(1536L * 1024 * 1024)
        }.getOrDefault(false)
    }
}

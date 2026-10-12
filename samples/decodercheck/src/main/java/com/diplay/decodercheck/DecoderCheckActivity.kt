package com.diplay.decodercheck

import android.app.Activity
import android.media.MediaExtractor
import android.os.Bundle
import android.util.Log
import android.view.Surface
import android.view.SurfaceHolder
import android.view.SurfaceView
import com.shilapi.xcertplay.airplay.AirPlayCrypto
import com.shilapi.xcertplay.airplay.VideoCodec
import com.shilapi.xcertplay.media.AndroidMediaSink
import java.nio.ByteBuffer
import java.util.Collections
import java.util.concurrent.atomic.AtomicBoolean
import org.json.JSONArray
import org.json.JSONObject

/** Standalone test app using the production shared decoder, not a replacement player. */
class DecoderCheckActivity : Activity(), SurfaceHolder.Callback {
    private val started = AtomicBoolean(false)
    private val cancelled = AtomicBoolean(false)
    private val diagnostics = Collections.synchronizedList(mutableListOf<String>())
    private var sink: AndroidMediaSink? = null

    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        val view = SurfaceView(this)
        view.holder.addCallback(this)
        setContentView(view)
    }
    override fun surfaceCreated(holder: SurfaceHolder) {
        if (started.compareAndSet(false, true)) Thread { test(holder.surface) }.start()
    }
    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) = Unit
    override fun surfaceDestroyed(holder: SurfaceHolder) { cancelled.set(true); sink?.close() }

    private fun raw(buffer: ByteBuffer): ByteArray {
        val bytes = ByteArray(buffer.remaining()).also { buffer.duplicate().get(it) }
        val prefix = if (bytes.size >= 4 && bytes[2] == 0.toByte()) 4 else 3
        return bytes.copyOfRange(prefix, bytes.size)
    }
    private fun test(surface: Surface) {
        val result = JSONObject().put("width", 800).put("height", 480)
            .put("target_frames", 90).put("tail_frames", 6).put("fixture_fps", 30).put("feed_fps", 10).put("device_fps_claim", false)
        val extractor = MediaExtractor()
        try {
            val input = getFileStreamPath("pattern.mp4")
            assets.open("pattern.mp4").use { source -> input.outputStream().use { source.copyTo(it) } }
            extractor.setDataSource(input.path)
            extractor.selectTrack(0)
            val format = extractor.getTrackFormat(0)
            val sps = raw(checkNotNull(format.getByteBuffer("csd-0")))
            val pps = raw(checkNotNull(format.getByteBuffer("csd-1")))
            val config = byteArrayOf(1, sps[1], sps[2], sps[3], -1, -31,
                (sps.size shr 8).toByte(), sps.size.toByte()) + sps +
                byteArrayOf(1, (pps.size shr 8).toByte(), pps.size.toByte()) + pps
            val decoder = AndroidMediaSink(surface = surface, videoWidth = 800, videoHeight = 480,
                context = this, mainVideoFrameRate = 30)
            sink = decoder
            decoder.setVideoDiagnosticHandler(110) { line -> diagnostics.add(line); Log.i("DecoderCheck", line) }
            decoder.onVideoCodec(110, VideoCodec.H264)
            decoder.onVideoConfig(110, config)
            val buffer = ByteBuffer.allocate(1024 * 1024)
            val key = ByteArray(32) { it.toByte() }
            val aad = ByteArray(128)
            var submitted = 0
            while (!cancelled.get()) {
                buffer.clear()
                val length = extractor.readSampleData(buffer, 0)
                if (length < 0) break
                val frame = ByteArray(length)
                buffer.position(0); buffer.get(frame)
                val nonce = AirPlayCrypto.nonce64(submitted.toLong())
                val encrypted = AirPlayCrypto.chachaSeal(key, nonce, frame, aad)
                val decoded = AirPlayCrypto.chachaOpen(key, nonce, encrypted, aad)
                check(frame.contentEquals(decoded)) { "Frame crypto mismatch" }
                decoder.onVideoFrame(110, decoded)
                submitted++
                extractor.advance()
                Thread.sleep(100) // Functional test: do not claim a TCG throughput benchmark.
            }
            val deadline = System.nanoTime() + 120_000_000_000L
            while (!cancelled.get() && System.nanoTime() < deadline &&
                (decoder.liveVideoCounters()?.rendered ?: 0) < 90) Thread.sleep(100)
            val counters = decoder.liveVideoCounters()
            result.put("submitted", submitted).put("received", counters?.received ?: 0)
                .put("rendered", counters?.rendered ?: 0).put("crypto_provider", AirPlayCrypto.chachaImplementation)
                .put("buffered_tail", submitted - (counters?.rendered ?: 0))
                .put("passed", submitted == 96 && (counters?.rendered ?: 0) >= 90 &&
                    diagnostics.none { it.contains("failed", ignoreCase = true) })
        } catch (failure: Throwable) {
            result.put("passed", false).put("error", Log.getStackTraceString(failure))
        } finally {
            extractor.release()
            val current = sink
            current?.close()
            result.put("decoder_released", current?.awaitVideoReleased(10_000) ?: true)
            result.put("diagnostics", JSONArray(diagnostics.toList()))
            getFileStreamPath("result.json").writeText(result.toString(2))
            Log.i("DecoderCheck", "RESULT $result")
        }
    }
}

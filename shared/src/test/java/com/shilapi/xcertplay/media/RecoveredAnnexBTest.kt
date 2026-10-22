package com.shilapi.xcertplay.media

import java.nio.ByteBuffer
import org.junit.Assert.*
import org.junit.Test

class RecoveredAnnexBTest {
    @Test fun malformedTailDoesNotPartiallyWrite() {
        val target = ByteBuffer.allocate(20)
        target.position(3)
        // An Annex B prefix is ambiguous with a one-byte length. Use an unambiguous length below.
        val malformed = byteArrayOf(0, 0, 0, 2, 65, 66, 0)
        target.position(3)
        assertFalse(MediaCodecSupport.putAnnexB(malformed, target))
        assertEquals(3, target.position())
    }
    @Test fun heapAndDirectBuffersProduceTheSameOutput() {
        val bytes = byteArrayOf(0, 0, 0, 2, 65, 66, 0, 0, 0, 2, 67, 68)
        val expected = byteArrayOf(0, 0, 0, 1, 65, 66, 0, 0, 0, 1, 67, 68)
        for (buffer in listOf(ByteBuffer.allocate(12), ByteBuffer.allocateDirect(12))) {
            assertTrue(MediaCodecSupport.putAnnexB(bytes, buffer))
            buffer.flip()
            val result = ByteArray(12)
            buffer.get(result)
            assertArrayEquals(expected, result)
        }
    }
    @Test fun aLengthOf256To511IsNotTakenForAStartCode() {
        // A 300-byte NAL's prefix 00 00 01 2C starts like a 3-byte start code.
        val nal = ByteArray(300) { 65 }
        val bytes = byteArrayOf(0, 0, 1, 44) + nal
        assertArrayEquals(byteArrayOf(0, 0, 0, 1) + nal, MediaCodecSupport.toAnnexB(bytes))
    }
    @Test fun insufficientCapacityPreservesPosition() {
        val buffer = ByteBuffer.allocate(5)
        assertFalse(MediaCodecSupport.putAnnexB(byteArrayOf(0, 0, 0, 2, 65, 66), buffer))
        assertEquals(0, buffer.position())
    }
}

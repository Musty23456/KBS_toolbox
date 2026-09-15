package com.kbstoolbox.app.util

import android.content.Context
import android.media.MediaRecorder
import android.os.Build
import java.io.File

/** Thin wrapper around MediaRecorder for short voice-note answers. */
class AudioRecorder(private val context: Context) {
    private var recorder: MediaRecorder? = null
    private var outputFile: File? = null

    fun start(): File {
        val file = MediaFiles.newAudioFile(context)
        outputFile = file

        val mediaRecorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(context)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }

        mediaRecorder.apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            setOutputFile(file.absolutePath)
            prepare()
            start()
        }
        recorder = mediaRecorder
        return file
    }

    /** Returns the recorded file, or null if nothing was recording. */
    fun stop(): File? {
        return try {
            recorder?.apply {
                stop()
                release()
            }
            outputFile
        } catch (e: Exception) {
            null
        } finally {
            recorder = null
        }
    }

    fun cancel() {
        try {
            recorder?.apply {
                stop()
                release()
            }
        } catch (e: Exception) {
            // Recorder may not have produced valid output if stopped too early; ignore.
        }
        outputFile?.delete()
        recorder = null
        outputFile = null
    }
}

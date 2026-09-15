package com.kbstoolbox.app.util

import android.content.Context
import android.net.Uri
import androidx.core.content.FileProvider
import java.io.File
import java.util.UUID

/**
 * Every captured media answer (photo/audio/signature) is written under the
 * app's own external-files "captures" directory, which survives app restarts
 * and is not world-readable. The submission stores only the file's absolute
 * path as its `media_reference` string — matching the backend's design,
 * which treats media_reference as an opaque reference rather than binary
 * data (see backend README's "known limitations" on media upload).
 */
object MediaFiles {

    private fun capturesDir(context: Context): File {
        val dir = File(context.getExternalFilesDir(null), "captures")
        if (!dir.exists()) dir.mkdirs()
        return dir
    }

    fun newPhotoFile(context: Context): File =
        File(capturesDir(context), "photo_${UUID.randomUUID()}.jpg")

    fun newAudioFile(context: Context): File =
        File(capturesDir(context), "audio_${UUID.randomUUID()}.m4a")

    fun newSignatureFile(context: Context): File =
        File(capturesDir(context), "signature_${UUID.randomUUID()}.png")

    fun uriForFile(context: Context, file: File): Uri =
        FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
}

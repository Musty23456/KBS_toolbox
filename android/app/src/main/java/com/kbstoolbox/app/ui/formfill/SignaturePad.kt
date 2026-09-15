package com.kbstoolbox.app.ui.formfill

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import androidx.compose.foundation.Canvas as ComposeCanvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color as ComposeColor
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.asAndroidPath
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.kbstoolbox.app.util.MediaFiles
import java.io.FileOutputStream

@Composable
fun SignaturePad(onSigned: (filePath: String) -> Unit) {
    val context = LocalContext.current
    val paths = remember { mutableStateListOf<Path>() }
    var currentPath by remember { mutableStateOf(Path()) }

    Column {
        ComposeCanvas(
            modifier = Modifier
                .fillMaxWidth()
                .height(180.dp)
                .background(ComposeColor.White)
                .border(1.dp, ComposeColor.Gray)
                .pointerInput(Unit) {
                    detectDragGestures(
                        onDragStart = { offset ->
                            currentPath = Path().apply { moveTo(offset.x, offset.y) }
                        },
                        onDrag = { change, _ ->
                            currentPath.lineTo(change.position.x, change.position.y)
                            change.consume()
                        },
                        onDragEnd = {
                            paths.add(currentPath)
                            currentPath = Path()
                        }
                    )
                }
        ) {
            (paths + currentPath).forEach { path ->
                drawPath(path, color = ComposeColor.Black, style = Stroke(width = 5f))
            }
        }

        Button(
            onClick = {
                val bitmap = renderSignatureBitmap(paths, width = 800, height = 300)
                val file = MediaFiles.newSignatureFile(context)
                FileOutputStream(file).use { out -> bitmap.compress(Bitmap.CompressFormat.PNG, 100, out) }
                onSigned(file.absolutePath)
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Save signature")
        }

        Button(
            onClick = {
                paths.clear()
                currentPath = Path()
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Clear")
        }
    }
}

private fun renderSignatureBitmap(paths: List<Path>, width: Int, height: Int): Bitmap {
    val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
    val canvas = Canvas(bitmap)
    canvas.drawColor(Color.WHITE)
    val paint = Paint().apply {
        color = Color.BLACK
        style = Paint.Style.STROKE
        strokeWidth = 6f
        isAntiAlias = true
    }
    paths.forEach { composePath ->
        canvas.drawPath(composePath.asAndroidPath(), paint)
    }
    return bitmap
}

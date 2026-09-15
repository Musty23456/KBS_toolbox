package com.kbstoolbox.app.ui.formfill

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Checkbox
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.kbstoolbox.app.data.local.entity.ChoiceEntity
import com.kbstoolbox.app.data.local.entity.QuestionEntity

@Composable
fun QuestionField(
    question: QuestionEntity,
    index: Int,
    value: String?,
    mediaValue: String?,
    choices: List<ChoiceEntity>,
    errorMessage: String?,
    onTextChange: (String) -> Unit,
    onMultiToggle: (choiceValue: String, checked: Boolean) -> Unit,
    onCaptureGps: () -> Unit,
    onCapturePhoto: () -> Unit,
    onStartAudio: () -> Unit,
    onStopAudio: () -> Unit,
    isRecordingAudio: Boolean,
    onSignatureSaved: (String) -> Unit,
    onScanBarcode: () -> Unit
) {
    Card(modifier = Modifier
        .fillMaxWidth()
        .padding(bottom = 16.dp)) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "${index + 1}. ${question.label}${if (question.isRequired) " *" else ""}",
                style = MaterialTheme.typography.titleLarge
            )
            question.hint?.takeIf { it.isNotBlank() }?.let {
                Text(it, style = MaterialTheme.typography.bodyMedium)
            }

            when (question.type) {
                "SHORT_TEXT" -> TextInput(value, onTextChange, singleLine = true, keyboardType = KeyboardType.Text)
                "LONG_TEXT" -> TextInput(value, onTextChange, singleLine = false, keyboardType = KeyboardType.Text)
                "INTEGER" -> TextInput(value, onTextChange, singleLine = true, keyboardType = KeyboardType.Number)
                "DECIMAL" -> TextInput(value, onTextChange, singleLine = true, keyboardType = KeyboardType.Decimal)
                "DATE" -> TextInput(value, onTextChange, singleLine = true, keyboardType = KeyboardType.Text, placeholder = "YYYY-MM-DD")
                "TIME" -> TextInput(value, onTextChange, singleLine = true, keyboardType = KeyboardType.Text, placeholder = "HH:MM")
                "DATETIME" -> TextInput(value, onTextChange, singleLine = true, keyboardType = KeyboardType.Text, placeholder = "YYYY-MM-DD HH:MM")
                "YES_NO" -> YesNoField(value, onTextChange)
                "SINGLE_CHOICE" -> SingleChoiceField(choices, value, onTextChange)
                "DROPDOWN" -> DropdownField(choices, value, onTextChange)
                "MULTIPLE_CHOICE" -> MultipleChoiceField(choices, value, onMultiToggle)
                "GPS" -> GpsField(value, onCaptureGps)
                "PHOTO" -> MediaCaptureField(mediaValue, "Take photo", onCapturePhoto)
                "SIGNATURE" -> SignaturePad(onSigned = onSignatureSaved)
                "AUDIO" -> AudioField(mediaValue, isRecordingAudio, onStartAudio, onStopAudio)
                "BARCODE" -> MediaCaptureField(value, "Scan barcode / QR", onScanBarcode)
                else -> Text("Unsupported question type: ${question.type}")
            }

            errorMessage?.let {
                Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

@Composable
private fun TextInput(
    value: String?,
    onChange: (String) -> Unit,
    singleLine: Boolean,
    keyboardType: KeyboardType,
    placeholder: String? = null
) {
    OutlinedTextField(
        value = value ?: "",
        onValueChange = onChange,
        singleLine = singleLine,
        keyboardOptions = KeyboardOptions(keyboardType = keyboardType),
        placeholder = placeholder?.let { { Text(it) } },
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 8.dp)
    )
}

@Composable
private fun YesNoField(value: String?, onChange: (String) -> Unit) {
    Row(modifier = Modifier.padding(top = 8.dp)) {
        listOf("YES", "NO").forEach { option ->
            Row(
                modifier = Modifier
                    .selectable(selected = value == option, onClick = { onChange(option) })
                    .padding(end = 24.dp)
            ) {
                RadioButton(selected = value == option, onClick = { onChange(option) })
                Text(option, modifier = Modifier.padding(start = 4.dp, top = 12.dp))
            }
        }
    }
}

@Composable
private fun SingleChoiceField(choices: List<ChoiceEntity>, value: String?, onChange: (String) -> Unit) {
    Column(modifier = Modifier.padding(top = 8.dp)) {
        choices.forEach { choice ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .selectable(selected = value == choice.value, onClick = { onChange(choice.value) })
            ) {
                RadioButton(selected = value == choice.value, onClick = { onChange(choice.value) })
                Text(choice.label, modifier = Modifier.padding(start = 4.dp, top = 12.dp))
            }
        }
    }
}

@Composable
private fun MultipleChoiceField(choices: List<ChoiceEntity>, value: String?, onToggle: (String, Boolean) -> Unit) {
    val selected = value?.split("|")?.toSet() ?: emptySet()
    Column(modifier = Modifier.padding(top = 8.dp)) {
        choices.forEach { choice ->
            Row(modifier = Modifier.fillMaxWidth()) {
                Checkbox(
                    checked = selected.contains(choice.value),
                    onCheckedChange = { checked -> onToggle(choice.value, checked) }
                )
                Text(choice.label, modifier = Modifier.padding(start = 4.dp, top = 12.dp))
            }
        }
    }
}

@Composable
private fun DropdownField(choices: List<ChoiceEntity>, value: String?, onChange: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    val selectedLabel = choices.firstOrNull { it.value == value }?.label ?: ""

    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = it },
        modifier = Modifier.padding(top = 8.dp)
    ) {
        OutlinedTextField(
            value = selectedLabel,
            onValueChange = {},
            readOnly = true,
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            modifier = Modifier
                .fillMaxWidth()
                .menuAnchor()
        )
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            choices.forEach { choice ->
                DropdownMenuItem(text = { Text(choice.label) }, onClick = {
                    onChange(choice.value)
                    expanded = false
                })
            }
        }
    }
}

@Composable
private fun GpsField(value: String?, onCapture: () -> Unit) {
    Column(modifier = Modifier.padding(top = 8.dp)) {
        Text(value?.let { "Captured: $it" } ?: "No location captured yet.", style = MaterialTheme.typography.bodyMedium)
        Button(onClick = onCapture, modifier = Modifier.padding(top = 8.dp)) {
            Text("Capture current location")
        }
    }
}

@Composable
private fun MediaCaptureField(reference: String?, actionLabel: String, onCapture: () -> Unit) {
    Column(modifier = Modifier.padding(top = 8.dp)) {
        Text(reference?.let { "Captured" } ?: "Not captured yet.", style = MaterialTheme.typography.bodyMedium)
        Button(onClick = onCapture, modifier = Modifier.padding(top = 8.dp)) {
            Text(actionLabel)
        }
    }
}

@Composable
private fun AudioField(reference: String?, isRecording: Boolean, onStart: () -> Unit, onStop: () -> Unit) {
    Column(modifier = Modifier.padding(top = 8.dp)) {
        Text(
            when {
                isRecording -> "Recording…"
                reference != null -> "Recording saved."
                else -> "No recording yet."
            },
            style = MaterialTheme.typography.bodyMedium
        )
        Button(onClick = if (isRecording) onStop else onStart, modifier = Modifier.padding(top = 8.dp)) {
            Text(if (isRecording) "Stop recording" else "Start recording")
        }
    }
}

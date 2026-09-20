package com.kbstoolbox.app.ui.formfill

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import com.kbstoolbox.app.di.ServiceLocator
import com.kbstoolbox.app.util.AudioRecorder
import com.kbstoolbox.app.util.LocationCapture
import com.kbstoolbox.app.util.MediaFiles
import com.kbstoolbox.app.util.ViewModelFactory
import kotlinx.coroutines.launch

@Composable
fun FormFillScreen(surveyId: String, submissionUuid: String, onDone: () -> Unit) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    val viewModel: FormFillViewModel = viewModel(
        factory = ViewModelFactory {
            FormFillViewModel(
                ServiceLocator.surveyRepository(context),
                ServiceLocator.submissionRepository(context),
                context.applicationContext
            )
        }
    )
    val state by viewModel.uiState.collectAsState()

    LaunchedEffect(surveyId, submissionUuid) {
        viewModel.load(surveyId, submissionUuid.ifBlank { null })
    }

    LaunchedEffect(state.isSubmitted) {
        if (state.isSubmitted) onDone()
    }

    // --- Capture plumbing shared across all questions on this screen ---
    var pendingPhotoQuestionId by remember { mutableStateOf<String?>(null) }
    var pendingPhotoUri by remember { mutableStateOf<android.net.Uri?>(null) }
    var pendingBarcodeQuestionId by remember { mutableStateOf<String?>(null) }
    var pendingGpsQuestionId by remember { mutableStateOf<String?>(null) }
    var recordingQuestionId by remember { mutableStateOf<String?>(null) }
    val audioRecorder = remember { AudioRecorder(context) }

    val cameraPermissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { }
    val locationPermissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        val questionId = pendingGpsQuestionId
        if (granted && questionId != null) {
            coroutineScope.launch {
                val location = LocationCapture.captureCurrentLocation(context)
                if (location != null) {
                    viewModel.onGpsCaptured(questionId, location.latitude, location.longitude)
                }
            }
        }
    }
    val audioPermissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        val questionId = recordingQuestionId
        if (granted && questionId != null) {
            audioRecorder.start()
        } else {
            recordingQuestionId = null
        }
    }

    val takePictureLauncher = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        val questionId = pendingPhotoQuestionId
        val uri = pendingPhotoUri
        if (success && questionId != null && uri != null) {
            viewModel.setMediaAnswer(questionId, uri.path ?: uri.toString())
        }
        pendingPhotoQuestionId = null
        pendingPhotoUri = null
    }

    val barcodeLauncher = rememberLauncherForActivityResult(ScanContract()) { result ->
        val questionId = pendingBarcodeQuestionId
        if (questionId != null && result.contents != null) {
            viewModel.updateTextAnswer(questionId, result.contents)
        }
        pendingBarcodeQuestionId = null
    }

    Scaffold(
        topBar = { TopAppBar(title = { Text(state.surveyTitle.ifBlank { "Survey" }) }) }
    ) { padding ->
        if (state.isLoading) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                verticalArrangement = Arrangement.Center,
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                CircularProgressIndicator()
            }
            return@Scaffold
        }

        state.errorMessage?.takeIf { state.questions.isEmpty() }?.let {
            Column(modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp)) {
                Text(it, style = MaterialTheme.typography.titleLarge)
            }
            return@Scaffold
        }

        Column(modifier = Modifier
            .fillMaxSize()
            .padding(padding)) {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
                    .weight(1f)
            ) {
                items(state.visibleQuestions, key = { "q:${it.id}" }) { question ->
                    RenderQuestion(
                        question = question, instanceIndex = null, index = state.questions.indexOf(question),
                        state = state, viewModel = viewModel, context = context, coroutineScope = coroutineScope,
                        pendingGpsQuestionId = { pendingGpsQuestionId = it },
                        pendingPhoto = { qid, uri -> pendingPhotoQuestionId = qid; pendingPhotoUri = uri },
                        setBarcode = { pendingBarcodeQuestionId = it },
                        setRecording = { recordingQuestionId = it },
                        recordingQuestionId = recordingQuestionId,
                        audioRecorder = audioRecorder,
                        onCaptureLocation = { qid, instance ->
                            pendingGpsQuestionId = qid
                            val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                            if (granted) coroutineScope.launch {
                                val location = LocationCapture.captureCurrentLocation(context)
                                if (location != null) viewModel.onGpsCaptured(qid, location.latitude, location.longitude, instance)
                            } else locationPermissionLauncher.launch(Manifest.permission.ACCESS_FINE_LOCATION)
                        },
                        onTakePhoto = { qid, instance ->
                            val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
                            if (!granted) cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
                            val file = MediaFiles.newPhotoFile(context)
                            val uri = MediaFiles.uriForFile(context, file)
                            pendingPhotoQuestionId = qid
                            pendingPhotoUri = uri
                            takePictureLauncher.launch(uri)
                        },
                        onStartAudio = { qid ->
                            recordingQuestionId = qid
                            val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED
                            if (granted) audioRecorder.start() else audioPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                        },
                        onStopAudio = { qid, instance ->
                            val file = audioRecorder.stop()
                            recordingQuestionId = null
                            if (file != null) viewModel.setMediaAnswer(qid, file.absolutePath, instance)
                        },
                        onSignature = { qid, path, instance -> viewModel.setMediaAnswer(qid, path, instance) },
                        onScan = { qid ->
                            pendingBarcodeQuestionId = qid
                            barcodeLauncher.launch(ScanOptions().setBeepEnabled(false).setOrientationLocked(false))
                        }
                    )
                }

                state.groups.sortedBy { it.orderIndex }.forEach { group ->
                    item(key = "group:${group.id}") {
                        androidx.compose.material3.Card(modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text(group.title, style = MaterialTheme.typography.headlineSmall)
                                group.description?.takeIf { it.isNotBlank() }?.let { Text(it, style = MaterialTheme.typography.bodyMedium) }
                                Text(
                                    if (group.repeatable) "${state.groupInstances[group.id]?.size ?: 1} record(s)" else "One record",
                                    style = MaterialTheme.typography.labelLarge,
                                    modifier = Modifier.padding(top = 6.dp)
                                )
                            }
                        }
                    }

                    val instances = state.groupInstances[group.id] ?: listOf(0)
                    instances.forEach { instance ->
                        val groupQuestions = state.questions.filter { it.groupId == group.id && state.isVisible(it, instance) }.sortedBy { it.orderIndex }
                        item(key = "instance:${group.id}:$instance") {
                            Column(modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)) {
                                androidx.compose.material3.Text(
                                    "${group.title} — ${instance + 1}",
                                    style = MaterialTheme.typography.titleMedium,
                                    modifier = Modifier.padding(vertical = 8.dp)
                                )
                                groupQuestions.forEachIndexed { localIndex, question ->
                                    RenderQuestion(
                                        question = question, instanceIndex = instance, index = localIndex,
                                        state = state, viewModel = viewModel, context = context, coroutineScope = coroutineScope,
                                        pendingGpsQuestionId = { pendingGpsQuestionId = it },
                                        pendingPhoto = { qid, uri -> pendingPhotoQuestionId = qid; pendingPhotoUri = uri },
                                        setBarcode = { pendingBarcodeQuestionId = it },
                                        setRecording = { recordingQuestionId = it },
                                        recordingQuestionId = recordingQuestionId, audioRecorder = audioRecorder,
                                        onCaptureLocation = { qid, inst ->
                                            pendingGpsQuestionId = qid
                                            val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                                            if (granted) coroutineScope.launch {
                                                val location = LocationCapture.captureCurrentLocation(context)
                                                if (location != null) viewModel.onGpsCaptured(qid, location.latitude, location.longitude, inst)
                                            } else locationPermissionLauncher.launch(Manifest.permission.ACCESS_FINE_LOCATION)
                                        },
                                        onTakePhoto = { qid, inst ->
                                            val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
                                            if (!granted) cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
                                            val file = MediaFiles.newPhotoFile(context)
                                            val uri = MediaFiles.uriForFile(context, file)
                                            pendingPhotoQuestionId = qid; pendingPhotoUri = uri
                                            takePictureLauncher.launch(uri)
                                        },
                                        onStartAudio = { qid -> recordingQuestionId = qid; if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) audioRecorder.start() else audioPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO) },
                                        onStopAudio = { qid, inst -> val file = audioRecorder.stop(); recordingQuestionId = null; if (file != null) viewModel.setMediaAnswer(qid, file.absolutePath, inst) },
                                        onSignature = { qid, path, inst -> viewModel.setMediaAnswer(qid, path, inst) },
                                        onScan = { qid -> pendingBarcodeQuestionId = qid; barcodeLauncher.launch(ScanOptions().setBeepEnabled(false).setOrientationLocked(false)) }
                                    )
                                }
                                if (group.repeatable && instance != 0) {
                                    Button(onClick = { viewModel.removeGroupInstance(group.id, instance) }, modifier = Modifier.fillMaxWidth()) { Text("Remove ${group.title} #${instance + 1}") }
                                }
                            }
                        }
                    }

                    if (group.repeatable) {
                        item(key = "add:${group.id}") {
                            Button(onClick = { viewModel.addGroupInstance(group.id) }, modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp)) {
                                Text("+ Add ${group.title}")
                            }
                        }
                    }
                }
            }

            state.errorMessage?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(horizontal = 16.dp)) }
            Column(modifier = Modifier.padding(16.dp)) {
                Button(onClick = { viewModel.saveDraft {} }, enabled = !state.isSaving, modifier = Modifier.fillMaxWidth()) { Text("Save draft") }
                Button(onClick = { viewModel.submit() }, enabled = !state.isSaving, modifier = Modifier.fillMaxWidth().padding(top = 8.dp)) { Text(if (state.isSaving) "Saving…" else "Complete submission") }
            }
        }
    }
}

@Composable
private fun RenderQuestion(
    question: com.kbstoolbox.app.data.local.entity.QuestionEntity,
    instanceIndex: Int?,
    index: Int,
    state: FormFillUiState,
    viewModel: FormFillViewModel,
    context: android.content.Context,
    coroutineScope: kotlinx.coroutines.CoroutineScope,
    pendingGpsQuestionId: (String) -> Unit,
    pendingPhoto: (String, android.net.Uri) -> Unit,
    setBarcode: (String) -> Unit,
    setRecording: (String) -> Unit,
    recordingQuestionId: String?,
    audioRecorder: AudioRecorder,
    onCaptureLocation: (String, Int?) -> Unit,
    onTakePhoto: (String, Int?) -> Unit,
    onStartAudio: (String) -> Unit,
    onStopAudio: (String, Int?) -> Unit,
    onSignature: (String, String, Int?) -> Unit,
    onScan: (String) -> Unit
) {
    val key = if (instanceIndex == null) question.id else "${question.id}#$instanceIndex"
    QuestionField(
        question = question,
        index = index,
        value = state.textAnswers[key],
        mediaValue = state.mediaAnswers[key],
        choices = viewModel.choicesFor(question),
        errorMessage = state.validationErrors[key],
        onTextChange = { viewModel.updateTextAnswer(question.id, it, instanceIndex) },
        onMultiToggle = { value, checked -> viewModel.toggleMultipleChoice(question.id, value, checked, instanceIndex) },
        onCaptureGps = { onCaptureLocation(question.id, instanceIndex) },
        onCapturePhoto = { onTakePhoto(question.id, instanceIndex) },
        onStartAudio = { onStartAudio(question.id) },
        onStopAudio = { onStopAudio(question.id, instanceIndex) },
        isRecordingAudio = recordingQuestionId == question.id,
        onSignatureSaved = { path -> onSignature(question.id, path, instanceIndex) },
        onScanBarcode = { onScan(question.id) }
    )
}

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
                items(state.visibleQuestions, key = { it.id }) { question ->
                    val index = state.questions.indexOf(question)
                    QuestionField(
                        question = question,
                        index = index,
                        value = state.textAnswers[question.id],
                        mediaValue = state.mediaAnswers[question.id],
                        choices = viewModel.choicesFor(question),
                        errorMessage = state.validationErrors[question.id],
                        onTextChange = { viewModel.updateTextAnswer(question.id, it) },
                        onMultiToggle = { choiceValue, checked -> viewModel.toggleMultipleChoice(question.id, choiceValue, checked) },
                        onCaptureGps = {
                            pendingGpsQuestionId = question.id
                            val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                            if (granted) {
                                coroutineScope.launch {
                                    val location = LocationCapture.captureCurrentLocation(context)
                                    if (location != null) viewModel.onGpsCaptured(question.id, location.latitude, location.longitude)
                                }
                            } else {
                                locationPermissionLauncher.launch(Manifest.permission.ACCESS_FINE_LOCATION)
                            }
                        },
                        onCapturePhoto = {
                            val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
                            if (!granted) {
                                cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
                            }
                            val file = MediaFiles.newPhotoFile(context)
                            val uri = MediaFiles.uriForFile(context, file)
                            pendingPhotoQuestionId = question.id
                            pendingPhotoUri = uri
                            takePictureLauncher.launch(uri)
                        },
                        onStartAudio = {
                            recordingQuestionId = question.id
                            val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED
                            if (granted) {
                                audioRecorder.start()
                            } else {
                                audioPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                            }
                        },
                        onStopAudio = {
                            val file = audioRecorder.stop()
                            recordingQuestionId = null
                            if (file != null) viewModel.setMediaAnswer(question.id, file.absolutePath)
                        },
                        isRecordingAudio = recordingQuestionId == question.id,
                        onSignatureSaved = { path -> viewModel.setMediaAnswer(question.id, path) },
                        onScanBarcode = {
                            pendingBarcodeQuestionId = question.id
                            val options = ScanOptions().setBeepEnabled(false).setOrientationLocked(false)
                            barcodeLauncher.launch(options)
                        }
                    )
                }
            }

            state.errorMessage?.let {
                Text(
                    it,
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier.padding(horizontal = 16.dp)
                )
            }

            Column(modifier = Modifier.padding(16.dp)) {
                Button(
                    onClick = { viewModel.saveDraft {} },
                    enabled = !state.isSaving,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Save draft")
                }
                Button(
                    onClick = { viewModel.submit() },
                    enabled = !state.isSaving,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 8.dp)
                ) {
                    Text(if (state.isSaving) "Saving…" else "Complete submission")
                }
            }
        }
    }
}

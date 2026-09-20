package com.kbstoolbox.app.ui.submissions

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.kbstoolbox.app.data.local.entity.LocalSyncStatus
import com.kbstoolbox.app.data.local.entity.SubmissionEntity
import com.kbstoolbox.app.di.ServiceLocator
import com.kbstoolbox.app.ui.theme.Brick
import com.kbstoolbox.app.ui.theme.FieldGreen
import com.kbstoolbox.app.ui.theme.Ochre
import com.kbstoolbox.app.util.ViewModelFactory

@Composable
fun SubmissionsScreen() {
    val context = LocalContext.current
    val viewModel: SubmissionsViewModel = viewModel(
        factory = ViewModelFactory { SubmissionsViewModel(context, ServiceLocator.submissionRepository(context), ServiceLocator.syncRepository(context)) }
    )
    val submissions by viewModel.submissions.collectAsState()

    val pending = submissions.count { it.status == LocalSyncStatus.PENDING_SYNC || it.status == LocalSyncStatus.FAILED }
    Scaffold(topBar = { TopAppBar(title = { Text("Sync Center") }) }) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding)) {
            Row(modifier = Modifier.fillMaxWidth().padding(16.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                Column { Text("Pending: $pending"); Text("Synced: ${submissions.count { it.status == LocalSyncStatus.SYNCED }}") }
                Button(onClick = { viewModel.syncNow() }) { Text("Sync now") }
            }
            HorizontalDivider()
        if (submissions.isEmpty()) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp)
            ) {
                Text("No submissions yet.", style = MaterialTheme.typography.titleLarge)
                Text("Forms you save or complete will show up here with their sync status.")
            }
        } else {
            LazyColumn(modifier = Modifier
                .fillMaxSize()
                .padding(16.dp)) {
                items(submissions, key = { it.clientSubmissionUuid }) { submission ->
                    SubmissionRow(submission)
                }
            }
        }
        }
    }
}

@Composable
private fun SubmissionRow(submission: SubmissionEntity) {
    Card(modifier = Modifier
        .fillMaxWidth()
        .padding(bottom = 10.dp)) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(submission.surveyTitle, style = MaterialTheme.typography.titleLarge)
                StatusChip(submission.status)
            }
            Text(
                "Submission ${submission.clientSubmissionUuid.take(8)}",
                style = MaterialTheme.typography.bodyMedium
            )
            if (submission.status == LocalSyncStatus.FAILED && submission.syncErrorMessage != null) {
                Text(
                    submission.syncErrorMessage,
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodyMedium
                )
            }
        }
    }
}

@Composable
private fun StatusChip(status: LocalSyncStatus) {
    val (label, color) = when (status) {
        LocalSyncStatus.DRAFT -> "Draft" to Color.Gray
        LocalSyncStatus.PENDING_SYNC -> "Pending sync" to Ochre
        LocalSyncStatus.SYNCING -> "Uploading…" to Ochre
        LocalSyncStatus.SYNCED -> "Synced" to FieldGreen
        LocalSyncStatus.FAILED -> "Failed — will retry" to Brick
    }
    Text(label, color = color, style = MaterialTheme.typography.labelLarge)
}

package com.kbstoolbox.app.ui.submissions

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kbstoolbox.app.data.local.entity.SubmissionEntity
import com.kbstoolbox.app.data.repository.SubmissionRepository
import com.kbstoolbox.app.data.repository.SyncRepository
import com.kbstoolbox.app.data.repository.SyncUploadOutcome
import com.kbstoolbox.app.sync.SyncWorker
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class SubmissionsViewModel(
    private val context: Context,
    submissionRepository: SubmissionRepository,
    private val syncRepository: SyncRepository
) : ViewModel() {
    val submissions: StateFlow<List<SubmissionEntity>> = submissionRepository.observeAll()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun syncNow() {
        viewModelScope.launch { syncRepository.uploadPendingSubmissions(); SyncWorker.triggerImmediateSync(context) }
    }
}

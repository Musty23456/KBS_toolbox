package com.kbstoolbox.app.ui.submissions

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kbstoolbox.app.data.local.entity.SubmissionEntity
import com.kbstoolbox.app.data.repository.SubmissionRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn

class SubmissionsViewModel(submissionRepository: SubmissionRepository) : ViewModel() {
    val submissions: StateFlow<List<SubmissionEntity>> = submissionRepository.observeAll()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
}

package com.kbstoolbox.app.ui.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kbstoolbox.app.data.repository.SubmissionRepository
import com.kbstoolbox.app.data.repository.SurveyRepository
import com.kbstoolbox.app.session.SessionManager
import com.kbstoolbox.app.session.SessionState
import com.kbstoolbox.app.sync.NetworkConnectivityObserver
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class DashboardUiState(
    val fullName: String = "",
    val role: String = "",
    val isOnline: Boolean = false,
    val downloadedSurveys: Int = 0,
    val draftForms: Int = 0,
    val pendingSync: Int = 0,
    val syncedSubmissions: Int = 0,
    val failedSync: Int = 0,
    val isRefreshing: Boolean = false,
    val refreshMessage: String? = null
)

class DashboardViewModel(
    private val sessionManager: SessionManager,
    private val surveyRepository: SurveyRepository,
    private val submissionRepository: SubmissionRepository,
    connectivityObserver: NetworkConnectivityObserver
) : ViewModel() {

    private val _refreshState = MutableStateFlow(Pair(false, null as String?))

    private data class RepoCounts(
        val surveys: List<*>,
        val draft: Int,
        val pending: Int,
        val synced: Int,
        val failed: Int
    )

    val uiState: StateFlow<DashboardUiState> = combine(
        combine(
            surveyRepository.observeSurveys(),
            submissionRepository.observeDraftCount(),
            submissionRepository.observePendingCount(),
            submissionRepository.observeSyncedCount(),
            submissionRepository.observeFailedCount()
        ) { surveys, draft, pending, synced, failed ->
            RepoCounts(surveys, draft, pending, synced, failed)
        },
        connectivityObserver.observe(),
        _refreshState
    ) { counts, online, refresh ->
        val session = sessionManager.sessionState.value
        val fullName = (session as? SessionState.LoggedIn)?.fullName ?: ""
        val role = (session as? SessionState.LoggedIn)?.role ?: ""

        DashboardUiState(
            fullName = fullName,
            role = role,
            isOnline = online,
            downloadedSurveys = counts.surveys.size,
            draftForms = counts.draft,
            pendingSync = counts.pending,
            syncedSubmissions = counts.synced,
            failedSync = counts.failed,
            isRefreshing = refresh.first,
            refreshMessage = refresh.second
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), DashboardUiState())

    fun refreshSurveys() {
        viewModelScope.launch {
            _refreshState.value = Pair(true, null)
            val result = surveyRepository.refreshFromServer()
            _refreshState.value = Pair(
                false,
                when (result) {
                    is com.kbstoolbox.app.data.repository.SyncDownloadResult.Success ->
                        "Downloaded ${result.surveyCount} survey(s)."
                    is com.kbstoolbox.app.data.repository.SyncDownloadResult.Error -> result.message
                }
            )
        }
    }
}

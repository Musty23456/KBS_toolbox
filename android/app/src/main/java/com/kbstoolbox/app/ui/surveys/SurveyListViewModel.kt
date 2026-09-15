package com.kbstoolbox.app.ui.surveys

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kbstoolbox.app.data.local.entity.SurveyEntity
import com.kbstoolbox.app.data.repository.SurveyRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn

class SurveyListViewModel(surveyRepository: SurveyRepository) : ViewModel() {
    val surveys: StateFlow<List<SurveyEntity>> = surveyRepository.observeSurveys()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
}

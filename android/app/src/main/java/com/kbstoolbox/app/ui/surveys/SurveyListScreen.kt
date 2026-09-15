package com.kbstoolbox.app.ui.surveys

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
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
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.kbstoolbox.app.di.ServiceLocator
import com.kbstoolbox.app.util.ViewModelFactory

@Composable
fun SurveyListScreen(onSurveySelected: (surveyId: String, surveyTitle: String) -> Unit) {
    val context = LocalContext.current
    val viewModel: SurveyListViewModel = viewModel(
        factory = ViewModelFactory { SurveyListViewModel(ServiceLocator.surveyRepository(context)) }
    )
    val surveys by viewModel.surveys.collectAsState()

    Scaffold(topBar = { TopAppBar(title = { Text("Surveys") }) }) { padding ->
        if (surveys.isEmpty()) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(24.dp),
                verticalArrangement = Arrangement.Center
            ) {
                Text("No surveys downloaded yet.", style = MaterialTheme.typography.titleLarge)
                Text(
                    "Go to the dashboard and tap \"Download / refresh surveys\" while online.",
                    style = MaterialTheme.typography.bodyMedium
                )
            }
        } else {
            LazyColumn(modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp)) {
                items(surveys, key = { it.id }) { survey ->
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(bottom = 12.dp)
                            .clickable { onSurveySelected(survey.id, survey.title) }
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(survey.title, style = MaterialTheme.typography.titleLarge)
                            survey.description?.let {
                                Text(it, style = MaterialTheme.typography.bodyMedium)
                            }
                            Text(
                                "Version ${survey.currentVersionNumber ?: "—"}",
                                style = MaterialTheme.typography.bodyMedium
                            )
                        }
                    }
                }
            }
        }
    }
}

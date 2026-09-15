package com.kbstoolbox.app.ui.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.kbstoolbox.app.di.ServiceLocator
import com.kbstoolbox.app.util.ViewModelFactory
import androidx.compose.ui.platform.LocalContext

@Composable
fun LoginScreen(onLoginSuccess: () -> Unit, onNavigateToRegister: () -> Unit) {
    val context = LocalContext.current
    val viewModel: LoginViewModel = viewModel(
        factory = ViewModelFactory { LoginViewModel(ServiceLocator.authRepository(context)) }
    )
    val state by viewModel.uiState.collectAsState()

    LaunchedEffect(state.loginSucceeded) {
        if (state.loginSucceeded) onLoginSuccess()
    }

    Scaffold { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 32.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("KBS Toolbox", style = MaterialTheme.typography.headlineMedium)
            Text(
                "by Musty — field survey collection",
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(bottom = 32.dp)
            )

            OutlinedTextField(
                value = state.email,
                onValueChange = viewModel::onEmailChange,
                label = { Text("Email") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                modifier = Modifier.fillMaxWidth()
            )
            Column(modifier = Modifier.padding(top = 12.dp)) {
                OutlinedTextField(
                    value = state.password,
                    onValueChange = viewModel::onPasswordChange,
                    label = { Text("Password") },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                    modifier = Modifier.fillMaxWidth()
                )
            }

            state.error?.let {
                Text(
                    text = it,
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier.padding(top = 12.dp)
                )
            }

            Button(
                onClick = { viewModel.submit() },
                enabled = !state.isSubmitting,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 24.dp)
            ) {
                if (state.isSubmitting) {
                    CircularProgressIndicator(modifier = Modifier.padding(end = 8.dp))
                }
                Text(if (state.isSubmitting) "Signing in…" else "Sign in")
            }

            TextButton(
                onClick = onNavigateToRegister,
                modifier = Modifier.padding(top = 8.dp)
            ) {
                Text("Don't have an account? Sign up")
            }
        }
    }
}

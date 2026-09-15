package com.kbstoolbox.app.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kbstoolbox.app.data.repository.AuthRepository
import com.kbstoolbox.app.data.repository.AuthResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class LoginUiState(
    val email: String = "",
    val password: String = "",
    val isSubmitting: Boolean = false,
    val error: String? = null,
    val loginSucceeded: Boolean = false
)

class LoginViewModel(private val authRepository: AuthRepository) : ViewModel() {

    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    fun onEmailChange(value: String) {
        _uiState.value = _uiState.value.copy(email = value, error = null)
    }

    fun onPasswordChange(value: String) {
        _uiState.value = _uiState.value.copy(password = value, error = null)
    }

    fun submit() {
        val state = _uiState.value
        if (state.email.isBlank() || state.password.isBlank()) {
            _uiState.value = state.copy(error = "Enter both email and password.")
            return
        }
        _uiState.value = state.copy(isSubmitting = true, error = null)
        viewModelScope.launch {
            when (val result = authRepository.login(state.email.trim(), state.password)) {
                is AuthResult.Success -> {
                    _uiState.value = _uiState.value.copy(isSubmitting = false, loginSucceeded = true)
                }
                is AuthResult.Error -> {
                    _uiState.value = _uiState.value.copy(isSubmitting = false, error = result.message)
                }
            }
        }
    }
}

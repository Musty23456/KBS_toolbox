package com.kbstoolbox.app.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kbstoolbox.app.data.repository.AuthRepository
import com.kbstoolbox.app.data.repository.AuthResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class RegisterUiState(
    val fullName: String = "",
    val email: String = "",
    val password: String = "",
    val confirmPassword: String = "",
    val isSubmitting: Boolean = false,
    val error: String? = null,
    val registerSucceeded: Boolean = false
)

class RegisterViewModel(private val authRepository: AuthRepository) : ViewModel() {

    private val _uiState = MutableStateFlow(RegisterUiState())
    val uiState: StateFlow<RegisterUiState> = _uiState.asStateFlow()

    fun onFullNameChange(value: String) {
        _uiState.value = _uiState.value.copy(fullName = value, error = null)
    }

    fun onEmailChange(value: String) {
        _uiState.value = _uiState.value.copy(email = value, error = null)
    }

    fun onPasswordChange(value: String) {
        _uiState.value = _uiState.value.copy(password = value, error = null)
    }

    fun onConfirmPasswordChange(value: String) {
        _uiState.value = _uiState.value.copy(confirmPassword = value, error = null)
    }

    fun submit() {
        val state = _uiState.value
        val validationError = validate(state)
        if (validationError != null) {
            _uiState.value = state.copy(error = validationError)
            return
        }
        _uiState.value = state.copy(isSubmitting = true, error = null)
        viewModelScope.launch {
            val result = authRepository.register(
                fullName = state.fullName.trim(),
                email = state.email.trim(),
                password = state.password
            )
            when (result) {
                is AuthResult.Success -> {
                    _uiState.value = _uiState.value.copy(isSubmitting = false, registerSucceeded = true)
                }
                is AuthResult.Error -> {
                    _uiState.value = _uiState.value.copy(isSubmitting = false, error = result.message)
                }
            }
        }
    }

    private fun validate(state: RegisterUiState): String? {
        return when {
            state.fullName.isBlank() -> "Enter your full name."
            state.email.isBlank() -> "Enter your email."
            state.password.length < 8 -> "Password must be at least 8 characters."
            state.password != state.confirmPassword -> "Passwords do not match."
            else -> null
        }
    }
}

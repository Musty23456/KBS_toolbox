package com.kbstoolbox.app.data.remote.dto

data class LoginRequestDto(
    val email: String,
    val password: String
)

// role must be one of the backend's RoleName values: "ADMINISTRATOR",
// "SUPERVISOR", "ENUMERATOR". Defaults to "ENUMERATOR" since that's what
// field staff self-registering from the app should get; administrators can
// promote a user's role later from the web dashboard.
data class RegisterRequestDto(
    val full_name: String,
    val email: String,
    val password: String,
    val role: String = "ENUMERATOR"
)

data class TokenResponseDto(
    val access_token: String,
    val refresh_token: String,
    val token_type: String,
    val expires_in_minutes: Int
)

data class UserDto(
    val id: String,
    val full_name: String,
    val email: String,
    val role: String,
    val is_active: Boolean,
    val created_at: String
)

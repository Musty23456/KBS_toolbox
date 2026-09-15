package com.kbstoolbox.app.data.remote

import com.kbstoolbox.app.data.remote.dto.LoginRequestDto
import com.kbstoolbox.app.data.remote.dto.RegisterRequestDto
import com.kbstoolbox.app.data.remote.dto.SurveyDetailDto
import com.kbstoolbox.app.data.remote.dto.SyncDownloadResponseDto
import com.kbstoolbox.app.data.remote.dto.SyncUploadRequestDto
import com.kbstoolbox.app.data.remote.dto.SyncUploadResponseDto
import com.kbstoolbox.app.data.remote.dto.TokenResponseDto
import com.kbstoolbox.app.data.remote.dto.UserDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface ApiService {

    @POST("/api/auth/login-json")
    suspend fun login(@Body request: LoginRequestDto): Response<TokenResponseDto>

    @POST("/api/auth/register")
    suspend fun register(@Body request: RegisterRequestDto): Response<UserDto>

    @POST("/api/auth/logout")
    suspend fun logout(): Response<Unit>

    @GET("/api/auth/me")
    suspend fun me(): Response<UserDto>

    @GET("/api/surveys")
    suspend fun listSurveys(): Response<List<SurveyDetailDto>>

    @GET("/api/sync/download")
    suspend fun syncDownload(): Response<SyncDownloadResponseDto>

    @POST("/api/sync/upload")
    suspend fun syncUpload(@Body request: SyncUploadRequestDto): Response<SyncUploadResponseDto>
}

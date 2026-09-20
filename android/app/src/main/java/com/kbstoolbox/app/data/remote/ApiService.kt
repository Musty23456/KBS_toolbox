package com.kbstoolbox.app.data.remote
import com.kbstoolbox.app.data.remote.dto.MediaUploadResponseDto
import com.kbstoolbox.app.data.remote.dto.LoginRequestDto
import com.kbstoolbox.app.data.remote.dto.RegisterRequestDto
import com.kbstoolbox.app.data.remote.dto.SurveyDetailDto
import com.kbstoolbox.app.data.remote.dto.SyncDownloadResponseDto
import com.kbstoolbox.app.data.remote.dto.SyncUploadRequestDto
import com.kbstoolbox.app.data.remote.dto.SyncUploadResponseDto
import com.kbstoolbox.app.data.remote.dto.TokenResponseDto
import com.kbstoolbox.app.data.remote.dto.DeviceHeartbeatDto
import com.kbstoolbox.app.data.remote.dto.UserDto
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Multipart
import retrofit2.http.Part

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

    @POST("/api/devices/heartbeat")
    suspend fun deviceHeartbeat(@Body request: DeviceHeartbeatDto): Response<Any>

    @Multipart
    @POST("/api/media/upload")
    suspend fun uploadMedia(
        @Part("submission_id") submissionId: RequestBody,
        @Part("question_id") questionId: RequestBody,
        @Part("kind") kind: RequestBody,
        @Part("group_instance_index") groupInstanceIndex: RequestBody?,
        @Part file: MultipartBody.Part
    ): Response<MediaUploadResponseDto>
}

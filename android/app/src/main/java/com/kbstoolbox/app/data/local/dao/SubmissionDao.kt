package com.kbstoolbox.app.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import com.kbstoolbox.app.data.local.entity.LocalSyncStatus
import com.kbstoolbox.app.data.local.entity.SubmissionAnswerEntity
import com.kbstoolbox.app.data.local.entity.SubmissionEntity
import kotlinx.coroutines.flow.Flow

data class SubmissionWithAnswers(
    val submission: SubmissionEntity,
    val answers: List<SubmissionAnswerEntity>
)

@Dao
interface SubmissionDao {

    @Query("SELECT * FROM submissions ORDER BY createdAt DESC")
    fun observeAll(): Flow<List<SubmissionEntity>>

    @Query("SELECT * FROM submissions WHERE status = :status ORDER BY createdAt ASC")
    suspend fun getByStatus(status: LocalSyncStatus): List<SubmissionEntity>

    @Query("SELECT * FROM submissions WHERE status = :status ORDER BY createdAt ASC")
    fun observeByStatus(status: LocalSyncStatus): Flow<List<SubmissionEntity>>

    @Query("SELECT * FROM submissions WHERE clientSubmissionUuid = :uuid")
    suspend fun getByUuid(uuid: String): SubmissionEntity?

    @Query("SELECT * FROM submission_answers WHERE submissionUuid = :uuid")
    suspend fun getAnswers(uuid: String): List<SubmissionAnswerEntity>

    @Query("UPDATE submission_answers SET mediaReference = :reference WHERE id = :answerId")
    suspend fun updateMediaReference(answerId: Long, reference: String)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSubmission(submission: SubmissionEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAnswers(answers: List<SubmissionAnswerEntity>)

    @Query("DELETE FROM submission_answers WHERE submissionUuid = :uuid")
    suspend fun deleteAnswersForSubmission(uuid: String)

    @Transaction
    suspend fun saveSubmissionWithAnswers(submission: SubmissionEntity, answers: List<SubmissionAnswerEntity>) {
        deleteAnswersForSubmission(submission.clientSubmissionUuid)
        insertSubmission(submission)
        insertAnswers(answers)
    }

    @Query(
        "UPDATE submissions SET status = :status, serverSubmissionId = :serverId, " +
            "syncErrorMessage = :error, syncAttemptCount = syncAttemptCount + 1, updatedAt = :now " +
            "WHERE clientSubmissionUuid = :uuid"
    )
    suspend fun updateSyncResult(uuid: String, status: LocalSyncStatus, serverId: String?, error: String?, now: Long)

    @Query("UPDATE submissions SET status = :status, updatedAt = :now WHERE clientSubmissionUuid = :uuid")
    suspend fun updateStatus(uuid: String, status: LocalSyncStatus, now: Long)

    @Query("SELECT COUNT(*) FROM submissions WHERE status = :status")
    fun countByStatus(status: LocalSyncStatus): Flow<Int>
}

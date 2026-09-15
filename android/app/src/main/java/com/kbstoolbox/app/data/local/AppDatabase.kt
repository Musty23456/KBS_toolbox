package com.kbstoolbox.app.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.kbstoolbox.app.data.local.dao.SubmissionDao
import com.kbstoolbox.app.data.local.dao.SurveyDao
import com.kbstoolbox.app.data.local.entity.ChoiceEntity
import com.kbstoolbox.app.data.local.entity.QuestionEntity
import com.kbstoolbox.app.data.local.entity.SubmissionAnswerEntity
import com.kbstoolbox.app.data.local.entity.SubmissionEntity
import com.kbstoolbox.app.data.local.entity.SurveyEntity

@Database(
    entities = [
        SurveyEntity::class,
        QuestionEntity::class,
        ChoiceEntity::class,
        SubmissionEntity::class,
        SubmissionAnswerEntity::class
    ],
    version = 1,
    exportSchema = true
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun surveyDao(): SurveyDao
    abstract fun submissionDao(): SubmissionDao

    companion object {
        @Volatile
        private var instance: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase =
            instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "kbs_toolbox.db"
                ).build().also { instance = it }
            }
    }
}

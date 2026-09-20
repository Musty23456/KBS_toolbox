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
import com.kbstoolbox.app.data.local.entity.QuestionGroupEntity
import com.kbstoolbox.app.data.local.entity.SubmissionAnswerEntity
import com.kbstoolbox.app.data.local.entity.SubmissionEntity
import com.kbstoolbox.app.data.local.entity.SurveyEntity

@Database(
    entities = [
        SurveyEntity::class,
        QuestionEntity::class,
        QuestionGroupEntity::class,
        ChoiceEntity::class,
        SubmissionEntity::class,
        SubmissionAnswerEntity::class
    ],
    version = 2,
    exportSchema = true
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun surveyDao(): SurveyDao
    abstract fun submissionDao(): SubmissionDao

    companion object {
        private val MIGRATION_1_2 = object : androidx.room.migration.Migration(1, 2) {
            override fun migrate(db: androidx.sqlite.db.SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE questions ADD COLUMN groupId TEXT")
                db.execSQL("ALTER TABLE submission_answers ADD COLUMN groupInstanceIndex INTEGER")
                db.execSQL("CREATE TABLE IF NOT EXISTS question_groups (id TEXT NOT NULL PRIMARY KEY, surveyId TEXT NOT NULL, surveyVersionId TEXT NOT NULL, sectionId TEXT, title TEXT NOT NULL, description TEXT, orderIndex INTEGER NOT NULL, repeatable INTEGER NOT NULL, minRepeats INTEGER NOT NULL, maxRepeats INTEGER)")
            }
        }

        @Volatile
        private var instance: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase =
            instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "kbs_toolbox.db"
                ).addMigrations(MIGRATION_1_2)
                .build().also { instance = it }
            }
    }
}

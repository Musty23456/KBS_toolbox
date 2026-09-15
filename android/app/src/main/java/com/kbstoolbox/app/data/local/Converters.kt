package com.kbstoolbox.app.data.local

import androidx.room.TypeConverter
import com.kbstoolbox.app.data.local.entity.LocalSyncStatus

class Converters {
    @TypeConverter
    fun fromSyncStatus(status: LocalSyncStatus): String = status.name

    @TypeConverter
    fun toSyncStatus(value: String): LocalSyncStatus = LocalSyncStatus.valueOf(value)
}

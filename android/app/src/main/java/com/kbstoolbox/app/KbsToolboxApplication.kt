package com.kbstoolbox.app

import android.app.Application
import com.kbstoolbox.app.sync.SyncWorker

class KbsToolboxApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        SyncWorker.schedulePeriodic(this)
    }
}

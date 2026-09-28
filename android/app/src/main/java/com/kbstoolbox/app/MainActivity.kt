package com.kbstoolbox.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.kbstoolbox.app.di.ServiceLocator
import com.kbstoolbox.app.ui.navigation.KbsToolboxNavHost
import com.kbstoolbox.app.ui.theme.KbsToolboxTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // Live presence: while the app is on screen and the user is signed in,
        // tell the server "I'm online" every minute. Stops automatically when
        // the app goes to the background. Failures are ignored (offline is fine).
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                while (true) {
                    withContext(Dispatchers.IO) {
                        try {
                            val hasSession = ServiceLocator.sessionManager(applicationContext).getAccessToken() != null
                            if (hasSession) {
                                ServiceLocator.syncRepository(applicationContext).sendHeartbeat()
                            }
                        } catch (_: Exception) {
                        }
                    }
                    delay(60_000L)
                }
            }
        }

        setContent {
            KbsToolboxTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    KbsToolboxNavHost()
                }
            }
        }
    }
}

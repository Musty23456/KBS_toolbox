package com.kbstoolbox.app.util

import android.annotation.SuppressLint
import android.content.Context
import com.google.android.gms.location.CurrentLocationRequest
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import kotlinx.coroutines.tasks.await

data class CapturedLocation(val latitude: Double, val longitude: Double)

/**
 * One-shot GPS fix, used when an enumerator taps "Capture location" on a
 * GPS-type question. Requires ACCESS_FINE_LOCATION to already be granted —
 * callers must request the runtime permission first.
 */
object LocationCapture {

    @SuppressLint("MissingPermission")
    suspend fun captureCurrentLocation(context: Context): CapturedLocation? {
        val client = LocationServices.getFusedLocationProviderClient(context)
        val request = CurrentLocationRequest.Builder()
            .setPriority(Priority.PRIORITY_HIGH_ACCURACY)
            .build()
        val location = client.getCurrentLocation(request, null).await() ?: return null
        return CapturedLocation(location.latitude, location.longitude)
    }
}

package com.kbstoolbox.app.util

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider

/** Small helper so each screen can build its ViewModel with constructor args from ServiceLocator, without Hilt. */
class ViewModelFactory(private val creator: () -> ViewModel) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T = creator() as T
}

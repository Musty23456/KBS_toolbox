package com.kbstoolbox.app.ui.navigation

object Routes {
    const val SPLASH = "splash"
    const val LOGIN = "login"
    const val REGISTER = "register"
    const val DASHBOARD = "dashboard"
    const val SURVEY_LIST = "surveys"
    const val SUBMISSIONS = "submissions"
    const val FORM_FILL = "form_fill/{surveyId}/{submissionUuid}"
    const val ABOUT = "about"

    fun formFill(surveyId: String, submissionUuid: String) =
        "form_fill/$surveyId/${submissionUuid.ifBlank { "new" }}"
}

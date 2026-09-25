package com.kbstoolbox.app.ui.navigation
import com.kbstoolbox.app.ui.about.AboutScreen
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.kbstoolbox.app.di.ServiceLocator
import com.kbstoolbox.app.session.SessionState
import com.kbstoolbox.app.ui.auth.LoginScreen
import com.kbstoolbox.app.ui.auth.RegisterScreen
import com.kbstoolbox.app.ui.dashboard.DashboardScreen
import com.kbstoolbox.app.ui.formfill.FormFillScreen
import com.kbstoolbox.app.ui.splash.SplashScreen
import com.kbstoolbox.app.ui.submissions.SubmissionsScreen
import com.kbstoolbox.app.ui.surveys.SurveyListScreen
import kotlinx.coroutines.launch

@Composable
fun KbsToolboxNavHost() {
    val navController = rememberNavController()
    val context = LocalContext.current
    val sessionState by ServiceLocator.sessionManager(context).sessionState.collectAsState()
    val coroutineScope = rememberCoroutineScope()

    NavHost(navController = navController, startDestination = Routes.SPLASH) {

        composable(Routes.SPLASH) {
            SplashScreen(onFinished = {
                val destination = if (sessionState is SessionState.LoggedIn) Routes.DASHBOARD else Routes.LOGIN
                navController.navigateAndClearBackStack(destination)
            })
        }

        composable(Routes.LOGIN) {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigateAndClearBackStack(Routes.DASHBOARD)
                },
                onNavigateToRegister = {
                    navController.navigate(Routes.REGISTER)
                }
            )
        }

        composable(Routes.REGISTER) {
            RegisterScreen(
                onRegisterSuccess = {
                    navController.navigateAndClearBackStack(Routes.DASHBOARD)
                },
                onBackToLogin = {
                    navController.popBackStack()
                }
            )
        }

        composable(Routes.DASHBOARD) {
            // If the session is cleared elsewhere (e.g. a 401 from an expired
            // token), fall back to login automatically instead of leaving the
            // user stranded on a dashboard that can no longer load data.
            LaunchedEffect(sessionState) {
                if (sessionState is SessionState.LoggedOut) {
                    navController.navigateAndClearBackStack(Routes.LOGIN)
                }
            }
            DashboardScreen(
                onOpenSurveys = { navController.navigate(Routes.SURVEY_LIST) },
                onOpenSubmissions = { navController.navigate(Routes.SUBMISSIONS) },
                onLogout = {
                    coroutineScope.launch {
                        ServiceLocator.authRepository(context).logout()
                    }
                }
            )
        }

        DashboardScreen(
    onOpenSurveys = {
        navController.navigate(Routes.SURVEY_LIST)
    },
    onOpenSubmissions = {
        navController.navigate(Routes.SUBMISSIONS)
    },
    onOpenAbout = {
        navController.navigate(Routes.ABOUT)
    },
    onLogout = {
        coroutineScope.launch {
            ServiceLocator.authRepository(context).logout()
        }
    }
)
        composable(Routes.SURVEY_LIST) {
            SurveyListScreen(onSurveySelected = { surveyId, _ ->
                navController.navigate(Routes.formFill(surveyId, ""))
            })
        }

        composable(Routes.SUBMISSIONS) {
            SubmissionsScreen()
        }

        composable(Routes.ABOUT) {
    AboutScreen(
        onBack = {
            navController.popBackStack()
        }
    )
        }
        composable(Routes.FORM_FILL) { backStackEntry ->
            val surveyId = backStackEntry.arguments?.getString("surveyId") ?: return@composable
            val rawSubmissionUuid = backStackEntry.arguments?.getString("submissionUuid") ?: "new"
            val submissionUuid = if (rawSubmissionUuid == "new") "" else rawSubmissionUuid
            FormFillScreen(
                surveyId = surveyId,
                submissionUuid = submissionUuid,
                onDone = { navController.popBackStack(Routes.SURVEY_LIST, inclusive = false) }
            )
        }
    }
}

private fun NavHostController.navigateAndClearBackStack(route: String) {
    navigate(route) {
        popUpTo(0) { inclusive = true }
        launchSingleTop = true
    }
}

package com.kbstoolbox.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

private val LightColors = lightColorScheme(
    primary = FieldGreen,
    onPrimary = PaperRaised,
    secondary = Ochre,
    onSecondary = PaperRaised,
    background = Paper,
    onBackground = Ink,
    surface = PaperRaised,
    onSurface = Ink,
    error = Brick,
    outline = Hairline
)

private val AppTypography = Typography(
    headlineMedium = TextStyle(fontWeight = FontWeight.SemiBold, fontSize = 26.sp),
    titleLarge = TextStyle(fontWeight = FontWeight.SemiBold, fontSize = 20.sp),
    bodyLarge = TextStyle(fontWeight = FontWeight.Normal, fontSize = 16.sp),
    bodyMedium = TextStyle(fontWeight = FontWeight.Normal, fontSize = 14.sp),
    labelLarge = TextStyle(fontWeight = FontWeight.Medium, fontSize = 14.sp)
)

@Composable
fun KbsToolboxTheme(content: @Composable () -> Unit) {
    // A single light "field registry" palette is used regardless of system
    // dark-mode setting, matching the web admin dashboard's fixed branding
    // rather than adapting to the OS theme.
    MaterialTheme(
        colorScheme = LightColors,
        typography = AppTypography,
        content = content
    )
}

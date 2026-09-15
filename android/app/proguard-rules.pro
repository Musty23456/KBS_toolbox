# Retrofit / Gson models keep their fields for reflection-based (de)serialization.
-keep class com.kbstoolbox.app.data.remote.dto.** { *; }
-keepattributes Signature
-keepattributes *Annotation*

# Room
-keep class com.kbstoolbox.app.data.local.entity.** { *; }

# OkHttp platform used only on JVM and when Conscrypt is available.
-dontwarn okhttp3.internal.platform.**
-dontwarn org.conscrypt.**

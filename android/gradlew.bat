@rem
@rem Copyright 2015 the original author or authors.
@rem
@rem Licensed under the Apache License, Version 2.0 (the "License");
@rem you may not use this file except in compliance with the License.
@rem You may obtain a copy of the License at
@rem
@rem      https://www.apache.org/licenses/LICENSE-2.0
@rem

@rem NOTE: gradle-wrapper.jar is not bundled in this archive — see the note
@rem in gradlew for how to generate it, or invoke `gradle` directly.

@if "%DEBUG%"=="" @echo off
setlocal

set DIRNAME=%~dp0
set APP_HOME=%DIRNAME%

set CLASSPATH=%APP_HOME%gradle\wrapper\gradle-wrapper.jar

if not exist "%CLASSPATH%" (
    echo ERROR: gradle\wrapper\gradle-wrapper.jar is missing. See the note in gradlew for how to generate it, or run 'gradle' directly instead of 'gradlew.bat'.
    exit /b 1
)

if defined JAVA_HOME goto findJavaFromJavaHome

set JAVA_EXE=java.exe
%JAVA_EXE% -version >NUL 2>&1
if "%ERRORLEVEL%" == "0" goto execute

echo ERROR: JAVA_HOME is not set and 'java' was not found in your PATH.
exit /b 1

:findJavaFromJavaHome
set JAVA_HOME=%JAVA_HOME:"=%
set JAVA_EXE=%JAVA_HOME%/bin/java.exe

if exist "%JAVA_EXE%" goto execute

echo ERROR: JAVA_HOME is set to an invalid directory: %JAVA_HOME%
exit /b 1

:execute
"%JAVA_EXE%" -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %*

endlocal

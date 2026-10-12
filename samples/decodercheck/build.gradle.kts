plugins { alias(libs.plugins.android.application) }
android {
    namespace = "com.diplay.decodercheck"
    compileSdk { version = release(37) }
    defaultConfig {
        applicationId = "com.diplay.decodercheck"
        minSdk = 23
        targetSdk = 23
        versionCode = 1
        versionName = "1.0"
    }
    compileOptions {
        isCoreLibraryDesugaringEnabled = true
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}
dependencies {
    implementation(project(":shared"))
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.5")
}

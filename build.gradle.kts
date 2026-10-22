// Top-level build file where you can add configuration options common to all sub-projects/modules.
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.compose) apply false
}
// Android JNI libraries cannot be loaded by host-side unit tests.
subprojects {
    configurations.configureEach {
        if (name.endsWith("UnitTestRuntimeClasspath")) {
            exclude(group = "org.conscrypt", module = "conscrypt-android")
        }
    }
    listOf("com.android.application", "com.android.library").forEach { pluginId ->
        pluginManager.withPlugin(pluginId) {
            dependencies.add("testImplementation", "org.conscrypt:conscrypt-openjdk-uber:2.7.0")
        }
    }
}

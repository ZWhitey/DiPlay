package com.shilapi.xcertplay

import android.view.View
import android.os.Looper
import org.junit.After
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.util.ReflectionHelpers
import org.robolectric.annotation.Config
import java.util.Locale

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [23], qualifiers = "en-sw600dp-w1024dp-h600dp-land-mdpi")
class Android6StartupTest {
    private val app get() = RuntimeEnvironment.getApplication()

    @After fun reset() {
        app.getSharedPreferences("diplay", 0).edit().clear().commit()
        CarPlayBackgroundSession.clear()
        AppAppearanceRuntime.resetForTest()
    }

    @Test fun launcherRendersOnAndroid6() {
        CarPlayBackgroundSession.clear()
        val controller = Robolectric.buildActivity(DiPlayActivity::class.java)
        controller.get().setTheme(android.R.style.Theme_Material_NoActionBar)
        try {
            controller.setup()
            assertNotNull(controller.get().findViewById<View>(android.R.id.content))
            assertFalse(controller.get().isFinishing)
        } finally { controller.pause().stop().destroy() }
    }

    @Test fun everySettingsCategoryRendersOnAndroid6() {
        val controller = Robolectric.buildActivity(DiPlayActivity::class.java)
        val activity = controller.get()
        activity.setTheme(android.R.style.Theme_Material_NoActionBar)
        try {
            controller.setup()
            ReflectionHelpers.setField(activity, "page", "settings")
            for (category in SettingsCategory.values()) {
                ReflectionHelpers.setField(activity, "settingsCategory", category)
                ReflectionHelpers.callInstanceMethod<Unit>(activity, "render")
                shadowOf(Looper.getMainLooper()).idle()
                assertFalse(category.name, activity.isFinishing)
            }
        } finally { controller.pause().stop().destroy() }
    }

    @Test fun traditionalChineseAndDensityOverrideSurviveAndroid6Launch() {
        AppLocale.save(app, AppLocale.TRADITIONAL_CHINESE)
        InterfaceSize.save(app, 150)
        val base = AppLocale.wrap(app)
        assertEquals(Locale.forLanguageTag("zh-TW"), AppLocale.primaryLocale(base.resources.configuration))
        val scaled = InterfaceSize.override(base.resources.configuration, 150)!!
        assertEquals(240, scaled.densityDpi)
        assertEquals(Locale.forLanguageTag("zh-TW"), AppLocale.primaryLocale(InterfaceSize.contextOverride(scaled)))
        val controller = Robolectric.buildActivity(DiPlayActivity::class.java)
        controller.get().setTheme(android.R.style.Theme_Material_NoActionBar)
        try {
            controller.setup()
            assertEquals(Locale.forLanguageTag("zh-TW"), AppLocale.primaryLocale(controller.get().resources.configuration))
            assertFalse(controller.get().isFinishing)
        } finally { controller.pause().stop().destroy() }
    }
}

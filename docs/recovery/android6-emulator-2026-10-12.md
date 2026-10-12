# Android 6 模擬器測試結果（2026-10-12）

- Android API 23，1024 MB RAM，1024×600，x86，軟體 CPU / SwiftShader。
- 本次重建的 APK 安裝成功，啟動成功，略過初始設定與開啟設定頁成功。
- DiPlayActivity 為前景活動，程序存活，測試 logcat 未發現 App FATAL EXCEPTION 或 ANR。
- 設定頁當下 PSS 約 30 MB。這是閒置畫面，不代表 CarPlay 播放耗用。
- 共用模組 1215 / 1215 通過；主程式 999 / 1013 通過，14 項 ExistingWifiManagerTest 因無非 loopback 介面失敗；home 4 / 4 通過。
- mobile / home / maphost APK 建置完成，lint 均無錯誤。
- APK minSdk 23，v1/v2 簽章驗證通過，runtime 認證資產與原始 APK 相同。
- 無法驗證 MTK 硬解、真實 iPhone 無線 CarPlay 及 30 FPS。

## 重建方式
先執行 `python3 scripts/recovery/install_host.py` 與 `python3 scripts/recovery/install_runtime.py`。
提供本機原始 APK 與私有簽章金鑰，再使用 `scripts/recovery/run_build.py` 跑 AGENTS.md 的 CI 命令；最後執行 `scripts/recovery/test_emulator.py`。
簽章與認證資產不得提交到公開 repo。模擬器使用唯讀映像及 interpret-only 安裝模式，避免軟體模擬的 dex2oat 過久；不能以這個模式推論實車 FPS。

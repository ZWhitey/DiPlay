# Android 6 解碼功能測試（2026-10-12）

## 結果
Android 6 / API 23、x86、1024 MB RAM、軟體 CPU 模擬下，使用 DiPlay 的 production shared AndroidMediaSink、VideoDecodeQueue、MediaCodecSupport、AirPlayCrypto 與 SurfaceView。

- 800×480 AVC baseline、無 B 幀，來源 30 FPS。
- 為測正確性，以 10 FPS 送資料，不作 30 FPS 效能判定。
- 90 個核心測試幀 + 6 個連續尾幀，96 個全部通過加密/解密位元比對並送入解碼器。
- 94 個輸出幀，已涵蓋最初的 90 個測試幀。最後兩個未輸出的尾幀為有限測試串流的解碼緩衝；截圖內 frame 93 與輸出計數一致。
- 使用 Conscrypt 原生解密實作、OMX.google.h264.decoder 軟體解碼器。
- 無 decoder recoveries，畫面正常；未發現本次測試的 native crash、FATAL EXCEPTION 或 ANR；解碼器釋放成功。

## 環境限制與失敗嘗試
預設 QEMU CPU 在 Android 系統的 libstagefright_soft_avcdec.so SSE 例程發生 SIGILL。完整 max CPU 的安裝過慢，該輪中止，沒有算成通過。改用 qemu32,+ssse3,+sse4.1,+sse4.2 後成功。
第一次有限影片只有 90 幀時收到 88 個輸出；加入 6 個連續尾幀驗證原始 90 個核心幀。沒有修改 production 解碼器來改變判定。

沒有真實 iPhone / CarPlay 協定連線、沒有 MTK 硬解、沒有 8227L 或 30 FPS 效能驗證。

## 重現
```
python3 samples/decodercheck/generate_fixture.py
DIPLAY_DECODER_TEST=1 python3 scripts/recovery/run_build.py :decodercheck:assembleDebug
DIPLAY_QEMU_CPU=qemu32,+ssse3,+sse4.1,+sse4.2 DIPLAY_TEST_KIND=decoder DIPLAY_TEST_PACKAGE=com.diplay.decodercheck DIPLAY_TEST_APK=<absolute path to decodercheck-debug.apk> python3 scripts/recovery/test_emulator.py
```
需先依 scripts/recovery 安裝 JDK、Gradle、SDK 與模擬器。decodercheck 為 opt-in 獨立測試 App，不包含 accessory 認證資產，也不是車機主程式 APK。

必需 CI 命令已執行：與上一輪相同，14 個 ExistingWifiManagerTest 因環境缺少 non-loopback 介面失敗。其餘單元測試、三個主要 APK 的建置與 lint 通過；獨立 decodercheck APK 建置成功。

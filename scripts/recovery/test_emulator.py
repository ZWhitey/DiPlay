"""Keep ADB and emulator in the same process namespace; report observed checks only."""
import json
import os
from pathlib import Path
import subprocess
import time
import re
import xml.etree.ElementTree as ET
import signal

root = Path(__file__).resolve().parents[2]
cache = root / 'runtime-cache'
sdk = cache / 'sdk'
avd = cache / 'avd'
avd_name = os.environ.get('DIPLAY_TEST_AVD', 'diplay23-' + str(int(time.time())))
device = avd / (avd_name + '.avd')
device.mkdir(parents=True, exist_ok=True)
(avd / (avd_name + '.ini')).write_text(f'avd.ini.encoding=UTF-8\npath={device}\ntarget=android-23\n')
(device / 'config.ini').write_text(f'''avd.ini.encoding=UTF-8
AvdId={avd_name}
abi.type=x86
image.sysdir.1={sdk}/system-images/android-23/default/x86/
hw.cpu.arch=x86
hw.cpu.ncore=1
hw.ramSize=1024
hw.lcd.width=1024
hw.lcd.height=600
hw.lcd.density=160
hw.gpu.enabled=yes
hw.gpu.mode=swiftshader
disk.dataPartition.size=2G
showDeviceFrame=no
''')
env = os.environ.copy()
env.update(ANDROID_HOME=str(sdk), ANDROID_AVD_HOME=str(avd), ANDROID_EMULATOR_HOME=str(cache / 'emulator-home'))
env['ANDROID_I_WANT_MY_TCG'] = 'yes'
env['LD_LIBRARY_PATH'] = '/tmp/diplay-emulator-libs/usr/lib/x86_64-linux-gnu:' + env.get('LD_LIBRARY_PATH', '')
adb = str(sdk / 'platform-tools/adb')
result = {'android_api': 23, 'configured_ram_mb': 1024, 'kvm': False, 'boot_completed': False, 'installation': None, 'launch': None, 'fps_verified': False}
def run(*args, timeout=20):
    try:
        return subprocess.run([adb, *args], env=env, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None

emulator = None
log = (cache / 'emulator-test.log').open('w')
try:
    run('start-server')
    emulator = subprocess.Popen([str(sdk / 'emulator/emulator'), '-avd', avd_name, '-read-only', '-no-window', '-no-audio', '-no-boot-anim', '-no-snapshot', '-no-metrics', '-accel', 'off', '-gpu', 'swiftshader', '-memory', '1024', '-cores', '1', '-port', '5554'], env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    start = time.monotonic()
    while time.monotonic() - start < 360:
        if emulator.poll() is not None:
            result['emulator_exit_code'] = emulator.returncode
            break
        state = run('-s', 'emulator-5554', 'shell', 'getprop', 'sys.boot_completed', timeout=8)
        if state and state.stdout.strip() == b'1':
            result['boot_completed'] = True
            break
        print(f'Android 6 boot: {int(time.monotonic()-start)} seconds, not completed', flush=True)
        time.sleep(15)
    if result['boot_completed']:
        apk = root / 'mobile/build/outputs/apk/debug/mobile-debug.apk'
        start = time.monotonic()
        while not apk.exists() and time.monotonic() - start < 360:
            print('Waiting for current APK build', flush=True)
            time.sleep(15)
        if apk.exists():
            run('-s', 'emulator-5554', 'root')
            run('-s', 'emulator-5554', 'wait-for-device')
            run('-s', 'emulator-5554', 'shell', 'setprop', 'dalvik.vm.dex2oat-filter', 'interpret-only')
            run('-s', 'emulator-5554', 'logcat', '-c')
            print('Installing current APK (software CPU, up to 600 seconds)', flush=True)
            installed = run('-s', 'emulator-5554', 'install', '-r', str(apk), timeout=600)
            result['installation'] = installed.stdout.decode(errors='replace') if installed else 'timeout'
            print('Installation:', result['installation'], flush=True)
            launched = run('-s', 'emulator-5554', 'shell', 'monkey', '-p', 'com.shihab.diplay.android6fix2', '-c', 'android.intent.category.LAUNCHER', '1', timeout=60)
            result['launch'] = launched.stdout.decode(errors='replace') if launched else 'timeout'
            time.sleep(20)
            def click_text(labels):
                run('-s', 'emulator-5554', 'shell', 'uiautomator', 'dump', '/sdcard/ui.xml', timeout=30)
                xml = run('-s', 'emulator-5554', 'shell', 'cat', '/sdcard/ui.xml')
                if not xml or not xml.stdout.strip(): return False
                try:
                    for node in ET.fromstring(xml.stdout).iter('node'):
                        if node.get('text', '').strip().lower() not in labels: continue
                        coordinates = list(map(int, re.findall(r'\d+', node.get('bounds', ''))))
                        if len(coordinates) != 4: continue
                        x1, y1, x2, y2 = coordinates
                        run('-s', 'emulator-5554', 'shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))
                        time.sleep(5)
                        return True
                except ET.ParseError:
                    pass
                return False
            result['skipped_setup'] = click_text({'skip setup', 'skip', '略過設定'})
            result['settings_button_clicked'] = click_text({'settings', '設定'})
            alive = run('-s', 'emulator-5554', 'shell', 'pidof', 'com.shihab.diplay.android6fix2')
            result['process_alive'] = bool(alive and alive.returncode == 0 and re.fullmatch(rb'[\d\s]+', alive.stdout.strip()))
            for name, command in [('logcat.txt', ['logcat', '-d']), ('activities.txt', ['shell', 'dumpsys', 'activity', 'activities']), ('memory.txt', ['shell', 'dumpsys', 'meminfo', 'com.shihab.diplay.android6fix2'])]:
                output = run('-s', 'emulator-5554', *command)
                if output: (cache / name).write_bytes(output.stdout)
            screenshot = run('-s', 'emulator-5554', 'exec-out', 'screencap', '-p')
            if screenshot: (cache / 'emulator-screen.png').write_bytes(screenshot.stdout)
            run('-s', 'emulator-5554', 'shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
            run('-s', 'emulator-5554', 'pull', '/sdcard/ui.xml', str(cache / 'ui.xml'))
        else:
            result['installation'] = 'Current APK was not built'
finally:
    (cache / 'emulator-result.json').write_text(json.dumps(result, indent=2))
    if emulator and emulator.poll() is None:
        run('-s', 'emulator-5554', 'emu', 'kill')
        try: os.killpg(emulator.pid, signal.SIGTERM)
        except ProcessLookupError: pass
        try: emulator.wait(timeout=15)
        except subprocess.TimeoutExpired: emulator.kill(); emulator.wait()
    run('kill-server')
    log.close()
print(json.dumps(result), flush=True)

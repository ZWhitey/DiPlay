"""Build behind the runtime proxy; keep private runtime assets outside the public tree."""
import os
from pathlib import Path
import subprocess
import sys
import urllib.parse
import zipfile
import shutil
import tempfile

root = Path(__file__).resolve().parents[2]
env = os.environ.copy()
env['ANDROID_HOME'] = str(root / 'runtime-cache/sdk')
env['GRADLE_USER_HOME'] = str(root / 'runtime-cache/gradle')
jdks = list((root / 'runtime-cache/jdk').glob('jdk-*'))
if jdks:
    env['JAVA_HOME'] = str(jdks[0])
    env['PATH'] = str(jdks[0] / 'bin') + ':' + env['PATH']
proxy = urllib.parse.urlparse(env.get('HTTPS_PROXY', ''))
if proxy.hostname:
    opts = ' '.join(f'-D{scheme}.proxyHost={proxy.hostname} -D{scheme}.proxyPort={proxy.port}' for scheme in ['http', 'https'])
    env['JAVA_TOOL_OPTIONS'] = opts + ' -Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts'
    env['GRADLE_OPTS'] = env['JAVA_TOOL_OPTIONS']
temporary = Path(tempfile.mkdtemp(prefix='diplay-private-build-'))
try:
    apk = root.parent / 'upload/DiPlay-android8-standalone-debug.apk'
    with zipfile.ZipFile(apk) as source:
        for name in ['identity.pk8', 'certificate.p7b']:
            target = temporary / 'offline-mfi' / name
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(source.read('assets/offline-mfi/' + name))
            target.chmod(0o600)
    env['DIPLAY_AUTH_ASSETS_DIR'] = str(temporary)
    installed = root / 'runtime-cache/gradle-dist/gradle-9.5.0/bin/gradle'
    executable = installed if installed.exists() else root / 'gradlew'
    executable.chmod(0o755)
    result = subprocess.run([str(executable), '--no-daemon', '--no-configuration-cache', '--max-workers=2', '--continue', '--init-script', str(root / 'scripts/recovery/test-init.gradle'), *sys.argv[1:]], cwd=root, env=env)
finally:
    shutil.rmtree(temporary)
sys.exit(result.returncode)

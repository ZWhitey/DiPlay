"""Pinned Java/Gradle and Linux libraries for the headless emulator workflow."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import tarfile
import urllib.request
import zipfile

root = Path(__file__).resolve().parents[2] / 'runtime-cache'
root.mkdir(exist_ok=True)
def download(url, path, checksum=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(url, timeout=120) as source, path.open('wb') as output:
            shutil.copyfileobj(source, output, 1024 * 1024)
    if checksum: assert hashlib.sha256(path.read_bytes()).hexdigest() == checksum, path

jdk = root / 'jdk/temurin25.tar.gz'
download('https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25.0.3%2B9/OpenJDK25U-jdk_x64_linux_hotspot_25.0.3_9.tar.gz', jdk, '69264a7a211bf5029830d07bc3370f879769d62ebc5b5488e90c9343a2da0e1f')
with tarfile.open(jdk) as archive:
    archive.extractall(jdk.parent, filter='data')
gradle = root / 'gradle-dist/gradle-9.5.0-bin.zip'
download('https://services.gradle.org/distributions/gradle-9.5.0-bin.zip', gradle, '553c78f50dafcd54d65b9a444649057857469edf836431389695608536d6b746')
with zipfile.ZipFile(gradle) as archive: archive.extractall(gradle.parent)
(gradle.parent / 'gradle-9.5.0/bin/gradle').chmod(0o755)
for name, url in {
    'libxkbfile1': 'https://archive.ubuntu.com/ubuntu/pool/main/libx/libxkbfile/libxkbfile1_1.1.0-1build5_amd64.deb',
    'libxtst6': 'https://archive.ubuntu.com/ubuntu/pool/main/libx/libxtst/libxtst6_1.2.3-1.1build1_amd64.deb',
}.items():
    path = root / (name + '.deb')
    download(url, path)
    subprocess.run(['dpkg-deb', '-x', str(path), '/tmp/diplay-emulator-libs'], check=True)
print('Host tools installed')

"""Recreate the Android 6 test runtime from Google's signed repository metadata."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2] / 'runtime-cache'
SDK = ROOT / 'sdk'
PACKAGES = {
    'platforms;android-37.0': 'platforms/android-37.0',
    'ndk;28.2.13676358': 'ndk/28.2.13676358',
    'build-tools;36.0.0': 'build-tools/36.0.0',
    'platform-tools': 'platform-tools',
    'emulator': 'emulator',
    'system-images;android-23;default;x86': 'system-images/android-23/default/x86',
}

def install(item):
    name, url, checksum, destination = item
    destination = SDK / destination
    if (destination / 'source.properties').exists():
        print('reusing', name, flush=True)
        return
    archive = ROOT / ('download-' + name.replace(';', '-') + '.zip')
    print('downloading', name, flush=True)
    if not archive.exists():
        with urllib.request.urlopen(url, timeout=120) as response, archive.open('wb') as output:
            shutil.copyfileobj(response, output, 1024 * 1024)
    assert hashlib.sha1(archive.read_bytes()).hexdigest() == checksum, name
    temporary = ROOT / ('unpack-' + name.replace(';', '-'))
    temporary.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(temporary)
        for entry in bundle.infolist():
            permissions = entry.external_attr >> 16
            if stat.S_ISLNK(permissions):
                target = temporary / entry.filename
                target.unlink()
                target.symlink_to(bundle.read(entry).decode())
                continue
            if permissions:
                os.chmod(temporary / entry.filename, permissions)
    sources = list(temporary.iterdir())
    source = sources[0] if len(sources) == 1 and sources[0].is_dir() else temporary
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    print('installed', name, flush=True)

if __name__ == '__main__':
    ROOT.mkdir(exist_ok=True)
    items = []
    for metadata in ['repository2-3.xml', 'sys-img/android/sys-img2-3.xml']:
        prefix = 'https://dl.google.com/android/repository/'
        raw = urllib.request.urlopen(prefix + metadata, timeout=60).read()
        (ROOT / metadata.split('/')[-1]).write_bytes(raw)
        for package in ET.fromstring(raw).findall('remotePackage'):
            name = package.attrib['path']
            if name not in PACKAGES or any(i[0] == name for i in items):
                continue
            for archive in package.findall('archives/archive'):
                if archive.findtext('host-os') not in (None, 'linux'):
                    continue
                relative = archive.findtext('complete/url')
                source = prefix + (metadata.rsplit('/', 1)[0] + '/' if '/' in metadata else '') + relative
                items.append((name, source, archive.findtext('complete/checksum'), PACKAGES[name]))
                break
    (ROOT / 'packages.json').write_text(json.dumps(items, indent=2))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(install, items))
    licenses = SDK / 'licenses'
    licenses.mkdir(exist_ok=True)
    (licenses / 'android-sdk-license').write_text('8933bad161af4178b1185d1a37fbf41ea5269c55\nd56f5187479451eabf01fb78af6dfcb131a6481e\n24333f8a63b6825ea9c5514f83c2829b004d1fee\n')

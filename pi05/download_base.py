"""Download the pi05_base weights into openpi's cache, checking every file against its CRC32C:

  .venv/bin/python ../AIRLAB/pi05/download_base.py

openpi fetches them with gsutil, which on Colab refuses the six largest files (composite objects
need crcmod's C extension to check). Once they are in the cache openpi does not download them.
Files already downloaded intact are kept, so this can simply be run again after a failure.
"""

import base64
import concurrent.futures
import json
import pathlib
import shutil
import urllib.request

import google_crc32c
from openpi.shared import download

BUCKET = 'https://storage.googleapis.com/openpi-assets'
PREFIX = 'checkpoints/pi05_base/params'
LISTING = ('https://storage.googleapis.com/storage/v1/b/openpi-assets/o'
           f'?prefix={PREFIX}/&fields=items(name,size,crc32c)')
BLOCK = 1 << 24
ATTEMPTS = 3


def crc32c(path):
    crc = google_crc32c.Checksum()
    with open(path, 'rb') as f:
        while block := f.read(BLOCK):
            crc.update(block)
    return base64.b64encode(crc.digest()).decode()


def fetch(item, root):
    """Download one bucket object under root unless it is already there and intact."""
    path = pathlib.Path(root) / item['name'].removeprefix(f'{PREFIX}/')
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(ATTEMPTS):
        if path.exists() and path.stat().st_size == int(item['size']) and crc32c(path) == item['crc32c']:
            return int(item['size'])
        try:
            with urllib.request.urlopen(f'{BUCKET}/{item["name"]}') as response, open(path, 'wb') as f:
                shutil.copyfileobj(response, f, BLOCK)
        except OSError as e:
            print(f'{path.name}: {e}, attempt {attempt + 1}/{ATTEMPTS}', flush=True)
    raise SystemExit(f'{item["name"]} could not be downloaded intact')


def main():
    target = download.get_cache_dir() / 'openpi-assets' / PREFIX
    if target.exists():
        print(f'already there: {target}')
        return
    items = json.load(urllib.request.urlopen(LISTING))['items']
    partial = target.with_suffix('.partial')
    print(f'{len(items)} files, {sum(int(i["size"]) for i in items) / 1e9:.1f} GB', flush=True)
    done = 0
    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        for size in pool.map(lambda item: fetch(item, partial), items):
            done += size
            print(f'{done / 1e9:.1f} GB checked', flush=True)
    partial.rename(target)
    print(f'done: {target}')


if __name__ == '__main__':
    main()

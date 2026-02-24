#!/usr/bin/env python3
"""regression test for gcloud updater archive safety and checksum verification.

this is a standalone test that loads installers.py with minimal import stubs,
so it can run without the full gcloud sdk runtime environment.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import os
import shutil
import sys
import tarfile
import tempfile
import types
from pathlib import Path


def _stub_mod(name: str, *, is_pkg: bool = False, **attrs: object) -> types.ModuleType:
  mod = types.ModuleType(name)
  if is_pkg:
    mod.__path__ = []  # type: ignore[attr-defined]
  for key, value in attrs.items():
    setattr(mod, key, value)
  sys.modules[name] = mod
  return mod


def _install_import_stubs() -> None:
  _stub_mod('googlecloudsdk', is_pkg=True)
  _stub_mod('googlecloudsdk.core', is_pkg=True)
  _stub_mod('googlecloudsdk.core.console', is_pkg=True)
  _stub_mod('googlecloudsdk.core.credentials', is_pkg=True)
  _stub_mod('googlecloudsdk.core.util', is_pkg=True)
  _stub_mod('googlecloudsdk.core.updater', is_pkg=True)

  class _Error(Exception):
    pass

  class _BinaryWriter:
    def __init__(self, path: str):
      self._path = path
      self._fp = None

    def __enter__(self):
      self._fp = open(self._path, 'wb')
      return self._fp

    def __exit__(self, exc_type, exc, tb):
      if self._fp:
        self._fp.close()

  class _BinaryReader:
    def __init__(self, path: str):
      self._path = path
      self._fp = None

    def __enter__(self):
      self._fp = open(self._path, 'rb')
      return self._fp

    def __exit__(self, exc_type, exc, tb):
      if self._fp:
        self._fp.close()

  _stub_mod('googlecloudsdk.core.exceptions', Error=_Error)
  _stub_mod('googlecloudsdk.core.local_file_adapter', LocalFileAdapter=object)
  _stub_mod(
      'googlecloudsdk.core.log',
      debug=lambda *a, **k: None,
      info=lambda *a, **k: None,
      warning=lambda *a, **k: None,
      error=lambda *a, **k: None,
  )
  _stub_mod(
      'googlecloudsdk.core.properties',
      VALUES=types.SimpleNamespace(
          core=types.SimpleNamespace(
              account=types.SimpleNamespace(Get=lambda: 'test'),
          )
      ),
  )
  _stub_mod('googlecloudsdk.core.transport', MakeUserAgentString=lambda _: 'ua')
  _stub_mod(
      'googlecloudsdk.core.console.console_io',
      DefaultProgressBarCallback=lambda *_: None,
  )
  _stub_mod('googlecloudsdk.core.credentials.exceptions', Error=Exception)
  _stub_mod(
      'googlecloudsdk.core.util.files',
      MakeDir=lambda p: os.makedirs(p, exist_ok=True),
      BinaryFileWriter=_BinaryWriter,
      BinaryFileReader=_BinaryReader,
  )
  _stub_mod('googlecloudsdk.core.util.http_encoding', Encode=lambda x: x)
  _stub_mod('googlecloudsdk.core.util.retry', Retryer=object, RetryException=Exception)


def load_installers_module(installers_path: str) -> types.ModuleType:
  _install_import_stubs()
  module_name = 'googlecloudsdk.core.updater.installers'
  spec = importlib.util.spec_from_file_location(module_name, installers_path)
  if spec is None or spec.loader is None:
    raise RuntimeError('failed to load installers module spec')
  module = importlib.util.module_from_spec(spec)
  sys.modules[module_name] = module
  spec.loader.exec_module(module)
  return module


def _test_tar_traversal_blocked(installers: types.ModuleType, workdir: str) -> None:
  extract_dir = os.path.join(workdir, 'extract')
  os.makedirs(extract_dir, exist_ok=True)
  tar_path = os.path.join(workdir, 'payload.tar.gz')
  with tarfile.open(tar_path, 'w:gz') as tf:
    payload = b'pwned\n'
    info = tarfile.TarInfo('../escaped.txt')
    info.size = len(payload)
    tf.addfile(info, fileobj=io.BytesIO(payload))

  escaped_path = os.path.realpath(os.path.join(extract_dir, '..', 'escaped.txt'))
  if os.path.exists(escaped_path):
    os.remove(escaped_path)

  try:
    installers.ExtractTar(tar_path, extract_dir, progress_callback=lambda _: None)
  except Exception:
    pass
  else:
    raise AssertionError('expected ExtractTar to reject traversal member')

  if os.path.exists(escaped_path):
    raise AssertionError('traversal file was created outside extraction directory')


def _test_checksum_mismatch_rejected(installers: types.ModuleType, workdir: str) -> None:
  archive_path = os.path.join(workdir, 'downloaded.tar.gz')
  with open(archive_path, 'wb') as f:
    f.write(b'not-a-real-archive')

  original_download = installers.DownloadTar

  def _fake_download(*args, **kwargs):
    return archive_path

  installers.DownloadTar = _fake_download
  try:
    component = types.SimpleNamespace(
        id='alpha',
        data=types.SimpleNamespace(
            type='tar',
            source='https://example.test/alpha.tar.gz',
            checksum='0' * 64,
        ),
    )
    installer = installers.ComponentInstaller(
        sdk_root=os.path.join(workdir, 'sdk-root'),
        state_directory=os.path.join(workdir, 'state-dir'),
    )
    os.makedirs(os.path.join(workdir, 'state-dir'), exist_ok=True)

    try:
      installer._DownloadTar(  # pylint: disable=protected-access
          component,
          progress_callback=lambda _: None,
          command_path='test',
      )
    except installers.ComponentDownloadFailedError:
      pass
    else:
      raise AssertionError('expected checksum mismatch to raise ComponentDownloadFailedError')
  finally:
    installers.DownloadTar = original_download


def main() -> int:
  ap = argparse.ArgumentParser()
  ap.add_argument('--repo', required=False, default='', help='path to repo root')
  ap.add_argument('--installers-file', required=False, default='', help='path to installers.py')
  args = ap.parse_args()

  installers_path = args.installers_file
  if not installers_path:
    repo_root = Path(args.repo) if args.repo else Path(__file__).resolve().parents[5]
    installers_path = str(
        repo_root
        / 'lib'
        / 'googlecloudsdk'
        / 'core'
        / 'updater'
        / 'installers.py'
    )

  installers = load_installers_module(installers_path)

  workdir = tempfile.mkdtemp(prefix='gcloud_regress_')
  try:
    _test_tar_traversal_blocked(installers, workdir)
    _test_checksum_mismatch_rejected(installers, workdir)
  finally:
    shutil.rmtree(workdir, ignore_errors=True)

  print('[REGRESSION_OK] traversal_blocked=true checksum_mismatch_rejected=true')
  return 0


if __name__ == '__main__':
  raise SystemExit(main())


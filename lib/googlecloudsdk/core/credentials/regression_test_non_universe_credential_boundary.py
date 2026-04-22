#!/usr/bin/env python3
"""regression test for non-universe credential attachment blocking."""

from __future__ import annotations

import argparse
import importlib.util
import sys
import types
from pathlib import Path


def _stub_mod(
    name: str, *, is_pkg: bool = False, **attrs: object
) -> types.ModuleType:
  mod = types.ModuleType(name)
  if is_pkg:
    mod.__path__ = []  # type: ignore[attr-defined]
  for key, value in attrs.items():
    setattr(mod, key, value)
  sys.modules[name] = mod
  return mod


def _install_import_stubs() -> types.SimpleNamespace:
  _stub_mod('googlecloudsdk', is_pkg=True)
  _stub_mod('googlecloudsdk.core', is_pkg=True)
  _stub_mod('googlecloudsdk.core.credentials', is_pkg=True)
  _stub_mod('googlecloudsdk.core.util', is_pkg=True)
  _stub_mod('google', is_pkg=True)
  _stub_mod('google.auth', is_pkg=True)

  class _Error(Exception):
    pass

  override_state = types.SimpleNamespace(
      allow_non_universe=False, universe_domain='googleapis.com'
  )

  _stub_mod('googlecloudsdk.core.context_aware')
  _stub_mod('googlecloudsdk.core.exceptions', Error=_Error)
  _stub_mod(
      'googlecloudsdk.core.log',
      debug=lambda *a, **k: None,
      info=lambda *a, **k: None,
      warning=lambda *a, **k: None,
      error=lambda *a, **k: None,
  )
  _stub_mod(
      'googlecloudsdk.core.properties',
      GetUniverseDomain=lambda: override_state.universe_domain,
      VALUES=types.SimpleNamespace(
          core=types.SimpleNamespace(
              allow_non_universe_credentialed_endpoints=types.SimpleNamespace(
                  GetBool=lambda: override_state.allow_non_universe
              )
          )
      ),
  )
  _stub_mod('googlecloudsdk.core.transport')
  _stub_mod('googlecloudsdk.core.credentials.creds')
  _stub_mod('googlecloudsdk.core.credentials.exceptions')
  _stub_mod('googlecloudsdk.core.credentials.store')
  _stub_mod('googlecloudsdk.core.util.files')
  _stub_mod('google.auth.exceptions', RefreshError=Exception)

  return override_state


def load_transport_module(
    transport_path: str,
) -> tuple[types.ModuleType, types.SimpleNamespace]:
  override_state = _install_import_stubs()
  module_name = 'googlecloudsdk.core.credentials.transport'
  spec = importlib.util.spec_from_file_location(module_name, transport_path)
  if spec is None or spec.loader is None:
    raise RuntimeError('failed to load transport module spec')
  module = importlib.util.module_from_spec(spec)
  sys.modules[module_name] = module
  spec.loader.exec_module(module)
  return module, override_state


def _test_googleapis_url_allowed(transport_module: types.ModuleType) -> None:
  transport_module.ValidateCredentialedRequestUrl(
      'https://compute.googleapis.com/compute/v1/projects/p'
  )


def _test_non_universe_url_blocked(transport_module: types.ModuleType) -> None:
  try:
    transport_module.ValidateCredentialedRequestUrl(
        'https://attacker.example/compute/v1/projects/p'
    )
  except Exception as exc:  # pylint: disable=broad-except
    if 'allow_non_universe_credentialed_endpoints' not in str(exc):
      raise AssertionError(
          'unexpected error message: {}'.format(exc)
      ) from exc
    return
  raise AssertionError('expected non-universe credentialed URL to be rejected')


def _test_non_universe_url_opt_in(
    transport_module: types.ModuleType, override_state: types.SimpleNamespace
) -> None:
  override_state.allow_non_universe = True
  try:
    transport_module.ValidateCredentialedRequestUrl(
        'https://attacker.example/compute/v1/projects/p'
    )
  finally:
    override_state.allow_non_universe = False


def main() -> int:
  ap = argparse.ArgumentParser()
  ap.add_argument(
      '--repo', required=False, default='', help='path to repo root'
  )
  ap.add_argument(
      '--transport-file',
      required=False,
      default='',
      help='path to core/credentials/transport.py',
  )
  args = ap.parse_args()

  transport_path = args.transport_file
  if not transport_path:
    repo_root = Path(args.repo) if args.repo else Path(__file__).resolve().parents[5]
    transport_path = str(
        repo_root
        / 'lib'
        / 'googlecloudsdk'
        / 'core'
        / 'credentials'
        / 'transport.py'
    )

  transport_module, override_state = load_transport_module(transport_path)

  _test_googleapis_url_allowed(transport_module)
  _test_non_universe_url_blocked(transport_module)
  _test_non_universe_url_opt_in(transport_module, override_state)

  print(
      '[REGRESSION_OK] googleapis_url=true '
      'non_universe_blocked=true opt_in_override=true'
  )
  return 0


if __name__ == '__main__':
  raise SystemExit(main())

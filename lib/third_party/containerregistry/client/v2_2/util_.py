"""This package holds a handful of utilities for manipulating manifests."""



import hashlib

from containerregistry.client import typing  # pylint: disable=unused-import


class BadManifestException(Exception):
  """Exception type raised when a malformed manifest is encountered."""


def Digest(manifest):
  """Compute the digest of the manifest."""
  return 'sha256:' + hashlib.sha256(manifest).hexdigest()


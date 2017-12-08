"""This package provides DockerImage for examining docker_build outputs."""

import abc
import binascii
import cStringIO
import hashlib
import httplib
import json
import os
import tarfile
from containerregistry.client import docker_name
from containerregistry.client.v2 import docker_http
from containerregistry.client.v2 import util


class DockerImage(object):
  """Interface for implementations that interact with Docker images."""

  __metaclass__ = abc.ABCMeta  # For enforcing that methods are overriden.

  def fs_layers(self):
    """The ordered collection of filesystem layers that comprise this image."""
    manifest = json.loads(self.manifest())
    return [x['blobSum'] for x in manifest['fsLayers']]

  def blob_set(self):
    """The unique set of blobs that compose to create the filesystem."""
    return set(self.fs_layers())

  @abc.abstractmethod
  def manifest(self):
    """The JSON manifest referenced by the tag/digest.

    Returns:
      The raw json manifest
    """

  @abc.abstractmethod
  def blob(self, digest):
    """The raw blob of the layer.

    Args:
      digest: str, the 'algo:digest' of the layer being addressed.

    Returns:
      The raw blob string of the layer.
    """

  # __enter__ and __exit__ allow use as a context manager.
  @abc.abstractmethod
  def __enter__(self):
    """Open the image for reading."""

  @abc.abstractmethod
  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Close the image."""


class FromRegistry(DockerImage):
  """This accesses a docker image hosted on a registry (non-local)."""

  def __init__(self, name, basic_creds, transport):
    self._name = name
    self._creds = basic_creds
    self._original_transport = transport
    self._response = {}

  def _content(self, suffix):
    """Fetches content of the resources from registry by http calls."""
    if not isinstance(self._name, docker_name.Repository):
      raise ValueError('Expected docker_name.Repository for "name"')

    if suffix not in self._response:
      _, self._response[suffix] = self._transport.Request(
          '{scheme}://{registry}/v2/{repository}/{suffix}'.format(
              scheme=docker_http.Scheme(self._name.registry),
              registry=self._name.registry,
              repository=self._name.repository,
              suffix=suffix),
          accepted_codes=[httplib.OK])
    return self._response[suffix]

  def _tags(self):
    # See //cloud/containers/registry/proto/v2/tags.proto
    # for the full response structure.
    return json.loads(self._content('tags/list'))

  def tags(self):
    return self._tags().get('tags', [])

  def manifests(self):
    payload = self._tags()
    if 'manifest' not in payload:
      # Only GCR supports this schema.
      return {}
    return payload['manifest']

  def children(self):
    payload = self._tags()
    if 'child' not in payload:
      # Only GCR supports this schema.
      return []
    return payload['child']

  def exists(self):
    try:
      self.manifest()
      return True
    except docker_http.V2DiagnosticException:
      # TODO(user): Check for 404
      return False

  def manifest(self):
    """Override."""
    # GET server1/v2/<name>/manifests/<tag_or_digest>
    if isinstance(self._name, docker_name.Tag):
      return self._content('manifests/' + self._name.tag)
    else:
      assert isinstance(self._name, docker_name.Digest)
      return self._content('manifests/' + self._name.digest)

  # Large, do not memoize.
  def blob(self, digest):
    """Override."""
    # GET server1/v2/<name>/blobs/<digest>
    return self._content('blobs/' + digest)

  def catalog(self, page_size=100):
    # TODO(user): Handle docker_name.Repository for /v2/<name>/_catalog
    if isinstance(self._name, docker_name.Repository):
      raise ValueError('Expected docker_name.Registry for "name"')

    url = '{scheme}://{registry}/v2/_catalog?n={page_size}'.format(
        scheme=docker_http.Scheme(self._name.registry),
        registry=self._name.registry,
        page_size=page_size)

    for _, content in self._transport.PaginatedRequest(
        url, accepted_codes=[httplib.OK]):
      wrapper_object = json.loads(content)

      if 'repositories' not in wrapper_object:
        raise docker_http.BadStateException(
            'Malformed JSON response: %s' % content)

      for repo in wrapper_object['repositories']:
        yield repo

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    # Create a v2 transport to use for making authenticated requests.
    self._transport = docker_http.Transport(
        self._name, self._creds, self._original_transport, docker_http.PULL)

    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass


def _in_whiteout_dir(fs, name):
  while name:
    dirname = os.path.dirname(name)
    if name == dirname:
      break
    if fs.get(dirname):
      return True
    name = dirname
  return False

_WHITEOUT_PREFIX = '.wh.'


def extract(image, tar):
  """Extract the final filesystem from the image into tar.

  Args:
    image: a DockerImage whose final filesystem to construct.
    tar: the tarfile.TarInfo into which we are writing the final filesystem.
  """
  # Maps all of the files we have already added (and should never add again)
  # to whether they are a tombstone or not.
  fs = {}

  # Walk the layers, topmost first and add files.  If we've seen them in a
  # higher layer then we skip them.
  for layer in image.fs_layers():
    buf = cStringIO.StringIO(image.blob(layer))
    with tarfile.open(mode='r:gz', fileobj=buf) as layer_tar:
      for member in layer_tar.getmembers():
        # If we see a whiteout file, then don't add anything to the tarball
        # but ensure that any lower layers don't add a file with the whited
        # out name.
        basename = os.path.basename(member.name)
        dirname = os.path.dirname(member.name)
        tombstone = basename.startswith(_WHITEOUT_PREFIX)
        if tombstone:
          basename = basename[len(_WHITEOUT_PREFIX):]

        # Before adding a file, check to see whether it (or its whiteout) have
        # been seen before.
        name = os.path.normpath(os.path.join('.', dirname, basename))
        if name in fs:
          continue

        # Check for a whited out parent directory
        if _in_whiteout_dir(fs, name):
          continue

        # Mark this file as handled by adding its name.
        # A non-directory implicitly tombstones any entries with
        # a matching (or child) name.
        fs[name] = tombstone or not member.isdir()
        if not tombstone:
          if member.isfile():
            tar.addfile(member, fileobj=layer_tar.extractfile(member.name))
          else:
            tar.addfile(member, fileobj=None)

# _EMPTY_LAYER_TAR_ID is the sha256 of an empty tarball.
_EMPTY_LAYER_TAR_ID = (
    'sha256:'
    'a3ed95caeb02ffe68cdd9fd84406680ae93d633cb16422d00e8a7c22955b46d4')


class AppendLayer(DockerImage):
  """Appends a new layer on top of a base image.

  This augments a base docker image with new files from a gzipped tarball,
  adds environment variables and exposes a port.
  """

  def __init__(self, base, tar_gz, port, *envs):
    """Creates a new layer on top of a base with optional tar.gz, port or envs.

    Args:
      base: a base DockerImage for a new layer.
      tar_gz: an optional gzipped tarball passed as a string with filesystem
          changeset.
      port: an optional port to be exposed, passed as a string. For example:
          '8080/tcp'.
      *envs: environment variables passed as strings in the format:
          'ENV_ONE=val', 'ENV_TWO=val2'.
    """
    self._base = base

    if tar_gz is None:
      self._blob_sum = _EMPTY_LAYER_TAR_ID
    else:
      self._blob = tar_gz
      self._blob_sum = 'sha256:' + hashlib.sha256(self._blob).hexdigest()

    unsigned_manifest, unused_signatures = util.DetachSignatures(
        self._base.manifest())
    manifest = json.loads(unsigned_manifest)
    manifest['fsLayers'].insert(0, {'blobSum': self._blob_sum})
    v1_compat = json.loads(manifest['history'][0]['v1Compatibility'])
    v1_compat['parent'] = v1_compat['id']
    v1_compat['id'] = binascii.hexlify(os.urandom(32))

    config = v1_compat.get('config', {}) or {}
    envs = list(envs)
    if envs:
      env_keys = [env.split('=')[0] for env in envs]
      old_envs = config.get('Env', []) or []
      old_envs = [env for env in old_envs if env.split('=')[0] not in env_keys]
      config['Env'] = old_envs + envs
    if port is not None:
      old_ports = config.get('ExposedPorts', {}) or {}
      old_ports[port] = {}
      config['ExposedPorts'] = old_ports
    v1_compat['config'] = config

    manifest['history'].insert(0, {'v1Compatibility': json.dumps(v1_compat)})
    self._manifest = util.Sign(json.dumps(manifest))

  def manifest(self):
    """Override."""
    return self._manifest

  def blob(self, digest):
    """Override."""
    if digest == self._blob_sum:
      return self._blob
    return self._base.blob(digest)

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    """Override."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Override."""
    return

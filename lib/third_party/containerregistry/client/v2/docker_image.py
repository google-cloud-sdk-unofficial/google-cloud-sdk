"""This package provides DockerImage for examining docker_build outputs."""

import abc
import httplib
import json
from containerregistry.client import docker_name
from containerregistry.client.v2 import docker_http


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


# TODO(user): We will need a FromTarball implementation once there is
# a specification for how to save/load a v2 image.
# class FromTarball(DockerImage):


class FromRegistry(DockerImage):
  """This accesses a docker image hosted on a registry (non-local)."""

  def __init__(self, name, basic_creds, transport):
    self._name = name
    self._creds = basic_creds
    self._original_transport = transport
    self._response = {}

  def _content(self, suffix):
    if suffix not in self._response:
      _, self._response[suffix] = self._transport.Request(
          'https://{registry}/v2/{repository}/{suffix}'.format(
              registry=self._name.registry,
              repository=self._name.repository,
              suffix=suffix),
          [httplib.OK])
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

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    # Create a v2 transport to use for making authenticated requests.
    self._transport = docker_http.Transport(
        self._name, self._creds, self._original_transport, docker_http.PULL)

    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass


# TODO(user): We need the ability to synthesize random images for probing
# the registry's v2 endpoints.
# class Random(DockerImage):

# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Wraps a Cloud Run revision message with convenience methods."""

import json

from apitools.base.protorpclite import messages
from apitools.base.py import encoding
from googlecloudsdk.api_lib.run import container_resource
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.run.v2 import run_v2_messages

# Label names as to be stored in k8s object metadata
SERVICE_LABEL = 'serving.knative.dev/service'
WORKER_POOL_LABEL = 'run.googleapis.com/workerPool'
# Used to force a new revision, and also to tie a particular request for changes
# to a particular created revision.
NONCE_LABEL = 'client.knative.dev/nonce'
MIN_SCALE_ANNOTATION = 'autoscaling.knative.dev/minScale'
MAX_SCALE_ANNOTATION = 'autoscaling.knative.dev/maxScale'
# gcloud-disable-gdu-domain
SESSION_AFFINITY_ANNOTATION = 'run.googleapis.com/sessionAffinity'
# gcloud-disable-gdu-domain
MESH_ANNOTATION = 'run.googleapis.com/mesh'
# gcloud-disable-gdu-domain
BASE_IMAGES_ANNOTATION = 'run.googleapis.com/base-images'
# gcloud-disable-gdu-domain
IDENTITY_ANNOTATION = 'run.googleapis.com/identity'
# gcloud-disable-gdu-domain
IDENTITY_CERTIFICATE_ENABLED_ANNOTATION = (
    'run.googleapis.com/identity-certificate-enabled'
)
# gcloud-disable-gdu-domain
IDENTITY_TYPE_ANNOTATION = 'run.googleapis.com/identity-type'
# gcloud-disable-gdu-domain
MESH_DATAPLANE_ANNOTATION = 'run.googleapis.com/mesh-dataplane'
# gcloud-disable-gdu-domain
BASE_IMAGE_UPDATE_RUNTIME_CLASS_NAME = (
    'run.googleapis.com/linux-base-image-update'
)
# gcloud-disable-gdu-domain
GPU_ZONAL_REDUNDANCY_DISABLED_ANNOTATION = (
    'run.googleapis.com/gpu-zonal-redundancy-disabled'
)
# gcloud-disable-gdu-domain
SOURCES_ANNOTATION = 'run.googleapis.com/sources'
# Annotation that contains a JSON-formatted string representing a map of
# (container name, BuildConfig) entries, where container name is either empty
# and corresponds to the ingress container or has a name and corresponds to
# the container with the same name, and BuildConfig is a JSON representation
# of a V2.Service.Template.Container.BuildConfig object.
# gcloud-disable-gdu-domain
BUILD_CONFIG_ANNOTATION = 'run.googleapis.com/build-config'
# If true, overflow scaling capabilities are enabled for this revision.
OVERFLOW_SCALING_ANNOTATION = 'run.googleapis.com/overflow-scaling'
# Annotation to set the CPU utilization target for scaling.
CPU_UTILIZATION_ANNOTATION = 'run.googleapis.com/scaling-cpu-target'
# Annotation to set the concurrency utilization target for scaling.
CONCURRENCY_UTILIZATION_ANNOTATION = (
    'run.googleapis.com/scaling-concurrency-target'
)
# gcloud-disable-gdu-domain
AMBIENT_NETWORKING_ANNOTATION = 'run.googleapis.com/ambient-networking'
# gcloud-disable-gdu-domain
AMBIENT_SCOPE_ANNOTATION = 'run.googleapis.com/ambient-scope'


def _ClearUnrecognizedFields(msg):
  """Recursively clears unrecognized fields from an apitools Message."""
  if not isinstance(msg, messages.Message):
    return
  setattr(msg, '_Message__unrecognized_fields', {})
  for field in msg.all_fields():
    val = getattr(msg, field.name, None)
    if isinstance(val, messages.Message):
      _ClearUnrecognizedFields(val)
    elif isinstance(val, list):
      for item in val:
        if isinstance(item, messages.Message):
          _ClearUnrecognizedFields(item)


def _ValidateBuildConfigDictTypes(val, message_type):
  """Validates that JSON values match expected apitools field types."""
  if not isinstance(val, dict):
    raise TypeError('Expected dict, got {}'.format(type(val)))
  for key, item in val.items():
    if item is None:
      continue
    try:
      field = message_type.field_by_name(key)
    except KeyError:
      continue
    if field.repeated:
      if not isinstance(item, list):
        raise TypeError('Expected list for repeated field {}'.format(key))
      if isinstance(field, messages.MessageField):
        for sub_item in item:
          if not isinstance(sub_item, dict):
            raise TypeError('Expected dict in list for {}'.format(key))
          _ValidateBuildConfigDictTypes(sub_item, field.message_type)
    elif isinstance(field, messages.MessageField):
      if not isinstance(item, dict):
        raise TypeError('Expected dict for message field {}'.format(key))
      _ValidateBuildConfigDictTypes(item, field.message_type)
    elif isinstance(field, messages.StringField):
      if not isinstance(item, str):
        raise TypeError('Expected str for string field {}'.format(key))


class Revision(container_resource.ContainerResource):
  """Wraps a Cloud Run Revision message, making fields more convenient."""

  API_CATEGORY = 'serving.knative.dev'
  KIND = 'Revision'
  READY_CONDITION = 'Ready'
  _ACTIVE_CONDITION = 'Active'
  TERMINAL_CONDITIONS = frozenset([
      READY_CONDITION,
  ])

  def __init__(self, *args, **kwargs):
    super(Revision, self).__init__(*args, **kwargs)
    self.DeserializeBuildConfig()

  @property
  def gcs_location(self):
    return self._m.status.gcs.location

  @property
  def service_name(self):
    return self.labels[SERVICE_LABEL] if SERVICE_LABEL in self.labels else None

  @property
  def worker_pool_name(self):
    return (
        self.labels[WORKER_POOL_LABEL]
        if WORKER_POOL_LABEL in self.labels
        else None
    )

  @property
  def serving_state(self):
    return self.spec.servingState

  @property
  def active(self):
    cond = self.conditions
    if self._ACTIVE_CONDITION in cond:
      return cond[self._ACTIVE_CONDITION]['status']
    return None

  @property
  def concurrency(self):
    """The concurrency number in the revisionTemplate.

    0: Multiple concurrency, max unspecified.
    1: Single concurrency
    n>1: Allow n simultaneous requests per instance.
    """
    return self.spec.containerConcurrency

  @concurrency.setter
  def concurrency(self, value):
    # Clear the old, deperecated string field
    try:
      self.spec.concurrencyModel = None
    except AttributeError:
      # This field only exists in the v1alpha1 spec, if we're working with a
      # different version, this is safe to ignore
      pass
    self.spec.containerConcurrency = value

  @property
  def timeout(self):
    """The timeout number in the revisionTemplate.

    The lib can accept either a duration format like '1m20s' or integer like
    '80' to set the timeout. The returned object is an integer value, which
    assumes second the unit, e.g., 80.
    """
    return self.spec.timeoutSeconds

  @timeout.setter
  def timeout(self, value):
    self.spec.timeoutSeconds = value

  @property
  def service_account(self):
    """The service account in the revisionTemplate."""
    return self.spec.serviceAccountName

  @service_account.setter
  def service_account(self, value):
    self.spec.serviceAccountName = value

  @property
  def image_digest(self):
    """The URL of the image, by digest. Stable when tags are not."""
    return self.status.imageDigest

  def _EnsureNodeSelector(self):
    if self.spec.nodeSelector is None:
      self.spec.nodeSelector = k8s_object.InitializedInstance(
          self._messages.RevisionSpec.NodeSelectorValue
      )

  @property
  def node_selector(self):
    """The node selector as a dictionary { accelerator_type: value}."""
    self._EnsureNodeSelector()
    return k8s_object.KeyValueListAsDictionaryWrapper(
        self.spec.nodeSelector.additionalProperties,
        self._messages.RevisionSpec.NodeSelectorValue.AdditionalProperty,
        key_field='key',
        value_field='value',
    )

  def DeserializeBuildConfig(self):
    """Deserializes container build configurations from annotations."""
    # Skip spec-only Revision objects (where metadata is None); accessing
    # `self.annotations` on a spec-only object raises ValueError via
    # AssertFullObject().
    if not self.IsFullObject():
      return
    if not getattr(self.spec, 'containers', None):
      return
    # Avoid accessing `self.annotations` if `metadata` or `metadata.annotations`
    # is None/empty, since `AnnotationsFromMetadata` mutates `metadata` by
    # attaching an empty `AnnotationsValue` message.
    if not getattr(self._m, 'metadata', None) or not getattr(
        self._m.metadata, 'annotations', None
    ):
      return
    if BUILD_CONFIG_ANNOTATION not in self.annotations:
      return
    raw_annotation = self.annotations.get(BUILD_CONFIG_ANNOTATION)
    if not raw_annotation:
      return
    try:
      build_config_map = json.loads(raw_annotation)
    except (ValueError, TypeError) as e:
      log.debug(
          'Failed to parse %s annotation as JSON: %s',
          BUILD_CONFIG_ANNOTATION,
          e,
      )
      return
    if not isinstance(build_config_map, dict):
      log.debug(
          'Invalid %s annotation format: expected dict, got %s',
          BUILD_CONFIG_ANNOTATION,
          type(build_config_map),
      )
      return

    for c in self.containers.values():
      # If `_build_config` is already set on the underlying container message,
      # do not overwrite it. This preserves in-memory mutations across repeated
      # instantiations of `Revision.Template` (e.g. accessing `service.template`
      # constructs a new `Revision.Template` which runs `__init__` and
      # `DeserializeBuildConfig()`; without this check, in-memory modifications
      # to `container.build_config` would be clobbered by the stale annotation).
      if c.HasBuildConfigState():
        continue
      key = c.name or ''
      if key in build_config_map:
        val = build_config_map[key]
        if isinstance(val, dict):
          try:
            _ValidateBuildConfigDictTypes(
                val, run_v2_messages.GoogleCloudRunV2BuildConfiguration
            )
            bc = encoding.DictToMessage(
                val, run_v2_messages.GoogleCloudRunV2BuildConfiguration
            )
            _ClearUnrecognizedFields(bc)
            c.build_config = bc
          except Exception as e:  # pylint: disable=broad-except
            log.debug(
                'Failed to deserialize build configuration for container [%s]:'
                ' %s',
                key,
                e,
            )
            c.build_config = None
        else:
          log.debug(
              'Invalid build configuration for container [%s]: expected dict,'
              ' got %s',
              key,
              type(val),
          )
          c.build_config = None
      else:
        # Mark as deserialized (None) so subsequent deserializations skip it.
        c.build_config = None

  def SerializeBuildConfig(self):
    """Serializes container build configurations to annotations."""
    # Skip spec-only Revision objects (where metadata is None); accessing
    # `self.annotations` on a spec-only object raises ValueError via
    # AssertFullObject().
    if not self.IsFullObject():
      return
    if not getattr(self.spec, 'containers', None):
      return

    # Defensively deserialize first so that if BUILD_CONFIG_ANNOTATION was
    # added to annotations after __init__, containers without in-memory
    # build_config state (HasBuildConfigState() == False) pick it up before
    # re-serializing.
    self.DeserializeBuildConfig()

    build_config_map = {}
    for c in self.containers.values():
      bc = c.build_config
      if bc is not None:
        key = c.name or ''
        build_config_map[key] = encoding.MessageToDict(bc)

    if build_config_map:
      self.annotations[BUILD_CONFIG_ANNOTATION] = json.dumps(
          build_config_map, sort_keys=True, separators=(',', ':')
      )
    elif (
        getattr(self._m, 'metadata', None)
        and getattr(self._m.metadata, 'annotations', None)
        and BUILD_CONFIG_ANNOTATION in self.annotations
    ):
      del self.annotations[BUILD_CONFIG_ANNOTATION]

  def Message(self):
    self.SerializeBuildConfig()
    return super(Revision, self).Message()

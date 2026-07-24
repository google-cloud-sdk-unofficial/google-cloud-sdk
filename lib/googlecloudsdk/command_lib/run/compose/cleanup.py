# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Helper class for discovering and deleting Compose resources."""

import abc
import contextlib
import os

from apitools.base.py import encoding
from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.util import apis as apis_util
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run.compose import compose_resource
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@contextlib.contextmanager
def SuppressApiEnablementPrompt():
  """Context manager to temporarily suppress gcloud API enablement prompts."""
  prop = properties.VALUES.core.should_prompt_to_enable_api
  old_value = prop.Get()
  prop.Set(False)
  try:
    yield
  finally:
    prop.Set(old_value)


class ResourceHandler(abc.ABC):
  """Abstract Base Class for managing individual resource lifecycles."""

  def __init__(self, project_id, region, sanitized_project_name):
    self.project_id = project_id
    self.region = region
    self.sanitized_project_name = sanitized_project_name
    self.api_disabled = False

  @abc.abstractmethod
  def Discover(self):
    """Queries Corresponding API and returns identified resource names.

    Returns:
      list[str]: A list of identified resource names/IDs.
    """
    pass

  @abc.abstractmethod
  def Delete(self, resource_names):
    """Deletes specified resources best-effort."""
    pass


class CloudRunServiceHandler(ResourceHandler):
  """Manages Cloud Run service teardown lifecycle."""

  def __init__(self, project_id, region, sanitized_project_name, conn_context):
    super(CloudRunServiceHandler, self).__init__(
        project_id, region, sanitized_project_name
    )
    self.conn_context = conn_context

  def Discover(self):
    namespace_ref = resources.REGISTRY.Parse(
        self.project_id,
        collection='run.namespaces',
    )
    with serverless_operations.Connect(self.conn_context) as client:
      label_selector = f'run-compose-project={self.sanitized_project_name}'
      with SuppressApiEnablementPrompt():
        try:
          services = client.ListServices(namespace_ref, label_selector)
          return [s.name for s in services]
        except api_exceptions.HttpError as e:
          if apis_util.GetApiEnablementInfo(e):
            self.api_disabled = True
          else:
            log.warning(f'Failed to list Cloud Run services: {e}')
          return []

  def Delete(self, resource_names):
    # To be implemented
    pass


class SecretManagerHandler(ResourceHandler):
  """Manages Secret Manager secrets teardown lifecycle."""

  def Discover(self):
    secrets_client = secrets_api.Secrets()
    project_ref = resources.REGISTRY.Parse(
        self.project_id,
        collection='cloudresourcemanager.projects',
    )
    request_filter = f'labels.run-compose-project:{self.sanitized_project_name}'
    with SuppressApiEnablementPrompt():
      try:
        secrets = secrets_client.ListWithPager(
            project_ref, limit=None, request_filter=request_filter
        )
        return [os.path.basename(s.name) for s in secrets]
      except api_exceptions.HttpError as e:
        if apis_util.GetApiEnablementInfo(e):
          self.api_disabled = True
        else:
          log.warning(f'Failed to list Secret Manager secrets: {e}')
        return []

  def Delete(self, resource_names):
    # To be implemented
    pass


class GcsBucketHandler(ResourceHandler):
  """Manages GCS Bucket teardown lifecycle."""

  def __init__(self, project_id, region, project_name, sanitized_project_name):
    super(GcsBucketHandler, self).__init__(
        project_id, region, sanitized_project_name
    )
    self.project_name = project_name

  def Discover(self):
    gcs_client = storage_api.StorageClient()
    with SuppressApiEnablementPrompt():
      try:
        bucket_name = compose_resource.generate_gcs_bucket_name(
            self.project_name, self.region
        )
        bucket = gcs_client.GetBucket(bucket_name)
        labels = encoding.MessageToDict(bucket.labels) if bucket.labels else {}
        if labels.get('run-compose-project') == self.sanitized_project_name:
          return [bucket_name]
        log.warning(
            f"Bucket '{bucket_name}' exists but does not carry the project"
            f" label '{self.sanitized_project_name}'. Skipping."
        )
        return []
      except storage_api.BucketNotFoundError:
        return []
      except api_exceptions.HttpError as e:
        if apis_util.GetApiEnablementInfo(e):
          self.api_disabled = True
        else:
          log.warning(f'Failed to check GCS bucket: {e}')
        return []

  def Delete(self, resource_names):
    # To be implemented
    pass


class ComposeTeardown(object):
  """Orchestrator for discovering and deleting all compose resources."""

  def __init__(
      self, project_name, region, project_id, conn_context, release_track
  ):
    self.project_name = project_name
    self.region = region
    self.project_id = project_id
    self.conn_context = conn_context
    self.release_track = release_track
    self.sanitized_project_name = compose_resource.sanitize_label_value(
        project_name
    )

    self.handlers = {
        'services': CloudRunServiceHandler(
            self.project_id,
            self.region,
            self.sanitized_project_name,
            self.conn_context,
        ),
        'secrets': SecretManagerHandler(
            self.project_id, self.region, self.sanitized_project_name
        ),
        'bucket': GcsBucketHandler(
            self.project_id,
            self.region,
            self.project_name,
            self.sanitized_project_name,
        ),
    }

  def Discover(self):
    """Queries APIs and returns discovered resources and disabled API statuses.

    Returns:
      tuple[dict, dict]:
        - dict: e.g. {'services': [...], 'secrets': [...], 'bucket': None|str}
        - dict: e.g. {'services': bool, 'secrets': bool, 'bucket': bool}
    """
    discovered = {
        'services': self.handlers['services'].Discover(),
        'secrets': self.handlers['secrets'].Discover(),
        'bucket': None,
    }
    buckets = self.handlers['bucket'].Discover()
    if buckets:
      discovered['bucket'] = buckets[0]

    disabled_apis = {
        'services': self.handlers['services'].api_disabled,
        'secrets': self.handlers['secrets'].api_disabled,
        'bucket': self.handlers['bucket'].api_disabled,
    }
    return discovered, disabled_apis

  def Delete(self, discovered_resources):
    """Best-effort deletion of all discovered resources."""
    # To be implemented
    pass

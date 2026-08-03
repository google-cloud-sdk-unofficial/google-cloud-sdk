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
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis as apis_util
from googlecloudsdk.command_lib.artifacts import requests as ar_requests
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run.compose import builder
from googlecloudsdk.command_lib.run.compose import compose_resource
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files

SERVICES_KEY = 'services'
SECRETS_KEY = 'secrets'
BUCKET_KEY = 'bucket'
FINGERPRINTS_KEY = 'fingerprints'
IMAGES_KEY = 'images'
AR_REPO_NAME = 'cloud-run-source-deploy'


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
    failures = []
    if not resource_names:
      return failures
    with serverless_operations.Connect(self.conn_context) as client:
      for name in resource_names:
        service_ref = resources.REGISTRY.Parse(
            name,
            params={'namespacesId': self.project_id},
            collection='run.namespaces.services',
        )
        try:
          client.DeleteService(service_ref)

        except (
            api_exceptions.HttpError,
            serverless_exceptions.ServiceNotFoundError,
        ) as e:
          log.warning(
              'Failed to delete Cloud Run service {}: {}'.format(name, e)
          )
          failures.append({
              'type': 'Cloud Run Service',
              'name': name,
              'error': str(e),
          })
    return failures


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
    failures = []
    if not resource_names:
      return failures
    secrets_client = secrets_api.Secrets()
    for name in resource_names:
      secret_ref = resources.REGISTRY.Parse(
          name,
          params={'projectsId': self.project_id},
          collection='secretmanager.projects.secrets',
      )
      try:
        secrets_client.Delete(secret_ref)

      except api_exceptions.HttpError as e:
        log.warning(
            'Failed to delete Secret Manager secret {}: {}'.format(name, e)
        )
        failures.append({
            'type': 'Secret Manager Secret',
            'name': name,
            'error': str(e),
        })
    return failures


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
    failures = []
    if not resource_names:
      return failures
    gcs_client = storage_api.StorageClient()
    for bucket_name in resource_names:
      bucket_ref = storage_util.BucketReference(bucket_name)
      try:
        # 1. Empty the bucket (delete all objects)
        for obj in gcs_client.ListBucket(bucket_ref):
          object_ref = storage_util.ObjectReference(bucket_name, obj.name)
          try:
            gcs_client.DeleteObject(object_ref)
          except api_exceptions.HttpError as e:
            log.warning(
                "Failed to delete object '{}' in bucket '{}': {}".format(
                    obj.name, bucket_name, e
                )
            )
            failures.append({
                'type': 'Cloud Storage Object',
                'name': f'gs://{bucket_name}/{obj.name}',
                'error': str(e),
            })
        # 2. Delete the bucket itself
        gcs_client.DeleteBucket(bucket_ref)

      except storage_api.BucketNotFoundError:
        pass
      except api_exceptions.HttpError as e:
        log.warning(
            'Failed to delete Cloud Storage bucket {}: {}'.format(
                bucket_name, e
            )
        )
        failures.append({
            'type': 'Cloud Storage Bucket',
            'name': bucket_name,
            'error': str(e),
        })
    return failures


class LocalFingerprintHandler(ResourceHandler):
  """Manages local build fingerprint cache teardown lifecycle."""

  def __init__(self, project_id, region, project_name, sanitized_project_name):
    super(LocalFingerprintHandler, self).__init__(
        project_id, region, sanitized_project_name
    )
    self.project_name = project_name

  def Discover(self):
    fingerprint_file = builder.get_fingerprint_file_path(
        self.project_name, self.project_id, self.region
    )
    if os.path.exists(fingerprint_file):
      return [fingerprint_file]
    return []

  def Delete(self, resource_names):
    failures = []
    if not resource_names:
      return failures
    try:
      builder.delete_source_fingerprints(
          self.project_name, self.project_id, self.region
      )
    except (files.Error, OSError) as e:
      failures.append({
          'type': 'Local Build Fingerprint',
          'name': resource_names[0],
          'error': str(e),
      })
    return failures


class ArtifactRegistryHandler(ResourceHandler):
  """Manages Artifact Registry packages teardown lifecycle."""

  def __init__(self, project_id, region, project_name, sanitized_project_name):
    super(ArtifactRegistryHandler, self).__init__(
        project_id, region, sanitized_project_name
    )
    self.project_name = project_name

  def Discover(self):
    client = apis_util.GetClientInstance('artifactregistry', 'v1')
    messages = apis_util.GetMessagesModule('artifactregistry', 'v1')
    repo = (
        f'projects/{self.project_id}/locations/{self.region}'
        f'/repositories/{AR_REPO_NAME}'
    )
    prefix = f'{self.project_name}_'
    with SuppressApiEnablementPrompt():
      try:
        packages = ar_requests.ListPackages(client, messages, repo)
        return [
            pkg_id
            for pkg in packages
            if (pkg_id := os.path.basename(pkg.name)).startswith(prefix)
        ]
      except api_exceptions.HttpError as e:
        if apis_util.GetApiEnablementInfo(e):
          self.api_disabled = True
        else:
          log.warning(f'Failed to list Artifact Registry packages: {e}')
        return []

  def Delete(self, resource_names):
    failures = []
    if not resource_names:
      return failures
    client = apis_util.GetClientInstance('artifactregistry', 'v1')
    messages = apis_util.GetMessagesModule('artifactregistry', 'v1')
    for name in resource_names:
      full_pkg_name = (
          f'projects/{self.project_id}/locations/{self.region}'
          f'/repositories/{AR_REPO_NAME}/packages/{name}'
      )
      try:
        ar_requests.DeletePackage(client, messages, full_pkg_name)
      except api_exceptions.HttpError as e:
        log.warning(
            'Failed to delete Artifact Registry package {}: {}'.format(name, e)
        )
        failures.append({
            'type': 'Container Image Package',
            'name': name,
            'error': str(e),
        })
    return failures


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
        SERVICES_KEY: CloudRunServiceHandler(
            self.project_id,
            self.region,
            self.sanitized_project_name,
            self.conn_context,
        ),
        SECRETS_KEY: SecretManagerHandler(
            self.project_id, self.region, self.sanitized_project_name
        ),
        BUCKET_KEY: GcsBucketHandler(
            self.project_id,
            self.region,
            self.project_name,
            self.sanitized_project_name,
        ),
        IMAGES_KEY: ArtifactRegistryHandler(
            self.project_id,
            self.region,
            self.project_name,
            self.sanitized_project_name,
        ),
        FINGERPRINTS_KEY: LocalFingerprintHandler(
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
        SERVICES_KEY: self.handlers[SERVICES_KEY].Discover(),
        SECRETS_KEY: self.handlers[SECRETS_KEY].Discover(),
        BUCKET_KEY: None,
        IMAGES_KEY: self.handlers[IMAGES_KEY].Discover(),
        FINGERPRINTS_KEY: self.handlers[FINGERPRINTS_KEY].Discover(),
    }
    buckets = self.handlers[BUCKET_KEY].Discover()
    if buckets:
      discovered[BUCKET_KEY] = buckets[0]

    disabled_apis = {
        SERVICES_KEY: self.handlers[SERVICES_KEY].api_disabled,
        SECRETS_KEY: self.handlers[SECRETS_KEY].api_disabled,
        BUCKET_KEY: self.handlers[BUCKET_KEY].api_disabled,
        IMAGES_KEY: self.handlers[IMAGES_KEY].api_disabled,
        FINGERPRINTS_KEY: False,
    }
    return discovered, disabled_apis

  def Delete(self, discovered_resources, tracker=None):
    """Best-effort deletion of all discovered resources."""
    failures = []

    def _DeleteStage(key, handler_func, target_arg):
      if tracker:
        tracker.StartStage(key)
      else:
        log.status.Print(f'  . Deleting {key}...')

      stage_failures = handler_func(target_arg)
      failures.extend(stage_failures)

      if tracker:
        if stage_failures:
          tracker.FailStage(
              key,
              api_exceptions.HttpError(
                  None, None, f'Failed to delete some {key}'
              ),
          )
        else:
          tracker.CompleteStage(key)

    if discovered_resources.get(BUCKET_KEY):
      _DeleteStage(
          BUCKET_KEY,
          lambda arg: self.handlers[BUCKET_KEY].Delete([arg]),
          discovered_resources[BUCKET_KEY],
      )
    if discovered_resources.get(IMAGES_KEY):
      _DeleteStage(
          IMAGES_KEY,
          self.handlers[IMAGES_KEY].Delete,
          discovered_resources[IMAGES_KEY],
      )
    if discovered_resources.get(SECRETS_KEY):
      _DeleteStage(
          SECRETS_KEY,
          self.handlers[SECRETS_KEY].Delete,
          discovered_resources[SECRETS_KEY],
      )
    if discovered_resources.get(SERVICES_KEY):
      _DeleteStage(
          SERVICES_KEY,
          self.handlers[SERVICES_KEY].Delete,
          discovered_resources[SERVICES_KEY],
      )
    if discovered_resources.get(FINGERPRINTS_KEY):
      _DeleteStage(
          FINGERPRINTS_KEY,
          self.handlers[FINGERPRINTS_KEY].Delete,
          discovered_resources[FINGERPRINTS_KEY],
      )
    return failures

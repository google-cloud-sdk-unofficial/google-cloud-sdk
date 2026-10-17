# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Allows you to write surfaces in terms of logical Cloud Run V2 WorkerPools API operations."""

from __future__ import annotations

import functools
from typing import Any

from googlecloudsdk.api_lib.run import metric_names
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.run.sourcedeploys import deployer
from googlecloudsdk.command_lib.run.sourcedeploys import source_container_context
from googlecloudsdk.command_lib.run.sourcedeploys import sources
from googlecloudsdk.command_lib.run.v2 import config_changes as config_changes_mod
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import metrics
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.generated_clients.gapic_clients.run_v2.types import worker_pool as worker_pool_objects


def _CatchGoogleAPICallError(func):
  """Decorator to catch GoogleAPICallError and raise core_exceptions.Error."""

  @functools.wraps(func)
  def Wrapper(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except Exception as e:
      # Checking module name string directly avoids importing standard GAPIC
      # exceptions at top level that pull heavy grpc dependencies at loaded
      # startup time.
      if 'google.api_core.exceptions' in type(e).__module__:
        core_exceptions.reraise(core_exceptions.Error(str(e)))
      raise

  return Wrapper


def WaitForOperation(response):
  """Waits for the LRO response to complete, converting GAPIC errors."""
  try:
    return response.result()
  except Exception as e:
    # Checking module name string directly avoids importing standard GAPIC
    # exceptions at top level that pull heavy grpc dependencies at loaded
    # startup time.
    if 'google.api_core.exceptions' in type(e).__module__:
      core_exceptions.reraise(core_exceptions.Error(str(e)))
    raise


def _UploadSourcesAndGetSourceLocationChanges(
    source_container_contexts: (
        list[source_container_context.SourceContainerContext] | None
    ) = None,
    worker_pool_ref: Any = None,
    tracker: progress_tracker.StagedProgressTracker | None = None,
    dry_run: bool = False,
    kms_key: str | None = None,
) -> list[config_changes_mod.SourceCodeChange]:
  """Uploads sources if necessary and creates source location changes.

  Args:
    source_container_contexts: Contexts for containers deployed from source.
    worker_pool_ref: The worker pool resource being deployed.
    tracker: Progress tracker for the deployment stages.
    dry_run: Whether this is a dry run deployment.
    kms_key: Customer managed encryption key.

  Returns:
    SourceCodeChange config changes for the uploaded sources.
  """
  if not source_container_contexts:
    return []

  needs_upload = not dry_run and any(
      not sources.IsGcsObject(source_container_ctx.source)
      for source_container_ctx in source_container_contexts
  )
  if tracker and needs_upload:
    tracker.StartStage(stages.UPLOAD_SOURCE)
  try:
    config_changes = []
    for source_container_ctx in source_container_contexts:
      if dry_run:
        bucket = 'placeholder-bucket'
        object_ = 'placeholder-source.tar.gz'
        generation = 0
      elif sources.IsGcsObject(source_container_ctx.source):
        bucket, object_, generation = sources.ParseGcsSource(
            source_container_ctx.source
        )
      elif kms_key:
        raise exceptions.ArgumentError(
            f'Invalid source location: {source_container_ctx.source}.'
            ' Deployments encrypted with a customer-managed encryption key'
            ' (CMEK) expect the source to be passed in a pre-configured Cloud'
            ' Storage bucket. See'
            ' https://cloud.google.com/run/docs/securing/using-cmek#source-deploy'
            ' for more details.'
        )
      else:
        source_obj = sources.Upload(
            source_container_ctx.source,
            worker_pool_ref.locationsId,
            worker_pool_ref,
            source_bucket=source_container_ctx.source_bucket,
            archive_type=sources.ArchiveType.TAR,
            respect_gitignore=False,
        )
        bucket = source_obj.bucket
        object_ = source_obj.name
        generation = int(source_obj.generation) if source_obj.generation else 0
      config_changes.append(
          config_changes_mod.SourceCodeChange(
              container_name=source_container_ctx.name,
              non_ingress_type=True,
              bucket=bucket,
              object_=object_,
              generation=generation,
          )
      )
    if tracker and needs_upload:
      tracker.CompleteStage(stages.UPLOAD_SOURCE)
    return config_changes
  except Exception as e:
    if tracker and needs_upload:
      tracker.FailStage(stages.UPLOAD_SOURCE, e)
    raise


class WorkerPoolsOperations(object):
  """Client used to communicate with the actual Cloud Run V2 WorkerPools API."""

  def __init__(self, client):
    self._client = client

  @_CatchGoogleAPICallError
  def GetWorkerPool(self, worker_pool_ref):
    """Get the WorkerPool.

    Args:
      worker_pool_ref: Resource, WorkerPool to get.

    Returns:
      A WorkerPool object.
    """
    worker_pools = self._client.worker
    get_request = self._client.types.GetWorkerPoolRequest(
        name=worker_pool_ref.RelativeName()
    )
    try:
      with metrics.RecordDuration(metric_names.GET_WORKER_POOL):
        return worker_pools.get_worker_pool(get_request)
    except Exception as e:
      # Checking module/class strings directly avoids importing standard GAPIC
      # exceptions that pull heavy grpc dependencies at loaded startup time.
      if (
          'google.api_core.exceptions' in type(e).__module__
          and type(e).__name__ == 'NotFound'
      ):
        return None
      raise

  @_CatchGoogleAPICallError
  def DeleteWorkerPool(self, worker_pool_ref, dry_run=False):
    """Delete the WorkerPool.

    Args:
      worker_pool_ref: Resource, WorkerPool to delete.
      dry_run: bool, if True only validate the change.

    Returns:
      A LRO for delete operation.
    """
    worker_pools = self._client.worker
    delete_request = self._client.types.DeleteWorkerPoolRequest(
        name=worker_pool_ref.RelativeName(),
        validate_only=dry_run,
    )
    try:
      with metrics.RecordDuration(metric_names.DELETE_WORKER_POOL):
        return worker_pools.delete_worker_pool(delete_request)
    except Exception as e:
      # Checking module/class strings directly avoids importing standard GAPIC
      # exceptions that pull heavy grpc dependencies at loaded startup time.
      if (
          'google.api_core.exceptions' in type(e).__module__
          and type(e).__name__ == 'NotFound'
      ):
        return None
      raise

  @_CatchGoogleAPICallError
  def ListWorkerPools(self, region_ref):
    """List the WorkerPools in a region.

    Args:
      region_ref: Resource, Region to get the list of WorkerPools from.

    Returns:
      A list of WorkerPool objects.
    """
    worker_pools = self._client.worker
    list_request = self._client.types.ListWorkerPoolsRequest(
        parent=region_ref.RelativeName()
    )
    # TODO(b/366501494): Support `next_page_token`
    with metrics.RecordDuration(metric_names.LIST_WORKER_POOLS):
      return worker_pools.list_worker_pools(list_request)

  @_CatchGoogleAPICallError
  def ReleaseWorkerPool(
      self,
      worker_pool_ref,
      config_changes,
      release_track=base.ReleaseTrack.ALPHA,
      tracker=None,
      prefetch=False,
      source_container_contexts: (
          list[source_container_context.SourceContainerContext] | None
      ) = None,
      legacy_build_context: (
          source_container_context.LegacyBuildSourceContainerContext | None
      ) = None,
      skip_activation_prompt=False,
      force_new_revision=False,
      dry_run=False,
      kms_key: str | None = None,
  ):
    """Stubbed method for worker pool deploy surface.

    Update the WorkerPool if it exists, otherwise create it (Upsert).

    Args:
      worker_pool_ref: WorkerPool reference containing project, location,
        workerpool IDs.
      config_changes: list, objects that implement Adjust().
      release_track: ReleaseTrack, the release track of a command calling this.
      tracker: StagedProgressTracker, used to track progress.
      prefetch: the worker pool, pre-fetched for ReleaseWorkerPool. `False`
        indicates the caller did not perform a prefetch; `None` indicates a
        nonexistent worker pool.
      source_container_contexts: Contexts for containers deployed from source
        (e.g. no-build Zip Deploy).
      legacy_build_context: Context for building source using the SubmitBuild
        API and local orchestration.
      skip_activation_prompt: bool. If true, skip activation prompts for
        services
      force_new_revision: bool to force a new revision to be created.
      dry_run: bool to indicate if this is a dry run.
      kms_key: Customer managed encryption key.

    Returns:
      A WorkerPool object.
    """
    has_legacy_build = bool(legacy_build_context)
    has_create_repo = bool(
        legacy_build_context and legacy_build_context.repo_to_create
    )
    has_source_containers = bool(source_container_contexts)
    if has_legacy_build and has_source_containers:
      raise exceptions.ConfigurationError(
          'A Cloud Build source deployment and a no-build source deployment'
          ' cannot be combined in the same worker pool release.'
      )
    if tracker is None:
      tracker = progress_tracker.NoOpStagedProgressTracker(
          stages.WorkerPoolStages(
              include_build=has_legacy_build,
              include_create_repo=has_create_repo,
              include_upload_source=has_legacy_build or has_source_containers,
          ),
          interruptable=True,
          aborted_message='aborted',
      )

    # Deploying from a source (legacy SubmitBuild).
    if has_legacy_build and not dry_run:
      (
          image_digest,
          _,  # build_base_image
          _,  # build_id
          _,  # uploaded_source
          _,  # build_name
      ) = deployer.CreateImage(
          tracker,
          legacy_build_context.build_image,
          legacy_build_context.build_source,
          legacy_build_context.build_pack,
          legacy_build_context.repo_to_create,
          release_track,
          skip_activation_prompt,
          worker_pool_ref.locationsId,  # region
          worker_pool_ref,
          kms_key=kms_key,
      )
      if image_digest is None:
        return
      config_changes.append(
          config_changes_mod.AddDigestToImageChange(
              container_name=legacy_build_context.deploy_from_source_container_name,
              non_ingress_type=True,
              image_digest=image_digest,
          )
      )

    elif has_source_containers:
      # Deploying from source containers (e.g., no-build / Zip Deploy).
      config_changes.extend(
          _UploadSourcesAndGetSourceLocationChanges(
              source_container_contexts,
              worker_pool_ref,
              tracker,
              dry_run=dry_run,
              kms_key=kms_key,
          )
      )

    if prefetch is None:
      worker_pool = None
    elif has_legacy_build:
      # if we're building from source, we want to force a new fetch
      # because building takes a while which leaves a long time for
      # potential write conflicts.
      worker_pool = self.GetWorkerPool(worker_pool_ref)
    else:
      worker_pool = prefetch or self.GetWorkerPool(worker_pool_ref)
    metric_name = metric_names.UPDATE_WORKER_POOL
    if worker_pool is None:
      # WorkerPool does not exist, create it.
      worker_pool = worker_pool_objects.WorkerPool(
          name=worker_pool_ref.RelativeName(),
      )
      metric_name = metric_names.CREATE_WORKER_POOL
    # Apply config changes to the WorkerPool.
    worker_pool = config_changes_mod.WithChanges(worker_pool, config_changes)
    worker_pools = self._client.worker
    upsert_request = self._client.types.UpdateWorkerPoolRequest(
        worker_pool=worker_pool,
        allow_missing=True,
        force_new_revision=force_new_revision,
        validate_only=dry_run,
    )
    with metrics.RecordDuration(metric_name):
      return worker_pools.update_worker_pool(upsert_request)

  @_CatchGoogleAPICallError
  def UpdateInstanceSplit(
      self,
      worker_pool_ref,
      config_changes,
  ):
    """Update the instance split of a WorkerPool."""
    worker_pool = self.GetWorkerPool(worker_pool_ref)
    if worker_pool is None:
      raise core_exceptions.Error(
          'WorkerPool [{}] could not be found.'.format(
              worker_pool_ref.workerPoolsId
          )
      )
    worker_pool = config_changes_mod.WithChanges(worker_pool, config_changes)
    worker_pools = self._client.worker
    update_request = self._client.types.UpdateWorkerPoolRequest(
        worker_pool=worker_pool,
    )
    with metrics.RecordDuration(metric_names.UPDATE_WORKER_POOL):
      return worker_pools.update_worker_pool(update_request)

  @_CatchGoogleAPICallError
  def GetRevision(self, worker_pool_revision_ref):
    """Get the Revision.

    Args:
      worker_pool_revision_ref: Resource, Revision to get.

    Returns:
      A Revision object.
    """
    worker_pool_revisions = self._client.revisions
    get_request = self._client.types.GetRevisionRequest(
        name=worker_pool_revision_ref.RelativeName()
    )
    try:
      with metrics.RecordDuration(metric_names.GET_WORKER_POOL_REVISION):
        return worker_pool_revisions.get_revision(get_request)
    except Exception as e:
      # Checking module/class strings directly avoids importing standard GAPIC
      # exceptions that pull heavy grpc dependencies at loaded startup time.
      if (
          'google.api_core.exceptions' in type(e).__module__
          and type(e).__name__ == 'NotFound'
      ):
        return None
      raise

  @_CatchGoogleAPICallError
  def DeleteRevision(self, worker_pool_revision_ref):
    """Delete the Revision.

    Args:
      worker_pool_revision_ref: Resource, Revision to delete.

    Returns:
      A LRO for delete operation.
    """
    worker_pool_revisions = self._client.revisions
    delete_request = self._client.types.DeleteRevisionRequest(
        name=worker_pool_revision_ref.RelativeName()
    )
    try:
      with metrics.RecordDuration(metric_names.DELETE_WORKER_POOL_REVISION):
        return worker_pool_revisions.delete_revision(delete_request)
    except Exception as e:
      # Checking module/class strings directly avoids importing standard GAPIC
      # exceptions that pull heavy grpc dependencies at loaded startup time.
      if (
          'google.api_core.exceptions' in type(e).__module__
          and type(e).__name__ == 'NotFound'
      ):
        return None
      raise

  @_CatchGoogleAPICallError
  def ListRevisions(self, worker_pool_ref):
    """List the Revisions in a region under the given WorkerPool.

    Args:
      worker_pool_ref: Resource, WorkerPool to get the list of Revisions from.

    Returns:
      A list of Revision objects.
    """
    worker_pool_revisions = self._client.revisions
    list_request = self._client.types.ListRevisionsRequest(
        parent=worker_pool_ref.RelativeName()
    )
    # TODO(b/366501494): Support `next_page_token`
    with metrics.RecordDuration(metric_names.LIST_WORKER_POOL_REVISIONS):
      return worker_pool_revisions.list_revisions(list_request)

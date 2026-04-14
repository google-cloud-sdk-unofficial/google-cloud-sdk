# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Utilities for AI Platform serverless ray jobs commands."""

from googlecloudsdk.core import log

SERVERLESS_RAY_JOB_COLLECTION = (
    'aiplatform.projects.locations.serverlessRayJobs'
)


def _ConstructWorkerPoolSpecs(aiplatform_client, worker_pool_spec):
  """Constructs the specification of a Ray worker nodepool.

  Args:
    aiplatform_client: The AI Platform API client used.
    worker_pool_spec: A dict whose fields represent the worker pool spec.

  Returns:
    A RayWorkerPoolSpec message instance for nodepool resource spec for the
    serverless ray job.
  """

  worker_pool_specs = []
  spec = aiplatform_client.GetMessage('RayWorkerPoolSpec')()
  worker_pool_spec_dict = worker_pool_spec

  spec.machineSpec = aiplatform_client.GetMessage('MachineSpec')()

  if worker_pool_spec_dict.get('disk-size'):
    spec.diskSpec = aiplatform_client.GetMessage('DiskSpec')()
    spec.diskSpec.bootDiskSizeGb = worker_pool_spec_dict.get('disk-size')

  if worker_pool_spec_dict.get('max-node-count'):
    spec.maxReplicaCount = worker_pool_spec_dict.get('max-node-count')

  log.status.Print('worker_pool_spec: {}'.format(spec))

  worker_pool_specs.append(spec)

  return worker_pool_specs


def ConstructServerlessRayJobSpec(
    aiplatform_client,
    entrypoint=None,
    service_account=None,
    container_image_uri=None,
    worker_pool_spec=None,
):
  """Constructs the specification of a serverless ray job.

  Args:
    aiplatform_client: The AI platform API client used.
    entrypoint: The code entrypoint to use for the Ray job.
    service_account: The service account for the serverless ray job.
    container_image_uri: The container image URI for the serverless ray job.
    worker_pool_spec: The worker pool spec of the nodepool for the serverless
      ray job.

  Returns:
    A ServerlessRayJobSpec message instance for creating a serverless ray job.
  """

  job_spec_message = aiplatform_client.GetMessage('ServerlessRayJobSpec')
  job_spec = job_spec_message(entrypoint=entrypoint)

  if service_account is not None:
    job_spec.serviceAccount = service_account

  if worker_pool_spec:
    job_spec.workerPoolSpecs = _ConstructWorkerPoolSpecs(
        aiplatform_client, worker_pool_spec
    )

  if container_image_uri:
    runtime_env = aiplatform_client.GetMessage(
        'ServerlessRayJobSpecRuntimeEnv'
    )()
    runtime_env_container = aiplatform_client.GetMessage(
        'ServerlessRayJobSpecRuntimeEnvContainer'
    )(imageUri=container_image_uri)
    runtime_env.container = runtime_env_container
    job_spec.runtimeEnv = runtime_env

  return job_spec


def _IsKwargsDefined(key, **kwargs):
  return key in kwargs and bool(kwargs.get(key))

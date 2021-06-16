# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to create a custom job in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.custom_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.ai.custom_jobs import custom_jobs_util
from googlecloudsdk.command_lib.ai.custom_jobs import flags
from googlecloudsdk.core import log

_JOB_CREATION_DISPLAY_MESSAGE_TEMPLATE = """\
Custom Job [{id}] submitted successfully.

Your job is still active. You may view the status of your job with the command

  $ {command_prefix} ai custom-jobs describe {id}

Job State: {state}\
"""


def _ValidateArgs(args, job_spec_from_config, version):
  """Validate the argument values specified in command."""
  # TODO(b/186082396): adds more validations for other args.
  if args.worker_pool_spec:
    if version != constants.GA_VERSION:
      args.worker_pool_spec = _NormalizeDeprecatedPythonImageUriInSpec(
          args.worker_pool_spec)
    _ValidateWorkerPoolSpecArgs(args.worker_pool_spec)
  else:
    _ValidateWorkerPoolSpecsFromConfig(job_spec_from_config)


def _ValidateWorkerPoolSpecArgs(worker_pool_specs):
  """Validate the argument values specified via `--worker-pool-spec` flags."""

  for spec in worker_pool_specs:
    if spec:
      _ValidateSingleWorkerPoolSpecArgs(spec)


def _NormalizeDeprecatedPythonImageUriInSpec(specs):
  """Update the values of `--worker-pool-spec` flags if `python-image-uri` is specified."""

  updated = []
  for spec in specs:
    if spec and 'python-image-uri' in spec:
      # TODO(b/185461224): remove `python-image-uri`
      if 'executor-image-uri' not in spec:
        log.warning('Field `python-image-uri` in flag `--worker-pool-spec` will'
                    ' be deprecated. Please use `executor-image-uri` instead.')
        spec['executor-image-uri'] = spec['python-image-uri']
      else:
        log.warning('Field `python-image-uri` in flag `--worker-pool-spec` is'
                    'ignored and replaced by `executor-image-uri`.')
    updated.append(spec)
  return updated


def _ValidateSingleWorkerPoolSpecArgs(spec):
  """Validate a single `--worker-pool-spec` flag value."""

  has_executor_image = 'executor-image-uri' in spec
  has_container_image = 'container-image-uri' in spec
  has_python_module = 'python-module' in spec

  if has_executor_image == has_container_image:
    raise exceptions.InvalidArgumentException(
        '--worker-pool-spec',
        ('Exactly one of keys [executor-image-uri, container-image-uri] '
         'is required.'))

  if has_container_image and has_python_module:
    raise exceptions.InvalidArgumentException(
        '--worker-pool-spec',
        ('Key [python-module] is not allowed together with key '
         '[container-image-uri].'))

  if has_executor_image and not has_python_module:
    raise exceptions.InvalidArgumentException(
        '--worker-pool-spec', 'Key [python-module] is required.')


def _ValidateWorkerPoolSpecsFromConfig(job_spec):
  """Validate WorkerPoolSpec message instances imported from the config file."""
  # TODO(b/186082396): adds more validations for other fields.
  for spec in job_spec.workerPoolSpecs:
    use_python_package = spec.pythonPackageSpec and (
        spec.pythonPackageSpec.executorImageUri or
        spec.pythonPackageSpec.pythonModule)
    use_container = spec.containerSpec and spec.containerSpec.imageUri

    if (use_container and use_python_package) or (not use_container and
                                                  not use_python_package):
      raise exceptions.InvalidArgumentException(
          '--config',
          ('Exactly one of fields [pythonPackageSpec, containerSpec] '
           'is required for a [workerPoolSpecs] in the YAML config file.'))


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  """Create a new custom job.

  This command will attempt to run the custom job immediately upon creation.

  ## EXAMPLES

  To create a job under project ``example'' in region
  ``us-central1'', run:

    $ {command} --region=us-central1 --project=example
    --worker-pool-spec=replica-count=1,machine-type='n1-highmem-2',container-image-uri='gcr.io/ucaip-test/ucaip-training-test'
    --display-name=test
  """

  _version = constants.GA_VERSION

  @classmethod
  def Args(cls, parser):
    flags.AddCreateCustomJobFlags(parser, version=cls._version)

  def _DisplayResult(self, response):
    cmd_prefix = 'gcloud'
    if self.ReleaseTrack().prefix:
      cmd_prefix += ' ' + self.ReleaseTrack().prefix

    log.status.Print(
        _JOB_CREATION_DISPLAY_MESSAGE_TEMPLATE.format(
            id=custom_jobs_util.ParseJobName(response.name),
            command_prefix=cmd_prefix,
            state=response.state))

  def _PrepareJobSpec(self, args, api_client):
    job_config = api_client.ImportResourceMessage(
        args.config, 'CustomJobSpec') if args.config else api_client.GetMessage(
            'CustomJobSpec')()

    _ValidateArgs(args, job_config, self._version)

    job_spec = custom_jobs_util.ConstructCustomJobSpec(
        api_client,
        base_config=job_config,
        worker_pool_specs=args.worker_pool_spec,
        network=args.network,
        service_account=args.service_account,
        python_package_uri=args.python_package_uris,
        args=args.args,
        command=args.command)
    return job_spec

  def Run(self, args):
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    with endpoint_util.AiplatformEndpointOverrides(
        version=self._version, region=region):
      api_client = client.CustomJobsClient(version=self._version)
      job_spec = self._PrepareJobSpec(args, api_client)

      response = api_client.Create(
          parent=region_ref.RelativeName(),
          display_name=args.display_name,
          job_spec=job_spec,
          kms_key_name=validation.GetAndValidateKmsKey(args))
      self._DisplayResult(response)
      return response


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreatePreGA(CreateGA):
  """Create a new custom job.

  This command will attempt to run the custom job immediately upon creation.

  ## EXAMPLES

  To create a job under project ``example'' in region
  ``us-central1'', run:

    $ {command} --region=us-central1 --project=example
    --worker-pool-spec=replica-count=1,machine-type='n1-highmem-2',container-image-uri='gcr.io/ucaip-test/ucaip-training-test'
    --display-name=test
  """
  _version = constants.BETA_VERSION

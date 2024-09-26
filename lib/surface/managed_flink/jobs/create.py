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
"""Create a Flink job from a Java jar."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.managed_flink import util as flink_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.managed_flink import flags
from googlecloudsdk.command_lib.managed_flink import flink_backend
from googlecloudsdk.command_lib.util.args import common_args
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms


def GetJobType(job_type, job_file):
  """Returns the job type based on the job_type and job_file."""
  if job_type == 'auto':
    job_type = None
    if job_file.endswith('.py'):
      job_type = 'python'
    elif job_file.endswith('.sql'):
      job_type = 'sql'
    elif job_file.endswith('.jar'):
      job_type = 'jar'
    if not job_type:
      raise UnknownJobType(
          'Unable to determine type of job [{}]. Job input files must end in'
      )
  return job_type


class UnknownJobType(core_exceptions.Error):
  """Raised when the job type cannot be determined."""


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.BinaryBackedCommand):
  """Create a Flink job from a Java jar."""

  detailed_help = {
      'EXAMPLES': """
      To create a Flink job from a Java jar, run:

      $ {command} my-job.jar --project=my-project --location=us-central1
      """,
  }

  def _JobSubmitResponseHandler(self, response, job_type, temp_dir, args):
    """Process results of BinaryOperation Execution."""
    if response.stdout and (args.show_output or job_type == 'sql'):
      log.Print(response.stdout)

    if response.stderr:
      log.status.Print(response.stderr)

    if response.failed:
      return None

    jobgraph = os.path.join(temp_dir, 'jobgraph.bin')
    if not os.path.exists(jobgraph):
      return None
    jobspec = os.path.join(temp_dir, 'jobspec.yaml')
    if not os.path.exists(jobspec):
      return None
    with files.FileReader(jobspec) as f:
      jobspec_json = yaml.load(f)

    files_to_upload = list()
    files_to_upload.append(os.path.join(temp_dir, 'jobgraph.bin'))
    for jar in jobspec_json['job']['jars']:
      if jar.startswith('file:'):
        files_to_upload.append(jar[5:])

    dest = flink_backend.Upload(
        files_to_upload,
        os.path.join(args.staging_location, jobspec_json['job']['id']),
    )
    msg = flink_util.GetMessagesModule(self.ReleaseTrack())

    jobspec = msg.JobSpec(
        jobName='{0}'.format(jobspec_json['job']['name']),
        jobGraphUri=dest[os.path.join(temp_dir, 'jobgraph.bin')],
        jarUris=[dest[jar[5:]] for jar in jobspec_json['job']['jars']],
    )

    # Configure optional arguments
    if args.name:
      jobspec.displayName = args.name

    if args.network:
      config = msg.NetworkConfig(vpc=args.network)
      if args.subnetwork:
        config.subnetwork = args.subnetwork
      jobspec.networkConfig = config

    # Configure autotuning mode
    autotuning_config = msg.AutotuningConfig()
    if args.autotuning_mode == 'fixed':
      autotuning_config.fixed = msg.Fixed(parallelism=args.parallelism)
    else:
      autotuning_config.throughputBased = msg.Elastic(
          parallelism=args.min_parallelism,
          minParallelism=args.min_parallelism,
          maxParallelism=args.max_parallelism,
      )
    jobspec.autotuningConfig = autotuning_config

    job = msg.Job(name=jobspec_json['job']['id'], jobSpec=jobspec)
    if args.deployment:
      job.deploymentId = args.deployment

    create = msg.ManagedflinkProjectsLocationsJobsCreateRequest(
        parent='projects/{0}/locations/{1}'.format(
            properties.VALUES.core.project.Get(required=True), args.location
        ),
        jobId=jobspec_json['job']['id'],
        job=job,
    )
    if args.show_output:
      log.Print(create)
    if args.dry_run:
      return response
    flink_client = flink_util.FlinkClient(self.ReleaseTrack())
    create_op = flink_client.client.projects_locations_jobs.Create(create)
    if args.show_output:
      log.Print(create_op)
    log.Print('Create request issued for [{0}]'.format(create.jobId))
    if args.async_submit:
      return response

    create_op_ref = resources.REGISTRY.Parse(
        create_op.name, collection='managedflink.projects.locations.operations'
    )
    waiter.WaitFor(
        waiter.CloudOperationPoller(
            flink_client.client.projects_locations_jobs,
            flink_client.client.projects_locations_operations,
        ),
        create_op_ref,
        'Waiting for operations [{0}] to complete...'.format(create_op.name),
    )
    return response

  @staticmethod
  def Args(parser):
    # Common arguments
    common_args.ProjectArgument(
        help_text_to_overwrite='Project to run the job in.'
    ).AddToParser(parser)
    # Specific arguments
    flags.AddDeploymentArgument(
        parser, help_text_to_overwrite='Deployment to run the job in.'
    )
    flags.AddShowOutputArgument(parser)
    flags.AddDryRunArgument(parser)
    flags.AddAsyncArgument(parser)
    flags.AddMainClassArgument(parser)
    flags.AddExtraJarsArgument(parser)
    flags.AddLocationArgument(parser)
    flags.AddStagingLocationArgument(parser)
    flags.AddAutotuningModeArgument(parser)
    flags.AddJobJarArgument(parser)
    flags.AddJobTypeArgument(parser)
    flags.AddNameArgument(parser)
    flags.AddFixedParallelismArgs(parser)
    flags.AddElasticParallelismArgs(parser)
    flags.AddNetworkConfigArgs(parser)
    flags.AddJobArgsCollector(parser)
    flags.AddPythonVirtualEnvArgument(parser)
    flags.AddExtraArchivesArgument(parser)

  def Run(self, args):
    current_os = platforms.OperatingSystem.Current()
    if current_os is platforms.OperatingSystem.WINDOWS:
      raise exceptions.ToolException('Job creation not supported on Windows.')
    # Make sure the job file exists
    if not os.path.exists(args.job):
      raise exceptions.InvalidArgumentException(
          'JAR|PY|SQL',
          'Job definition [{0}] does not exist.'.format(args.job),
      )

    # Determine the job type
    job_type = GetJobType(args.job_type, args.job)

    # Make sure both network arguments are set if at least one is present.
    if args.network:
      if not args.subnetwork:
        raise exceptions.InvalidArgumentException(
            'network-config-subnetwork',
            '--network-config-subnetwork must be set if --network-config-vpc is'
            ' set.',
        )
    elif args.subnetwork:
      if not args.network:
        raise exceptions.InvalidArgumentException(
            'network-config-vpc',
            '--network-config-vpc must be set if --network-config-subnetwork is'
            ' set.',
        )

    # Validate that autotuning arguments are consistent
    flink_backend.ValidateAutotuning(
        args.autotuning_mode,
        args.min_parallelism,
        args.max_parallelism,
        args.parallelism,
    )

    # Validate the staging location
    if not args.staging_location.startswith('gs://'):
      raise exceptions.InvalidArgumentException(
          'staging-location',
          'Staging location must be of the form gs://<bucket>/<path>.',
      )
    flink_backend.CheckStagingLocation(args.staging_location)

    if not args.staging_location.startswith('gs://'):
      raise exceptions.InvalidArgumentException(
          'staging-location',
          'Staging location must be of the form gs://<bucket>/<path>.',
      )

    # Validate the python virtualenv
    if job_type == 'python':
      if not args.python_venv:
        raise exceptions.InvalidArgumentException(
            'python-venv',
            'Python virtualenv must be set if job type is python.',
        )

      if not args.python_venv.startswith('gs://'):
        raise exceptions.InvalidArgumentException(
            'python-venv',
            'Python Virtualenv location must be of the form'
            ' gs://<bucket>/<path>.',
        )

    env = dict()
    env['CLOUDSDK_MANAGEDFLINK_JOB_TYPE'] = job_type

    # Dry run
    if args.dry_run:
      env['CLOUDSDK_MANAGEDFLINK_DRY_RUN'] = 'true'
      env['CLOUDSDK_MANAGEDFLINK_ECHO_CMD'] = 'true'

    with files.TemporaryDirectory() as temp_dir:
      command_executor = flink_backend.FlinkClientWrapper()
      response = command_executor(
          command='run',
          job_type=job_type,
          jar=args.job,
          target='gcloud',
          deployment=args.deployment,
          staging_location=args.staging_location,
          autotuning_mode=args.autotuning_mode,
          temp_dir=temp_dir,
          network=args.network,
          subnetwork=args.subnetwork,
          name=args.name,
          location=args.location,
          main_class=args.main_class,
          extra_jars=args.extra_jars,
          extra_args=args.job_args,
          extra_archives=args.archives,
          python_venv=args.python_venv,
          env=flink_backend.GetEnvArgsForCommand(env),
      )
      return self._JobSubmitResponseHandler(response, job_type, temp_dir, args)

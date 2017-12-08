# Copyright 2016 Google Inc. All Rights Reserved.
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
"""ml jobs submit training command."""
from googlecloudsdk.api_lib.ml import jobs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.logs import stream
from googlecloudsdk.command_lib.ml import flags
from googlecloudsdk.command_lib.ml import jobs as jobs_prep
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_printer


_POLLING_INTERVAL = 10
_FOLLOW_UP_MESSAGE = """\
You may view the status of your job with the command

  $ gcloud beta ml jobs describe {job_id}

or continue streaming the logs with the command

  $ gcloud beta ml jobs stream-logs {job_id}\
"""


class BetaTrain(base.Command):
  r"""Submits a Cloud Machine Learning training job.

  This creates temporary files and executes Python code staged
  by a user on Google Cloud Storage. Model code can either be
  specified with a path, e.g.:

      $ {command} my_job \
              --module-name trainer.task \
              --staging-bucket gs://my-bucket \
              --package-path /my/code/path/trainer \
              --packages additional-dep1.tar.gz,dep2.whl

  Or by specifying an already built package:

      $ {command} my_job \
              --module-name trainer.task \
              --staging-bucket gs://my-bucket \
              --packages trainer-0.0.1.tar.gz,additional-dep1.tar.gz,dep2.whl

  If --package-path /my/code/path/trainer is specified and there is a
  setup.py file at /my/code/path/setup.py then that file will be invoked
  with `sdist` and the generated tar files will be uploaded to Cloud Storage.
  Otherwise a temporary setup.py file will be generated for the build.

  By default, this command blocks until the job finishes, streaming the logs in
  the meantime. If the job succeeds, the command exits zero; otherwise, it exits
  non-zero. To avoid blocking, pass the `--async` flag.

  For more information, see:
  https://cloud.google.com/ml/docs/concepts/training-overview
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.JOB_NAME.AddToParser(parser)
    flags.PACKAGE_PATH.AddToParser(parser)
    flags.PACKAGES.AddToParser(parser)
    flags.MODULE_NAME.AddToParser(parser)
    compute_flags.AddRegionFlag(parser, 'machine learning training job',
                                'submit')
    flags.CONFIG.AddToParser(parser)
    flags.GetStagingBucket(required=True).AddToParser(parser)
    flags.USER_ARGS.AddToParser(parser)
    flags.SCALE_TIER.AddToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Format(self, args):
    return None

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    # TODO(b/33234717): remove this after deprecation period
    flags.ProcessPackages(args)

    region = properties.VALUES.compute.region.Get(required=True)
    uris = jobs_prep.RunSetupAndUpload(
        args.packages, args.staging_bucket, args.package_path, args.job)
    log.debug('Using {0} as trainer uris'.format(uris))
    scale_tier_enum = (jobs.GetMessagesModule().
                       GoogleCloudMlV1beta1TrainingInput.
                       ScaleTierValueValuesEnum)
    scale_tier = scale_tier_enum(args.scale_tier) if args.scale_tier else None
    job = jobs.BuildTrainingJob(
        path=args.config,
        module_name=args.module_name,
        job_name=args.job,
        trainer_uri=uris,
        region=region,
        scale_tier=scale_tier,
        user_args=args.user_args)

    jobs_client = jobs.JobsClient()
    job = jobs_client.Create(job)
    if args.async:
      log.status.Print('Job [{}] submitted successfully.'.format(job.jobId))
      log.status.Print(_FOLLOW_UP_MESSAGE.format(job_id=job.jobId))
      return job

    log_fetcher = stream.LogFetcher(job_id=job.jobId,
                                    polling_interval=_POLLING_INTERVAL,
                                    allow_multiline_logs=False)

    printer = resource_printer.Printer(stream.LogFetcher.LOG_FORMAT,
                                       out=log.err)
    def _CtrlCHandler(signal, frame):
      del signal, frame  # Unused
      raise KeyboardInterrupt
    with execution_utils.CtrlCSection(_CtrlCHandler):
      try:
        printer.Print(log_fetcher.YieldLogs())
      except KeyboardInterrupt:
        log.status.Print('Received keyboard interrupt.')
        log.status.Print(_FOLLOW_UP_MESSAGE.format(job_id=job.jobId))

    job_ref = resources.REGISTRY.Parse(job.jobId, collection='ml.projects.jobs')
    job = jobs_client.Get(job_ref)
    # If the job itself failed, we will return a failure status.
    if job.state is not job.StateValueValuesEnum.SUCCEEDED:
      self.exit_code = 1

    return job

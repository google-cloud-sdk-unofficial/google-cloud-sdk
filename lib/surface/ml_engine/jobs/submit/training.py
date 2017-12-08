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
"""ml-engine jobs submit training command."""
from googlecloudsdk.api_lib.ml import jobs
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.ml import flags
from googlecloudsdk.command_lib.ml import jobs_util


_FORMAT = 'yaml(jobId,state,startTime.date(tz=LOCAL),endTime.date(tz=LOCAL))'


def _AddSubmitTrainingArgs(parser):
  """Add arguments for `jobs submit training` command."""
  flags.JOB_NAME.AddToParser(parser)
  flags.PACKAGE_PATH.AddToParser(parser)
  flags.PACKAGES.AddToParser(parser)
  flags.MODULE_NAME.AddToParser(parser)
  compute_flags.AddRegionFlag(parser, 'machine learning training job',
                              'submit')
  flags.CONFIG.AddToParser(parser)
  flags.STAGING_BUCKET.AddToParser(parser)
  parser.add_argument(
      '--job-dir',
      type=storage_util.ObjectReference.FromUrl,
      help="""\
          A Google Cloud Storage path in which to store training outputs and
          other data needed for training.

          This path will be passed to your TensorFlow program as `--job_dir`
          command-line arg. The benefit of specifying this field is that Cloud
          ML Engine will validate the path for use in training.

          If packages must be uploaded and `--staging-bucket` is not provided,
          this path will be used instead.
      """)
  flags.GetUserArgs(local=False).AddToParser(parser)
  flags.SCALE_TIER.AddToParser(parser)
  flags.RUNTIME_VERSION.AddToParser(parser)
  base.ASYNC_FLAG.AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class TrainBeta(base.Command):
  """Submits a Cloud Machine Learning training job."""

  @staticmethod
  def Args(parser):
    _AddSubmitTrainingArgs(parser)

  def Format(self, args):
    return _FORMAT

  def Run(self, args):
    job = jobs_util.SubmitTraining(
        jobs.JobsClient('v1beta1'), args.job,
        job_dir=args.job_dir,
        staging_bucket=args.staging_bucket,
        packages=args.packages,
        package_path=args.package_path,
        scale_tier=args.scale_tier,
        config=args.config,
        module_name=args.module_name,
        runtime_version=args.runtime_version,
        async_=args.async,
        user_args=args.user_args)
    # If the job itself failed, we will return a failure status.
    if not args.async and job.state is not job.StateValueValuesEnum.SUCCEEDED:
      self.exit_code = 1
    return job


@base.ReleaseTracks(base.ReleaseTrack.GA)
class TrainGa(base.Command):
  """Submits a Cloud Machine Learning training job."""

  @staticmethod
  def Args(parser):
    _AddSubmitTrainingArgs(parser)

  def Format(self, args):
    return _FORMAT

  def Run(self, args):
    job = jobs_util.SubmitTraining(
        jobs.JobsClient('v1'), args.job,
        job_dir=args.job_dir,
        staging_bucket=args.staging_bucket,
        packages=args.packages,
        package_path=args.package_path,
        scale_tier=args.scale_tier,
        config=args.config,
        module_name=args.module_name,
        runtime_version=args.runtime_version,
        async_=args.async,
        user_args=args.user_args)
    # If the job itself failed, we will return a failure status.
    if not args.async and job.state is not job.StateValueValuesEnum.SUCCEEDED:
      self.exit_code = 1
    return job


_DETAILED_HELP = {
    'DESCRIPTION': r"""Submits a Cloud Machine Learning training job.

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
}

TrainBeta.detailed_help = _DETAILED_HELP
TrainGa.detailed_help = _DETAILED_HELP

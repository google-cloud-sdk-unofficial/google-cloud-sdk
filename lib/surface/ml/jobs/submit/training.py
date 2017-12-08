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
from googlecloudsdk.command_lib.ml import flags
from googlecloudsdk.command_lib.ml import jobs as jobs_prep
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaTrain(base.Command):
  r"""Submits a Cloud Machine Learning training job.

  This creates temporary files and executes Python code staged
  by a user on Google Cloud Storage. Model code can either be
  specified with a path, e.g.:

      $ {command} my_job \
              --module-name trainer.task \
              --staging-bucket gs://my-bucket \
              --package-path /my/code/path/trainer \
              --packages additional-dependency1.tar.gz \
                         additional-dependency2.tar.gz

  Or by specifying an already built package:

      $ {command} my_job \
              --module-name trainer.task \
              --staging-bucket gs://my-bucket \
              --packages trainer-0.0.1.tar.gz \
                         additional-dependency1.tar.gz \
                         additional-dependency2.tar.gz

  If --package-path /my/code/path/trainer is specified and there is a
  setup.py file at /my/code/path/setup.py then that file will be invoked
  with [sdist] and the generated tar files will be uploaded to Cloud Storage.
  Otherwise a temporary setup.py file will be generated for the build.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.JOB_NAME.AddToParser(parser)
    flags.PACKAGE_PATH.AddToParser(parser)
    flags.PACKAGES.AddToParser(parser)
    flags.MODULE_NAME.AddToParser(parser)
    compute_flags.AddRegionFlag(
        parser, 'machine learning training job', 'submit')
    flags.CONFIG.AddToParser(parser)
    flags.STAGING_BUCKET.AddToParser(parser)
    flags.USER_ARGS.AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    uris = jobs_prep.RunSetupAndUpload(
        args.packages, args.staging_bucket, args.package_path)
    log.debug('Using {0} as trainer uris'.format(uris))
    job = jobs.BuildTrainingJob(
        path=args.config,
        module_name=args.module_name,
        job_name=args.job,
        trainer_uri=uris,
        region=args.region,
        user_args=args.user_args)
    return jobs.Create(job)

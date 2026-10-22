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
"""Update environment command."""

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc.environments import util as env_util


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Managed Service for Apache Spark environment.

  Every successful update builds a new immutable revision of the environment.
  """

  detailed_help = {
      'EXAMPLES': """\
          To replace the Python packages of environment `my-env` in
          `us-central1`, run:

            $ {command} my-env --location=us-central1 \\
                --python-package="pandas>=2.0,<3" \\
                --python-package=scipy

          To remove all Python packages from the environment, run:

            $ {command} my-env --location=us-central1 --clear-python-packages

          To remove the custom package repository, so that the Python packages
          are downloaded from the public PyPI index, run:

            $ {command} my-env --location=us-central1 \\
                --clear-python-packages-repository
          """,
  }

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack(), api_version='v2')
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddTimeoutFlag(parser, default='35m')
    flags.AddEnvironmentResourceArg(parser, 'update', dataproc.api_version)
    env_util.AddUpdateEnvironmentFlags(parser)

  def Run(self, args):
    environment_ref = args.CONCEPTS.environment.Parse()
    dataproc = dp.Dataproc(
        self.ReleaseTrack(),
        api_version='v2',
        location=environment_ref.locationsId,
    )
    environment, changed_fields = env_util.BuildEnvironmentForUpdate(
        dataproc, args, environment_ref
    )
    return env_util.UpdateEnvironment(
        dataproc, environment_ref, environment, changed_fields, args
    )

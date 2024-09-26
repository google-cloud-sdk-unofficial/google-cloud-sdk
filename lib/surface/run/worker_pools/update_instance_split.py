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
"""Command for updating instances split for worker-pool resource."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AdjustInstanceSplit(base.Command):
  """Adjust the instance assignments for a Cloud Run worker-pool."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To assign 10% of instances to revision my-worker-pool-s5sxn and
          90% of instances to revision my-worker-pool-cp9kw run:

              $ {command} my-worker-pool --to-revisions=my-worker-pool-s5sxn=10,my-worker-pool-cp9kw=90

          To increase the instances to revision my-worker-pool-s5sxn to 20% and
          by reducing the instances to revision my-worker-pool-cp9kw to 80% run:

              $ {command} my-worker-pool --to-revisions=my-worker-pool-s5sxn=20

          To rollback to revision my-worker-pool-cp9kw run:

              $ {command} my-worker-pool --to-revisions=my-worker-pool-cp9kw=100

          To assign 100% of instances to the current or future LATEST revision
          run:

              $ {command} my-worker-pool --to-latest

          You can also refer to the current or future LATEST revision in
          --to-revisions by the string "LATEST". For example, to set 10% of
          instances to always float to the latest revision:

              $ {command} my-worker-pool --to-revisions=LATEST=10

         """,
  }

  @classmethod
  def CommonArgs(cls, parser):
    worker_pool_presentation = presentation_specs.ResourcePresentationSpec(
        'WORKER_POOL',
        resource_args.GetWorkerPoolResourceSpec(prompt=True),
        'WorkerPool to update instance split of.',
        required=True,
        prefixes=False,
    )
    concept_parsers.ConceptParser([worker_pool_presentation]).AddToParser(
        parser
    )
    flags.AddAsyncFlag(parser)
    flags.AddUpdateInstanceSplitFlags(parser)
    flags.AddBinAuthzBreakglassFlag(parser)

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

  def Run(self, args):
    """Update the instance split for the worker."""
    raise NotImplementedError

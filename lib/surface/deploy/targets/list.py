# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Exports a Gcloud Deploy delivery pipeline resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import flags
from googlecloudsdk.command_lib.deploy import resource_args
from googlecloudsdk.command_lib.deploy import target_util
from googlecloudsdk.core import resources

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        textwrap.dedent("""\

      To list the targets in region 'us-central1', run:

        $ {command} --region=us-central1

      """)
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Cloud Deploy targets."""
  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser)
    flags.AddDeliveryPipeline(parser, False)

  def Run(self, args):
    """Entry point of the export command.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
       A list of target messages.
    """
    loc_ref = args.CONCEPTS.region.Parse()
    name = loc_ref.RelativeName()
    if args.delivery_pipeline:
      loc_dict = loc_ref.AsDict()
      name = resources.REGISTRY.Parse(
          None,
          collection='clouddeploy.projects.locations.deliveryPipelines',
          params={
              'projectsId': loc_dict['projectsId'],
              'locationsId': loc_dict['locationsId'],
              'deliveryPipelinesId': args.delivery_pipeline,
          }).RelativeName()

    return target_util.ListTarget(name)

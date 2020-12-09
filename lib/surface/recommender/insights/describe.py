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
"""recommender API insights Describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.recommender import flag_utils as api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.recommender import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.Command):
  r"""Describe an insight.

     Describe an insight. This currently supports the following parent entities:
     project, billing account, folder, and organization.

     ## EXAMPLES
     To describe a insight:

      $ {command} INSIGHT_ID --project=${PROJECT} --location=${LOCATION}
      --recommender=${RECOMMENDER}
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
    """
    flags.AddParentFlagsToParser(parser)
    parser.add_argument(
        'INSIGHT',
        type=str,
        help='insight to describe',
    )
    parser.add_argument('--location', metavar='LOCATION', help='Location')
    parser.add_argument(
        '--insight-type',
        metavar='INSIGHT_TYPE',
        required=True,
        help='Insight type to describe insights')

  def Run(self, args):
    """Run 'gcloud recommender insights describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The result insights to describe
    """
    recommender_service = api_utils.GetServiceFromArgs(
        args, is_insight_api=True)
    parent_ref = flags.GetParentFromFlags(
        args, is_list_api=False, is_insight_api=True)
    request = api_utils.GetDescribeRequestFromArgs(
        args, parent_ref, is_insight_api=True)
    return recommender_service.Get(request)

# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""`gcloud dataplex set-iam-policy` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import zone
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.iam import iam_util


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetIamPolicy(base.Command):
  """Sets IAM policy to a zone."""

  detailed_help = {
      'EXAMPLES':
          """\
          To Set an IAM policy binding to a zone, run:

            $ {command} set-iam-policy projects/{project_id}/locations/{location}/lakes/{lake_id}/zones/{zone_id} policy.json

            policy.json is the relative path to the json file.
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddZoneResourceArg(parser, 'to set IAM policy to.')
    iam_util.AddArgForPolicyFile(parser)

  def Run(self, args):
    zone_ref = args.CONCEPTS.zone.Parse()
    result = zone.SetIamPolicyFromFile(zone_ref, args.policy_file)
    return result

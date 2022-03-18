# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""gcloud dns managed-zone set-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.command_lib.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetIamPolicyAlpha(base.Command):
  """Set the IAM policy for a Cloud DNS managed-zone.

  This command sets the IAM Policy of the specified managed-zone.

  ## EXAMPLES

  To set the IAM policy of your managed-zone , run:

    $ {command} my-zone --policy-file=policy.json
  """

  @staticmethod
  def Args(parser):
    flags.GetZoneResourceArg(
        'The name of the managed-zone to set IAM policy.').AddToParser(parser)
    parser.add_argument(
        '--policy-file',
        required=True,
        help='JSON or YAML file with the IAM policy')

  def Run(self, args):
    api_version = util.GetApiFromTrack(self.ReleaseTrack())
    dns_client = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)
    zone_ref = args.CONCEPTS.zone.Parse()
    resource_name = 'projects/{0}/managedZones/{1}'.format(
        zone_ref.project, zone_ref.managedZone)
    policy, update_mask = iam_util.ParsePolicyFileWithUpdateMask(
        args.policy_file, messages.GoogleIamV1Policy)

    req = messages.DnsProjectsManagedZonesSetIamPolicyRequest(
        resource=resource_name,
        googleIamV1SetIamPolicyRequest=messages.GoogleIamV1SetIamPolicyRequest(
            policy=policy, updateMask=update_mask))

    return dns_client.projects_managedZones.SetIamPolicy(req)

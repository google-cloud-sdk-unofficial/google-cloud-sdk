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

"""gcloud dns managed-zone get-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.command_lib.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetIamPolicyAlpha(base.Command):
  """Get the IAM policy for a Cloud DNS managed-zone.

  This command displays the IAM Policy of the specified managed-zone.

  ## EXAMPLES

  To display the details of your managed-zone IAM Policy , run:

    $ {command} my-zone
  """

  @staticmethod
  def Args(parser):
    flags.GetZoneResourceArg(
        'The name of the managed-zone to get IAM policy.').AddToParser(parser)

  def Run(self, args):
    api_version = util.GetApiFromTrack(self.ReleaseTrack())
    dns_client = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)
    zone_ref = args.CONCEPTS.zone.Parse()
    resource_name = 'projects/{0}/managedZones/{1}'.format(
        zone_ref.project, zone_ref.managedZone)

    req = messages.DnsProjectsManagedZonesGetIamPolicyRequest(
        resource=resource_name,
        googleIamV1GetIamPolicyRequest=messages.GoogleIamV1GetIamPolicyRequest(
            options=messages.GoogleIamV1GetPolicyOptions(
                requestedPolicyVersion=iam_util
                .MAX_LIBRARY_IAM_SUPPORTED_VERSION)))

    return dns_client.projects_managedZones.GetIamPolicy(req)



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
"""Command to get a policy on the given resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base


def GetClientInstance(no_http=False):
  return apis.GetClientInstance('iam', 'v2alpha1', no_http=no_http)


def GetMessagesModule(client=None):
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Get(base.DescribeCommand):
  """Get a policy on the given attachment point with the given name."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          The following command gets the IAM policy defined at the resource
          project "123" of kind "denypolicies" and id "my-deny-policy:

            $ {command} my-deny-policy --resource=cloudresourcemanager.googleapis.com/projects/123 --kind=denypolicies
          """),
  }

  @staticmethod
  def Args(parser):
    # TODO(b/150467260): Allow passing in decoded format as well.
    parser.add_argument(
        '--attachment-point',
        required=True,
        help='The resource to which the policy is attached.')

    parser.add_argument('--kind', required=True, help='The kind of the policy.')

    parser.add_argument('policy_id', help='The id of the policy.')

  def Run(self, args):
    client = GetClientInstance()
    messages = GetMessagesModule()

    result = client.policies.Get(
        messages.IamPoliciesGetRequest(name='policies/{}/{}/{}'.format(
            args.attachment_point, args.kind, args.policy_id)))
    return result

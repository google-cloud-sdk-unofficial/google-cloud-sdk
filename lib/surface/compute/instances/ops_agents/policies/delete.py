# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Implements command to delete a specified guest policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute.instances.ops_agents.policies import exceptions as policies_exceptions
from googlecloudsdk.api_lib.compute.instances.ops_agents.validators import guest_policy_validator
from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances.ops_agents.policies import parser_utils
from googlecloudsdk.command_lib.compute.os_config import utils as osconfig_command_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete a policy that manages Google Cloud Operations Suite agents across Google Cloud Compute instances."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To delete an Ops agents policy named ``policy1'' in the current project, run:

            $ {command} policy1
          """,
  }

  @staticmethod
  def Args(parser):
    """See base class."""
    parser_utils.AddSharedArgs(parser)

  def Run(self, args):
    """See base class."""
    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(
        release_track, api_version_override='v1beta')
    messages = osconfig_api_utils.GetClientMessages(
        release_track, api_version_override='v1beta')
    project = properties.VALUES.core.project.GetOrFail()
    guest_policy_uri_path = osconfig_command_utils.GetGuestPolicyUriPath(
        'projects', project, args.POLICY_ID)
    service = client.projects_guestPolicies

    get_request = messages.OsconfigProjectsGuestPoliciesGetRequest(
        name=guest_policy_uri_path)
    try:
      get_response = service.Get(get_request)
    except apitools_exceptions.HttpNotFoundError:
      raise policies_exceptions.NotFoundError(
          policy_id=args.POLICY_ID)
    if not guest_policy_validator.IsOpsAgentPolicy(get_response):
      raise policies_exceptions.NotFoundError(
          policy_id=args.POLICY_ID)

    delete_request = messages.OsconfigProjectsGuestPoliciesDeleteRequest(
        name=guest_policy_uri_path)
    delete_response = service.Delete(delete_request)

    log.DeletedResource(args.POLICY_ID)
    return delete_response

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
"""Update command to update a new Custom Mirroring profile."""

from googlecloudsdk.api_lib.network_security.security_profiles import mirroring_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import sp_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import repeated
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """

          Update a Custom Mirroring Security Profile.

          The supported fields for update are `description` and `labels`.

        """,
    'EXAMPLES': """
          To update the description of a Custom Mirroring Security Profile named `mirroring-profile`, run:

              $ {command} mirroring-profile --description="A new description" \
              --organization=1234567890 --location=global

          To change the labels of a Custom Mirroring Security Profile named `mirroring-profile`, run:

              $ {command} mirroring-profile
              --update-labels=key1=value1,key2=value2  \
              --delete-labels=key3,key4 \
              --organization=1234567890 --location=glob
        """,
}

_BROKER_RELEASE_TRACKS = (base.ReleaseTrack.ALPHA,)
_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Update(base.UpdateCommand):
  """Updates a Custom Mirroring Profile."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    project_scope_supported = (
        cls.ReleaseTrack() in _PROJECT_SCOPE_SUPPORTED_TRACKS
    )
    sp_flags.AddSecurityProfileResource(
        parser, cls.ReleaseTrack(), project_scope_supported
    )
    sp_flags.AddProfileDescription(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, False)
    labels_util.AddUpdateLabelsFlags(parser)

    if cls.ReleaseTrack() in _BROKER_RELEASE_TRACKS:
      repeated.AddPrimitiveArgs(
          parser,
          'security_profile',
          'mirroring-deployment-groups',
          'mirroring deployment groups',
          include_set=False,
      )

  def Run(self, args):
    result = args.CONCEPTS.security_profile.Parse()
    security_profile = result.result

    project_scoped = (
        result.concept_type.name
        == sp_flags.PROJECT_SECURITY_PROFILE_RESOURCE_COLLECTION
    )
    client = mirroring_api.Client(self.ReleaseTrack(), project_scoped)

    description = args.description
    is_async = args.async_

    sp_instance = client.GetSecurityProfile(security_profile.RelativeName())
    labels_update = labels_util.ProcessUpdateArgsLazy(
        args,
        client.messages.SecurityProfile.LabelsValue,
        orig_labels_thunk=lambda: sp_instance.labels,
    )

    if self.ReleaseTrack() in _BROKER_RELEASE_TRACKS:
      updated_dgs = repeated.ParsePrimitiveArgs(
          args,
          'mirroring-deployment-groups',
          lambda: sp_instance.customMirroringProfile.mirroringDeploymentGroups,
      )
    else:
      updated_dgs = None

    response = client.UpdateCustomMirroringProfile(
        name=security_profile.RelativeName(),
        description=description,
        labels=labels_update.GetOrNone(),
        deployment_groups=updated_dgs,
    )

    # Return the in-progress operation if async is requested.
    if is_async:
      operation_id = response.name
      log.status.Print(
          'Check for operation completion status using operation ID:',
          operation_id,
      )
      return response

    # Default operation poller if async is not specified.
    return client.WaitForOperation(
        operation_ref=client.GetOperationsRef(response),
        message='Waiting for security-profile [{}] to be updated'.format(
            security_profile.RelativeName()
        ),
        has_result=True,
    )

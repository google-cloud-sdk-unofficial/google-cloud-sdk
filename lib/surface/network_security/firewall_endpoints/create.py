# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Create endpoint command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
from googlecloudsdk.api_lib.network_security.firewall_endpoints import activation_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.network_security import activation_flags
from googlecloudsdk.command_lib.util.args import labels_util

DETAILED_HELP = {
    'DESCRIPTION': """
          Create a firewall endpoint. Successful creation of an endpoint results
          in an endpoint in READY state. Check the progress of endpoint creation
          by using `gcloud network-security firewall-endpoints list`.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To create a firewall endpoint called `my-endpoint`, in zone
            `us-central1-a` and organization ID 1234, run:

            $ {command} my-endpoint --zone=us-central1-a --organization=1234

        """,
}

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
@base.DefaultUniverseOnly
class Create(base.CreateCommand):
  """Create a Firewall Plus endpoint."""

  @classmethod
  def Args(cls, parser):
    project_scope_supported = (
        cls.ReleaseTrack() in _PROJECT_SCOPE_SUPPORTED_TRACKS
    )
    activation_flags.AddEndpointResource(
        cls.ReleaseTrack(),
        parser,
        project_scope_supported,
    )
    activation_flags.AddMaxWait(parser, '60m')  # default to 60 minutes wait.
    activation_flags.AddDescriptionArg(parser)
    activation_flags.AddEnableJumboFramesArg(parser)
    activation_flags.AddBillingProjectArg(parser, required=False)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    return self._Run(args)

  def _Run(self, args, target_firewall_attachment=None, endpoint_type=None):
    result = args.CONCEPTS.firewall_endpoint.Parse()
    endpoint = result.result

    project_scoped = (
        result.concept_type.name
        == activation_flags.PROJECT_ENDPOINT_RESOURCE_COLLECTION
    )

    if not project_scoped and not args.billing_project:
      raise exceptions.RequiredArgumentException(
          'billing-project',
          '--billing-project flag must be specified for org-scoped firewall'
          ' endpoints.',
      )

    client = activation_api.Client(self.ReleaseTrack(), project_scoped)

    labels = labels_util.ParseCreateArgs(
        args, client.messages.FirewallEndpoint.LabelsValue
    )

    is_async = args.async_
    max_wait = datetime.timedelta(seconds=args.max_wait)

    operation = client.CreateEndpoint(
        name=endpoint.Name(),
        parent=endpoint.Parent().RelativeName(),
        description=getattr(args, 'description', None),
        billing_project_id=args.billing_project,
        labels=labels,
        target_firewall_attachment=target_firewall_attachment,
        enable_jumbo_frames=getattr(args, 'enable_jumbo_frames', None),
        endpoint_type=endpoint_type,
        enable_wildfire=getattr(args, 'enable_wildfire', None),
        wildfire_region=getattr(args, 'wildfire_region', None),
        content_cloud_region=getattr(args, 'content_cloud_region', None),
        wildfire_lookup_timeout=getattr(args, 'wildfire_lookup_timeout', None),
        wildfire_lookup_action=getattr(args, 'wildfire_lookup_action', None),
        wildfire_analysis_timeout=getattr(
            args, 'wildfire_analysis_timeout', None
        ),
        wildfire_analysis_action=getattr(
            args, 'wildfire_analysis_action', None
        ),
        enable_wildfire_analysis_logging=getattr(
            args, 'enable_wildfire_analysis_logging', None
        ),
        block_partial_http=getattr(args, 'block_partial_http', None),
    )
    # Return the in-progress operation if async is requested.
    if is_async:
      # Delete operations have no format by default,
      # but here we want the operation metadata to be printed.
      if not args.IsSpecified('format'):
        args.format = 'default'
      return operation
    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for firewall endpoint [{}] to be created'.format(
            endpoint.RelativeName()
        ),
        has_result=True,
        max_wait=max_wait,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class CreateAlpha(Create):
  """Create a Firewall Plus endpoint."""

  @classmethod
  def Args(cls, parser):
    super(CreateAlpha, cls).Args(parser)
    activation_flags.AddTargetFirewallAttachmentArg(parser)
    activation_flags.AddEnableWildfireArg(parser)
    activation_flags.AddWildfireRegionArg(parser)
    activation_flags.AddContentCloudRegionArg(parser)
    activation_flags.AddWildfireLookupTimeoutArg(parser)
    activation_flags.AddWildfireLookupActionArg(parser)
    activation_flags.AddWildfireAnalysisTimeoutArg(parser)
    activation_flags.AddWildfireAnalysisActionArg(parser)
    activation_flags.AddEnableWildfireAnalysisLoggingArg(parser)
    activation_flags.AddBlockPartialHttpArg(parser)

  def Run(self, args):
    target_firewall_attachment = getattr(
        args, 'target_firewall_attachment', None
    )

    if target_firewall_attachment is not None:
      return self._Run(
          args, target_firewall_attachment, endpoint_type='THIRD_PARTY'
      )
    else:
      return self._Run(
          args, target_firewall_attachment, endpoint_type='TYPE_UNSPECIFIED'
      )


Create.detailed_help = DETAILED_HELP

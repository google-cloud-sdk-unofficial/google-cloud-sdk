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
"""Update endpoint command."""

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
          Update a firewall endpoint. Check the progress of endpoint update
          by using `gcloud network-security firewall-endpoints describe`.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To update labels k1 and k2, run:

            $ {command} my-endpoint --zone=us-central1-a --organization=1234 --update-labels=k1=v1,k2=v2

            To remove labels k3 and k4, run:

            $ {command} my-endpoint --zone=us-central1-a --organization=1234 --remove-labels=k3,k4

            To clear all labels from the firewall endpoint, run:

            $ {command} my-endpoint --zone=us-central1-a --organization=1234 --clear-labels
        """,
}

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
@base.DefaultUniverseOnly
class Update(base.UpdateCommand):
  """Update a Firewall Plus endpoint.

  This command is used to update labels on the endpoint.
  """

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
    activation_flags.AddUpdateBillingProjectArg(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    result = args.CONCEPTS.firewall_endpoint.Parse()
    endpoint = result.result

    project_scoped = (
        result.concept_type.name
        == activation_flags.PROJECT_ENDPOINT_RESOURCE_COLLECTION
    )

    client = activation_api.Client(self.ReleaseTrack(), project_scoped)

    original = client.DescribeEndpoint(endpoint.RelativeName())
    if original is None:
      raise exceptions.InvalidArgumentException(
          'firewall-endpoint',
          'Firewall endpoint does not exist.')

    update_mask = []

    labels = None
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      update_mask.append('labels')
      labels = original.labels
      labels_update = labels_diff.Apply(
          client.messages.FirewallEndpoint.LabelsValue,
          original.labels,
      )
      if labels_update.needs_update:
        labels = labels_update.labels

    billing_project_id = args.update_billing_project
    if billing_project_id:
      update_mask.append('billing_project_id')

    if hasattr(args, 'enable_wildfire') and args.IsSpecified('enable_wildfire'):
      update_mask.append('wildfire_settings.enabled')
    if hasattr(args, 'wildfire_region') and args.IsSpecified('wildfire_region'):
      update_mask.append('wildfire_settings.wildfire_region')
    if hasattr(args, 'content_cloud_region') and args.IsSpecified(
        'content_cloud_region'
    ):
      update_mask.append('endpoint_settings.content_cloud_region')
    if hasattr(args, 'wildfire_lookup_timeout') and args.IsSpecified(
        'wildfire_lookup_timeout'
    ):
      update_mask.append('wildfire_settings.wildfire_realtime_lookup_duration')
    if hasattr(args, 'wildfire_lookup_action') and args.IsSpecified(
        'wildfire_lookup_action'
    ):
      update_mask.append(
          'wildfire_settings.wildfire_realtime_lookup_timeout_action'
      )
    if hasattr(args, 'wildfire_analysis_timeout') and args.IsSpecified(
        'wildfire_analysis_timeout'
    ):
      update_mask.append(
          'wildfire_settings.wildfire_inline_cloud_analysis_settings.max_analysis_duration'
      )
    if hasattr(args, 'wildfire_analysis_action') and args.IsSpecified(
        'wildfire_analysis_action'
    ):
      update_mask.append(
          'wildfire_settings.wildfire_inline_cloud_analysis_settings.timeout_action'
      )
    if hasattr(
        args, 'enable_wildfire_analysis_logging'
    ) and args.IsSpecified('enable_wildfire_analysis_logging'):
      update_mask.append(
          'wildfire_settings.wildfire_inline_cloud_analysis_settings.submission_timeout_logging_disabled'
      )
    if hasattr(args, 'block_partial_http') and args.IsSpecified(
        'block_partial_http'
    ):
      update_mask.append('endpoint_settings.http_partial_response_blocked')

    if not update_mask:
      if self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
        raise exceptions.MinimumArgumentException([
            '--clear-labels',
            '--remove-labels',
            '--update-labels',
            '--update-billing-project',
            '--enable-wildfire',
            '--wildfire-region',
            '--content-cloud-region',
            '--wildfire-lookup-timeout',
            '--wildfire-lookup-action',
            '--wildfire-analysis-timeout',
            '--wildfire-analysis-action',
            '--enable-wildfire-analysis-logging',
            '--block-partial-http',
        ])
      else:
        raise exceptions.MinimumArgumentException([
            '--clear-labels',
            '--remove-labels',
            '--update-labels',
            '--update-billing-project',
        ])

    is_async = args.async_
    max_wait = datetime.timedelta(seconds=args.max_wait)

    operation = client.UpdateEndpoint(
        name=endpoint.RelativeName(),
        description=getattr(args, 'description', None),
        update_mask=','.join(update_mask),
        labels=labels,
        billing_project_id=billing_project_id,
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
        message='waiting for firewall endpoint [{}] to be updated'.format(
            endpoint.RelativeName()
        ),
        has_result=True,
        max_wait=max_wait,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class UpdateAlpha(Update):
  """Update a Firewall Plus endpoint."""

  @classmethod
  def Args(cls, parser):
    super(UpdateAlpha, cls).Args(parser)
    activation_flags.AddEnableWildfireArg(parser)
    activation_flags.AddWildfireRegionArg(parser)
    activation_flags.AddContentCloudRegionArg(parser)
    activation_flags.AddWildfireLookupTimeoutArg(parser)
    activation_flags.AddWildfireLookupActionArg(parser)
    activation_flags.AddWildfireAnalysisTimeoutArg(parser)
    activation_flags.AddWildfireAnalysisActionArg(parser)
    activation_flags.AddEnableWildfireAnalysisLoggingArg(parser)
    activation_flags.AddBlockPartialHttpArg(parser)


Update.detailed_help = DETAILED_HELP

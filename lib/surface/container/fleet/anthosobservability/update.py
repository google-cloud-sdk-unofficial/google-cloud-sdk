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
"""The command to update a Anthos Observability cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import exceptions


@calliope_base.Hidden
class Update(base.UpdateCommand):
  """Update Anthos Observability spec on the specified membership.

  ## EXAMPLES

  To update the observability configuration on a membership named
  `MEMBERSHIP_NAME`, run:

    $ {command} --membership=MEMBERSHIP_NAME
    --enable-stackdriver-on-applications=true
  """

  feature_name = 'anthosobservability'

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    resources.AddMembershipResourceArg(
        parser,
        membership_required=True,
        membership_help='The name of the Membership to update.',
    )
    app_group = parser.add_mutually_exclusive_group(required=False)

    app_group.add_argument(
        '--enable-stackdriver-on-applications',
        action='store_true',
        help='Enable the collection of logs and metrics from user applications',
        required=False,
    )
    app_group.add_argument(
        '--disable-stackdriver-on-applications',
        action='store_true',
        help='Disable the collection of logs and metrics from user applications',
        required=False,
    )
    metrics_group = parser.add_mutually_exclusive_group(required=False)
    metrics_group.add_argument(
        '--enable-optimized-metrics',
        action='store_true',
        help='Collect and report an optimized subset of container and kubelet metrics (recommended)',
        required=False,
    )
    metrics_group.add_argument(
        '--disable-optimized-metrics',
        action='store_true',
        help="""Collect and report a full set (instead of an optimized subset)
        of container and kubelet metrics, not recommended""",
        required=False,
    )

  def Run(self, args):
    """Runs the command.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
    """
    specified_args = args.GetSpecifiedArgsDict()

    if 'membership' not in specified_args:
      raise exceptions.Error('Please specify the membership to be changed')

    if len(specified_args) <= 1:
      raise exceptions.Error(
          """Please specify at least one config to be changed:
          --enable-stackdriver-on-applications
          --disable-stackdriver-on-applications
          --enable-optimized-metrics
          --disable-optimized-metrics""")

    membership = base.ParseMembership(args, search=True)
    resource_name = membership
    old_feature = self.GetFeature(v1alpha1=True)

    ao_feature_spec = old_feature.anthosobservabilityFeatureSpec
    membership_spec = self.v1alpha1_messages.AnthosObservabilityMembershipSpec()

    if ao_feature_spec is not None:
      membership_map = self.hubclient.ToPyDict(ao_feature_spec.membershipSpecs)
      membership_spec = membership_map.get(resource_name,
                                           membership_spec) or membership_spec

    if 'enable_optimized_metrics' in specified_args:
      membership_spec.doNotOptimizeMetrics = False
    elif 'disable_optimized_metrics' in specified_args:
      membership_spec.doNotOptimizeMetrics = True
    if 'enable_stackdriver_on_applications' in specified_args:
      membership_spec.enableStackdriverOnApplications = True
    if 'disable_stackdriver_on_applications' in specified_args:
      membership_spec.enableStackdriverOnApplications = False

    spec_map = {resource_name: membership_spec}

    value = client.HubClient.ToProtoMap(
        self.v1alpha1_messages.AnthosObservabilityFeatureSpec
        .MembershipSpecsValue, spec_map)

    f = self.v1alpha1_messages.Feature(
        anthosobservabilityFeatureSpec=self.v1alpha1_messages
        .AnthosObservabilityFeatureSpec(membershipSpecs=value))

    self.Update(['anthosobservability_feature_spec.membership_specs'],
                f,
                v1alpha1=True)

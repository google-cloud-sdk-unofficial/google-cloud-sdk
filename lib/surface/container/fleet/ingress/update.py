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
"""The command to update Multi-cluster Ingress Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Update(base.UpdateCommand):
  """Update Multi-cluster Ingress Feature.

  This command updates Multi-cluster Ingress Feature in a fleet.

  ## EXAMPLES

  To update the Ingress Feature, run:

    $ {command} --config-membership=CONFIG_MEMBERSHIP
  """

  feature_name = 'multiclusteringress'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--config-membership',
        type=str,
        help=textwrap.dedent("""\
            Membership resource representing the cluster which hosts
            the MultiClusterIngress and MultiClusterService CustomResourceDefinitions.
            """),
    )

  def Run(self, args):
    log.warning('Are you sure you want to update your config membership? Any '
                'differences in your MCI and MCS resources between the old and '
                'new config membership can trigger load balancer updates which '
                'could cause traffic interruption.')

    console_io.PromptContinue(default=True, cancel_on_no=True)

    config_membership = args.config_membership
    if not config_membership:
      memberships = base.ListMemberships()
      if not memberships:
        raise exceptions.Error('No Memberships available in the fleet.')
      index = console_io.PromptChoice(
          options=memberships,
          message='Please specify a config membership:\n')
      config_membership = memberships[index]
    else:
      # Strip to the final path component to allow short and long names.
      # Assumes long names are for the same project and global location.
      # TODO(b/192580393): Use the resource args instead of this hack.
      config_membership = os.path.basename(args.config_membership)

    config_membership = self.MembershipResourceName(config_membership)
    f = self.messages.Feature(
        spec=self.messages.CommonFeatureSpec(
            multiclusteringress=self.messages.MultiClusterIngressFeatureSpec(
                configMembership=config_membership)))

    self.Update(['spec.multiclusteringress.config_membership'], f)

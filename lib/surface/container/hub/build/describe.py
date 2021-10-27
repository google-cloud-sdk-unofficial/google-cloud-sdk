# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""The command to describe the configuration and status of Cloud Build clusters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.command_lib.container.hub.build import utils
from googlecloudsdk.command_lib.container.hub.features import base

# Pull out the example text so the example command can be one line without the
# py linter complaining. The docgen tool properly breaks it into multiple lines.
EXAMPLES = """\
    To describe the configuration and status of members with Cloud Build installed, run:

      $ {command}

    Example output:

      NAME              STATUS  DESCRIPTION                     SECURITY POLICY  VERSION
      managed-member-a  SUCCESS Created controller for cluster  NON_PRIVILEGED   0.1.0
      managed-member-b  SUCCESS Created controller for cluster  PRIVILEGED       0.1.0
      managed-member-c  FAILED  Unable to connect to cluster    PRIVILEGED       0.1.0

    To view the status for a membership named `managed-member-a`, run:

      $ {command} --filter="NAME:managed-member-a"

    To use a regular expression to list the configuration and status of multiple
    memberships, run:

      $ {command} --filter="NAME ~ managed-member.*"

    To list all members with security policy `PRIVILEGED`, run:

      $ {command} --filter="SECURITYPOLICY:PRIVILEGED"

    To list all the members with security policy `NON_PRIVILEGED` and Cloud
    Build version `0.1.0`, run:

      $ {command} --filter="SECURITYPOLICY:NON_PRIVILEGED AND VERSION:0.1.0"
"""


@gbase.Hidden
class Describe(base.DescribeCommand, gbase.ListCommand):
  """Describe the configuration and status of members with Cloud Build installed."""
  detailed_help = {'EXAMPLES': EXAMPLES}

  feature_name = 'cloudbuild'

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
    table(
            NAME:label=NAME:sort=1,
            STATUS:label=STATUS,
            DESCRIPTION:label=DESCRIPTION,
            SECURITYPOLICY:label="SECURITY POLICY",
            VERSION:label=VERSION
      )
    """)

  def Run(self, args):
    feature = self.GetFeature(v1alpha1=True)

    cluster_status = []
    feature_spec_memberships = utils.GetFeatureSpecMemberships(
        feature, self.v1alpha1_messages)
    feature_state_memberships = utils.GetFeatureStateMemberships(feature)

    for membership, config in feature_spec_memberships.items():
      dict_entry = {
          'NAME': os.path.basename(membership),
          'SECURITYPOLICY': config.securityPolicy,
          'VERSION': config.version
      }
      if membership in feature_state_memberships:
        details = feature_state_memberships[membership]
        dict_entry.update({
            'DESCRIPTION': details.description,
            'STATUS': details.code
        })

      cluster_status.append(dict_entry)

    return cluster_status

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
"""The command to install Cloud Build on a cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.command_lib.container.hub.build import utils
from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import exceptions

# Pull out the example text so the example command can be one line without the
# py linter complaining. The docgen tool properly breaks it into multiple lines.
EXAMPLES = """\
    To install Cloud Build hybrid worker pools on a membership named
    MEMBERSHIP-ID with a default security policy of NON_PRIVILEGED and the
    latest version of Cloud Build, run:

      $ {command} --membership=[MEMBERSHIP-ID]

    To install Cloud Build hybrid worker pools on a membership named
    MEMBERSHIP-ID with a specified security policy [SECURITY_POLICY]
    and version [X.Y.Z], run:

      $ {command} --membership=[MEMBERSHIP-ID] --security-policy=[SECURITY_POLICY] --version=[X.Y.Z]
"""


@gbase.Hidden
class Install(base.UpdateCommand):
  """Install Cloud Build on the specified member."""

  detailed_help = {'EXAMPLES': EXAMPLES}

  feature_name = 'cloudbuild'
  LATEST_VERSION = '0.1.0'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--membership',
        type=str,
        help=textwrap.dedent("""\
            The name of the Membership to install Cloud Build hybrid worker pools on.
            """),
        required=True,
    )
    parser.add_argument(
        '--security-policy',
        type=str,
        default='NON_PRIVILEGED',
        choices=['NON_PRIVILEGED', 'PRIVILEGED'],
        help=textwrap.dedent("""\
            Privilege options for build steps.
            """),
        required=False,
    )
    parser.add_argument(
        '--version',
        type=str,
        default=cls.LATEST_VERSION,
        choices=[cls.LATEST_VERSION],
        help=textwrap.dedent("""\
            Cloud Build version to be installed on the member.
            """),
        required=False,
    )

  def Run(self, args):
    feature = self.GetFeature(v1alpha1=True)
    membership = args.membership
    utils.VerifyMembership(membership)

    version = self._parse_version(args.version)

    feature_spec_memberships = utils.GetFeatureSpecMemberships(
        feature, self.v1alpha1_messages)
    # TODO(b/189313110): Move check to CLH/API
    if membership in feature_spec_memberships:
      raise exceptions.Error(
          'Cloud Build hybrid worker pool installation on the member already exists.'
      )

    securitypolicy = utils.ParseSecuritypolicy(args.security_policy,
                                               self.v1alpha1_messages)
    spec = self.v1alpha1_messages.CloudBuildMembershipConfig(
        securityPolicy=securitypolicy,
        version=version,
    )
    feature = utils.MembershipSpecPatch(self.v1alpha1_messages, membership,
                                        spec)
    self.Update(['cloudbuild_feature_spec.membership_configs'],
                feature,
                v1alpha1=True)

  def _parse_version(self, version):
    if version is None:
      return self.LATEST_VERSION
    return version

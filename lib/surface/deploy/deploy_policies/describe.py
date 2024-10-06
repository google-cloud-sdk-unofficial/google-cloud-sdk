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
"""Describes a Gcloud Deploy Policy resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import deploy_policy_util
from googlecloudsdk.command_lib.deploy import exceptions as deploy_exceptions
from googlecloudsdk.command_lib.deploy import manifest_util
from googlecloudsdk.command_lib.deploy import resource_args

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
  To describe a deploy policy called 'test-policy' in region 'us-central1', run:

     $ {command} test-policy --region=us-central1

""",
}


def _CommonArgs(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  resource_args.AddDeployPolicyResourceArg(parser, positional=True)


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Show details about a deploy policy."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      deploy_exceptions.HTTP_ERROR_FORMAT
  )
  def Run(self, args):
    """This is what gets called when the user runs this command."""
    policy_ref = args.CONCEPTS.deploy_policy.Parse()
    # Check if the policy exists.
    policy_obj = deploy_policy_util.GetDeployPolicy(policy_ref)
    manifest = collections.OrderedDict(
        apiVersion=manifest_util.API_VERSION_V1,
        kind=manifest_util.DEPLOY_POLICY_KIND,
    )
    for f in policy_obj.all_fields():
      value = getattr(policy_obj, f.name)
      # Only output populated values.
      if value:
        if f.name == 'rules':
          manifest_util.ExportDeployPolicyRules(manifest, value)
          continue
        manifest[f.name] = value
    return manifest

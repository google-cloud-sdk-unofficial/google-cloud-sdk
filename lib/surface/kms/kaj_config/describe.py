# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Describe the KajPolicyConfig."""

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  r"""Describe the KajPolicyConfig of an organization/folder/project.

  {command} can be used to retrieve the KajPolicyConfig, the default KAJ policy,
  of an organization/folder/project.

  ## EXAMPLES

  The following command retrieves the KajPolicyConfig of organizations/123:

  $ {command} --organization=123

  The following command retrieves the KajPolicyConfig of folders/456:

  $ {command} --folder=456

  The following command retrieves the KajPolicyConfig of projects/789:

  $ {command} --project=789
  """

  @staticmethod
  def Args(parser):
    flags.AddKajPolicyParentFlag(parser)

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    return flags.GetKajPolicyConfig(client, messages, args)

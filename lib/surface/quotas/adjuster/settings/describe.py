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
"""QuotaAdjusterSettings get command."""

from googlecloudsdk.api_lib.quotas import quota_adjuster_settings
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.quotas import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class Describe(base.DescribeCommand):
  """Gets details of the QuotaAdjusterSettings for a container.

  This command gets the QuotaAdjusterSettings for a container. The supported
  containers can be projects, folders, or organizations.

  ## EXAMPLES

  To get the QuotaAdjusterSettings for container 'projects/123', run:

    $ {command} --project=12321


  To get the QuotaAdjusterSettings for container 'folders/123', run:

    $ {command} --folder=123
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    flags.AddResourceFlags(parser, 'container id')

  def Run(self, args):
    """Run command.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The requested QuotaInfo for the service and consumer.
    """
    return quota_adjuster_settings.GetQuotaAdjusterSettings(args)

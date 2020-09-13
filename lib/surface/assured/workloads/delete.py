# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to delete an existing Assured Workload."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.api_lib.assured import workloads as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.assured import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

_DETAILED_HELP = {
    'DESCRIPTION':
        'Delete a given Assured Workloads environment.',
    'EXAMPLES':
        """ \
        To delete an Assured Workload environment in the us-central1 region,
        belonging to an organization with ID 123, with workload ID 456 and an
        etag of 789, run:

          $ {command} organizations/123/locations/us-central1/workloads/456 --etag=789
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  """Delete Assured Workloads environment."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddDeleteWorkloadFlags(parser)

  def Run(self, args):
    if not console_io.PromptContinue(
        message='You are about to delete Workload [{}]'.format(args.resource),
        default=True):
      log.status.Print('Aborted by user.')
      return

    with endpoint_util.AssuredWorkloadsEndpointOverridesFromResource(
        resource=args.resource):
      client = apis.WorkloadsClient()
      return client.Delete(name=args.resource, etag=args.etag)

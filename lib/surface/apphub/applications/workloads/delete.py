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
"""Command to delete a Application workload in the Project/Location."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub.applications import workloads as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.apphub import flags

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To delete the Workload `my-workload` from the Application `my-app` in
        location `us-east1`, run:

          $ {command} my-workload --application=my-app --location=us-east1
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete an Apphub application workload."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddDeleteApplicationWorkloadFlags(parser)

  def Run(self, args):
    """Run the delete command."""
    client = apis.WorkloadsClient()
    workload_ref = args.CONCEPTS.workload.Parse()
    if not workload_ref.Name():
      raise exceptions.InvalidArgumentException(
          'workload', 'workload id must be non-empty.'
      )
    return client.Delete(
        workload=workload_ref.RelativeName(), async_flag=args.async_
    )

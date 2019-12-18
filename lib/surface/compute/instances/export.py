# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Export Compute Engine virtual machine instance command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Export(base.Command):
  """Export a Compute Engine virtual machine instance's configuration to a file."""

  DETAILED_HELP = {
      'DESCRIPTION':
          """
        Export a Compute Engine virtual machine instance's configuration to a file.
        """,
      'EXAMPLES':
          """
        A virtual machine can be exported by running:

          $ {command} my-instance --destination=<path-to-file>
        """,
  }

  @classmethod
  def GetApiVersion(cls):
    """Returns the API version based on the release track."""
    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif cls.ReleaseTrack() == base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  @classmethod
  def GetSchemaPath(cls, for_help=False):
    """Returns the resource schema path."""
    return export_util.GetSchemaPath(
        'compute', cls.GetApiVersion(), 'Instance', for_help=for_help)

  @classmethod
  def Args(cls, parser):
    flags.INSTANCE_ARG.AddArgument(parser, operation_type='export')
    export_util.AddExportFlags(parser, cls.GetSchemaPath(for_help=True))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    # Retrieve the specified compute instance.
    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))

    request = client.messages.ComputeInstancesGetRequest(
        **instance_ref.AsDict())
    instance = client.MakeRequests([(client.apitools_client.instances, 'Get',
                                     request)])[0]

    # Get JSON Schema for Compute Engine instances (located in
    # third_party/py/googlecloudsdk/schemas/...).
    schema_path = self.GetSchemaPath(for_help=False)

    # Write configuration data to either designated file or stdout.
    if args.destination:
      with files.FileWriter(args.destination) as stream:
        export_util.Export(
            message=instance, stream=stream, schema_path=schema_path)
      return log.status.Print(
          'Exported [{}] to \'{}\'.'.format(
              instance.name, args.destination))
    else:
      export_util.Export(
          message=instance, stream=sys.stdout, schema_path=schema_path)

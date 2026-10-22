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
"""Export instance template command."""


import sys
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_templates import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.util import files

DETAILED_HELP = {
    'DESCRIPTION': (
        """\
        Exports the configuration for the instance template to a file.
        This configuration can be imported at a later time.
        """
    ),
    'EXAMPLES': (
        """\
        An instance template can be exported by running:

          $ {command} NAME --destination=<path-to-file>
        """
    ),
}


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.GA,
    base.ReleaseTrack.PREVIEW,
)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
class Export(base.Command):
  """Export an instance template."""

  detailed_help = DETAILED_HELP
  support_region_flag = True

  @classmethod
  def GetApiVersion(cls):
    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif cls.ReleaseTrack() == base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  @classmethod
  def GetSchemaPath(cls, for_help=False):
    return export_util.GetSchemaPath(
        'compute', cls.GetApiVersion(), 'InstanceTemplate', for_help=for_help
    )

  @classmethod
  def Args(cls, parser):
    cls.InstanceTemplateArg = flags.MakeInstanceTemplateArg(
        include_regional=cls.support_region_flag
    )
    cls.InstanceTemplateArg.AddArgument(parser, operation_type='export')
    export_util.AddExportFlags(parser, cls.GetSchemaPath(for_help=True))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_template_ref = self.InstanceTemplateArg.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
        default_scope=compute_scope.ScopeEnum.GLOBAL,
    )

    if instance_template_ref.Collection() == 'compute.instanceTemplates':
      service_client = client.apitools_client.instanceTemplates
      request_message = client.messages.ComputeInstanceTemplatesGetRequest
    else:
      service_client = client.apitools_client.regionInstanceTemplates
      request_message = client.messages.ComputeRegionInstanceTemplatesGetRequest

    instance_template = client.MakeRequests([(
        service_client,
        'Get',
        request_message(**instance_template_ref.AsDict()),
    )])[0]

    if args.destination:
      with files.FileWriter(args.destination) as stream:
        export_util.Export(
            message=instance_template,
            stream=stream,
            schema_path=self.GetSchemaPath(),
        )
    else:
      export_util.Export(
          message=instance_template,
          stream=sys.stdout,
          schema_path=self.GetSchemaPath(),
      )

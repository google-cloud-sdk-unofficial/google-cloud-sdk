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
"""Command for listing Device Run software versions."""

from collections.abc import Iterator
from typing import Any

from googlecloudsdk.api_lib import device_run
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.device_run import resource_args
from googlecloudsdk.core import resources


def _GetUri(resource: Any) -> str:
  """Returns the self link URI for a software version resource."""
  ref = resources.REGISTRY.Parse(
      resource.name,
      collection='devicerun.projects.locations.softwareVersions',
  )
  return ref.SelfLink()


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List available Device Run software versions."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    resource_args.AddLocationResourceArg(parser, 'list software versions')

    parser.display_info.AddFormat(
        'table(name.segment(-1):label=ID, '
        'displayName:label=NAME, '
        'softwareType:label=SOFTWARE_TYPE, '
        'version:label=VERSION, '
        'lifecycle.state:label=STATE, '
        'isDefault:label=IS_DEFAULT)'
    )
    parser.display_info.AddUriFunc(_GetUri)

  def Run(self, args: parser_extensions.Namespace) -> Iterator[Any]:
    location_ref = args.CONCEPTS.location.Parse()
    client = device_run.SoftwareVersionsClient(api_version='v1alpha')
    return client.List(location_ref, limit=args.limit)


List.detailed_help = {
    'DESCRIPTION': 'List available Device Run software versions.',
    'EXAMPLES': (
        """\
The following command lists all Device Run software versions:

  $ {command}
"""
    ),
}

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
"""Command for listing Device Run locations."""

from googlecloudsdk.api_lib import device_run
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List all Device Run locations."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(
        'table(locationId:label=LOCATION_ID, displayName:label=NAME)'
    )

    def UriFunc(resource):
      ref = resources.REGISTRY.Parse(
          resource.name, collection='devicerun.projects.locations'
      )
      return ref.SelfLink()

    parser.display_info.AddUriFunc(UriFunc)

  def Run(self, args):
    project_ref = resources.REGISTRY.Parse(
        properties.VALUES.core.project.GetOrFail(),
        collection='devicerun.projects',
    )
    client = device_run.LocationsClient(api_version='v1alpha')
    return list(client.List(project_ref, limit=args.limit))


List.detailed_help = {
    'DESCRIPTION':
        'List all Device Run locations.',
    'EXAMPLES':
        """\
The following command lists all Device Run locations sorted alphabetically by name:

  $ {command} --sort-by=locationId
""",
}

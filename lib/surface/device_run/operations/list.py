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
"""Command for listing Device Run operations."""

from googlecloudsdk.api_lib import device_run
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.device_run import resource_args
from googlecloudsdk.core import resources


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List all Device Run operations."""

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser, 'list operations')
    parser.display_info.AddFormat(
        'table(name.basename():label=OPERATION_ID, done)'
    )

    def UriFunc(resource):
      ref = resources.REGISTRY.Parse(
          resource.name, collection='devicerun.projects.locations.operations'
      )
      return ref.SelfLink()

    parser.display_info.AddUriFunc(UriFunc)

  def Run(self, args):
    location_ref = args.CONCEPTS.location.Parse()
    client = device_run.OperationsClient(api_version='v1alpha')
    return list(client.List(location_ref, limit=args.limit))


List.detailed_help = {
    'DESCRIPTION': 'List all Device Run operations.',
    'EXAMPLES': (
        """\
The following command lists all Device Run operations in us-central1:

  $ {command} --location=us-central1
"""
    ),
}

# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Command for listing subnetworks."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import exceptions


class List(base_classes.RegionalLister):
  """List subnetworks."""

  @staticmethod
  def Args(parser):
    base_classes.RegionalLister.Args(parser)

    parser.add_argument(
        '--network',
        help='Only show subnetworks of a specific network.')

  @property
  def service(self):
    return self.compute.subnetworks

  @property
  def resource_type(self):
    return 'subnetworks'

  def Run(self, args):
    if args.uri and args.network is not None:
      # TODO(b/25276193): --uri and --network don't work together
      raise exceptions.InvalidArgumentException(
          '--uri', '--uri cannot be used with --network')

    for resource in super(List, self).Run(args):
      if args.network is not None:
        if resource.get('network', None) == args.network:
          yield resource
      else:
        yield resource


List.detailed_help = base_classes.GetRegionalListerHelp('subnetworks')

# Copyright 2018 Google Inc. All Rights Reserved.
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
"""`gcloud access-context-manager zones update` command."""
from googlecloudsdk.api_lib.accesscontextmanager import zones as zones_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import zones
from googlecloudsdk.command_lib.util.args import repeated


class Update(base.UpdateCommand):
  """Update an existing access zone."""

  @staticmethod
  def Args(parser):
    zones.AddResourceArg(parser, 'to update')
    zones.AddZoneUpdateArgs(parser)

  def Run(self, args):
    client = zones_api.Client()
    zone_ref = args.CONCEPTS.zone.Parse()
    result = repeated.CachedResult.FromFunc(client.Get, zone_ref)

    return client.Patch(
        zone_ref,
        description=args.description,
        title=args.title,
        zone_type=zones.GetTypeEnumMapper().GetEnumForChoice(args.type),
        resources=zones.ParseResources(args, result),
        restricted_services=zones.ParseRestrictedServices(args, result),
        unrestricted_services=zones.ParseUnrestrictedServices(args, result),
        levels=zones.ParseLevels(args, result, zone_ref.accessPoliciesId))

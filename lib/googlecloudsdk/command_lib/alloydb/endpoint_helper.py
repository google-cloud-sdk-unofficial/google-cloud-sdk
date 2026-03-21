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
"""Helper functions for AlloyDB endpoint requests."""

from googlecloudsdk.command_lib.util.apis import arg_utils


def ConstructCreateRequestFromArgs(alloydb_messages, location_ref, args):
  """Returns the endpoint create request based on args."""
  endpoint = alloydb_messages.Endpoint()
  endpoint.targetInstances = args.target_instances
  endpoint.endpointType = arg_utils.ChoiceToEnum(
      args.endpoint_type,
      alloydb_messages.Endpoint.EndpointTypeValueValuesEnum,
  )

  return alloydb_messages.AlloydbProjectsLocationsEndpointsCreateRequest(
      endpoint=endpoint,
      endpointId=args.endpoint,
      parent=location_ref.RelativeName(),
  )




# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Flags and helpers for general Cloud NetApp Files commands."""


import random

from googlecloudsdk.api_lib.netapp import netapp_client
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


truthy = ['true', 'True', 'TRUE', 'on', 'ON', 'yes', 'YES']
falsey = ['false', 'False', 'FALSE', 'off', 'OFF', 'no', 'NO']


class Error(exceptions.Error):
  """Base class for exceptions in this module."""


class InvalidArgumentError(Error):
  """Raised when command line argument constraints are violated."""


def ParseLocationForTrials(args, release_track):
  """Parses location from args, falling back to a random location if not specified."""
  location_ref = args.CONCEPTS.location.Parse()
  if not location_ref:
    project = properties.VALUES.core.project.GetOrFail()
    project_ref = resources.REGISTRY.Parse(
        project, collection='netapp.projects'
    )
    client = netapp_client.NetAppClient(release_track=release_track)
    locations = list(client.ListLocations(project_ref))
    if not locations:
      raise exceptions.Error(
          'No available locations found.'
          ' Please ensure the Cloud NetApp Volumes API is enabled.'
      )
    chosen_location = random.choice(locations)
    location_name = chosen_location.name
    location_ref = resources.REGISTRY.Parse(
        location_name, collection='netapp.projects.locations'
    )
  return location_ref


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
"""File to add optional custom code to extend __init__.py."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.core import properties

_GLOBAL_LOCATIONS = frozenset(['global'])


def _GetLocation(args):
  """Extracts the location ID from parsed concept arguments, if present."""
  if args.CONCEPTS is None:
    return None
  for concept_name in ('task_store', 'location'):
    try:
      concept = args.CONCEPTS.GetValue(concept_name)
    except parser_errors.UnknownDestinationException:
      continue
    if concept is None:
      continue
    try:
      ref = concept.Parse()
    except handlers.ParseError:
      continue
    if ref is not None:
      location = ref.AsDict().get('locationsId')
      if location:
        return location
  return None


def _SetRegionalEndpoint(args, version=constants.BETA_VERSION):
  """Overrides the aiplatform endpoint when a regional location is specified."""
  location = _GetLocation(args)
  if not location or location in _GLOBAL_LOCATIONS:
    return
  endpoint = endpoint_util.GetEffectiveEndpoint(
      version=version, region=location
  )
  properties.VALUES.api_endpoint_overrides.aiplatform.Set(endpoint)


@base.DefaultUniverseOnly
class TaskStoresAlpha(base.Group):
  """Optional no-auto-generated code for ALPHA."""

  def Filter(self, context, args):
    super(TaskStoresAlpha, self).Filter(context, args)
    _SetRegionalEndpoint(args, version=constants.BETA_VERSION)


@base.DefaultUniverseOnly
class TaskStoresBeta(TaskStoresAlpha):
  """Optional no-auto-generated code for BETA."""


@base.DefaultUniverseOnly
class TaskStoresGa(base.Group):
  """Optional no-auto-generated code for GA."""

  def Filter(self, context, args):
    super(TaskStoresGa, self).Filter(context, args)
    _SetRegionalEndpoint(args, version=constants.GA_VERSION)

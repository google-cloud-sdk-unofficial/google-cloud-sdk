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
"""Flags and helpers for the compute network-location-bindings commands."""

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties

# NetworkLocationBinding is only available in the compute `preview` API
# version, which is served from the `/compute/v1/` base URL. The resource spec
# pins `api_version` so that both completion and full-URL parsing resolve the
# collection against the preview client rather than the registry default (v1).
_API_VERSION = 'preview'

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      region.basename(),
      network.basename(),
      state,
      status.bindingType:label=BINDING_TYPE
    )"""


def RegionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      help_text=(
          'Region of the {resource}. If not specified, the `compute/region`'
          ' property is used.'
      ),
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.compute.region),
      ],
  )


def NetworkLocationBindingAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='name',
      help_text='Name of the {resource}.',
  )


def GetNetworkLocationBindingResourceSpec():
  return concepts.ResourceSpec(
      'compute.networkLocationBindings',
      api_version=_API_VERSION,
      resource_name='network location binding',
      project=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      region=RegionAttributeConfig(),
      networkLocationBinding=NetworkLocationBindingAttributeConfig(),
  )


def AddNetworkLocationBindingResourceArg(parser, verb):
  """Adds the network location binding positional resource argument.

  Args:
    parser: The argparse parser to add the argument to.
    verb: str, the verb to describe the resource, e.g. 'to describe'.
  """
  concept_parsers.ConceptParser(
      [
          presentation_specs.ResourcePresentationSpec(
              'name',
              GetNetworkLocationBindingResourceSpec(),
              'The network location binding {}.'.format(verb),
              required=True,
          )
      ]
  ).AddToParser(parser)

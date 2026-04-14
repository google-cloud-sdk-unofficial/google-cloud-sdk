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
"""List command for Orchestration Pipelines Resource Types."""

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import registry


@calliope_base.Hidden
@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class List(calliope_base.ListCommand):
  """List supported orchestration pipelines resource types."""

  detailed_help = {
      "DESCRIPTION": (
          "List all resource types supported by orchestration pipelines "
          "deployments."
      ),
      "EXAMPLES": (
          """
        To list all supported resource types, run:

          $ {command}

        To discover a specific resource type and its properties, run:

          $ {command} --filter="type=bigquery.table"

        To output the list in JSON format, run:

          $ {command} --format=json
      """
      ),
  }

  @staticmethod
  def Args(parser):
    """Add arguments to the parser."""
    parser.display_info.AddFormat("""
        table(
            type:label=TYPE,
            description:label=DESCRIPTION,
            documentation_uri:label=DOCUMENTATION_URI
        )
    """)

  def Run(self, args):
    """Run the list command."""
    results = []
    for type_name, handler_class in registry.GetHandlerClasses().items():
      # Instantiate with dummy values to read properties
      dummy_resource = type(
          "DummyResource",
          (),
          {
              "type": type_name,
              "name": "dummy",
              "definition": {},
              "metadata": None,
              "api_version": None,
          },
      )()
      dummy_environment = type(
          "DummyEnvironment", (), {"project": "dummy", "region": "dummy"}
      )()

      # Bypass __init__ to avoid slow API client initialization and auth
      handler_instance = handler_class.__new__(handler_class)
      handler_instance.resource = dummy_resource
      handler_instance.environment = dummy_environment

      api_version = handler_instance._api_version  # pylint: disable=protected-access
      parent_type = handler_instance.get_parent_resource_type()
      doc_url = handler_instance.get_documentation_uri()

      description = handler_class.description

      results.append({
          "type": type_name,
          "parent_type": parent_type,
          "api_version": api_version,
          "description": description,
          "documentation_uri": doc_url,
      })

    # Sort results by resource type for predictable output
    return sorted(results, key=lambda x: x["type"])

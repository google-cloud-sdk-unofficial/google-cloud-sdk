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
"""Shared resource args for FTP commands."""

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def location_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='The region where the {resource} is located.')


def server_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='server', help_text='The ID of the FTP server.')


def get_server_resource_spec():
  return concepts.ResourceSpec(
      'ftp.projects.locations.servers',
      resource_name='server',
      serversId=server_attribute_config(),
      locationsId=location_attribute_config(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def add_server_resource_arg(parser, verb):
  """Adds a resource argument for an FTP server.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to start'.
  """
  concept_parsers.ConceptParser.ForResource(
      'server',
      get_server_resource_spec(),
      'The FTP server {}.'.format(verb),
      required=True).AddToParser(parser)

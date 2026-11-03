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
"""The create command for BigLake Iceberg REST catalogs views."""

import json
import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import arguments
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

help_text = textwrap.dedent("""\
    To create a view `my_view` in parent catalog `my-catalog` and namespace `my-namespace`
    using a creation request from `view_creation.json`, run:

      $ {command} --namespace=my-namespace --catalog=my-catalog --create-from-file=view_creation.json

    The view name, schema, and view-version fields are required and must be specified in the JSON file.
    The JSON file format must adhere to the Apache Iceberg REST Catalog Open API specification
    for `CreateViewRequest`.
    """)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
class Create(base.CreateCommand):
  """Create a BigLake Iceberg view."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddNamespaceResourceArg(parser, 'to create', positional=False)
    arguments.AddViewCreateArgs(parser)

  def Run(self, args):
    namespace_ref = args.CONCEPTS.namespace.Parse()

    try:
      json_content = files.ReadFileContents(args.create_from_file)
      data = json.loads(json_content)
    except files.Error as e:
      raise exceptions.Error(
          'Failed to read creation file [{}]: {}'.format(
              args.create_from_file, e
          )
      )
    except ValueError as e:
      raise exceptions.Error(
          'Failed to parse JSON from file [{}]: {}'.format(
              args.create_from_file, e
          )
      )

    # Validate that the name is in JSON.
    if 'name' not in data:
      raise exceptions.Error(
          'View name must be specified in the JSON file [{}] via the "name" '
          'field.'.format(args.create_from_file)
      )
    view_id = data['name']

    # Validate that the schema is in JSON.
    if 'schema' not in data:
      raise exceptions.Error(
          'View schema must be specified in the JSON file [{}] via the '
          '"schema" field.'.format(args.create_from_file)
      )

    # Validate that the view-version is in JSON.
    if 'view-version' not in data:
      raise exceptions.Error(
          'View version must be specified in the JSON file [{}] via the '
          '"view-version" field.'.format(args.create_from_file)
      )

    # Iceberg REST API is OSS compliant, so it actually sends and/or receives a
    # raw HTTP body not protos.
    response_json = util.CreateView(
        namespace_ref.catalogsId,
        namespace_ref.namespacesId,
        data,
        project_id=namespace_ref.projectsId,
    )
    response = json.loads(response_json)

    log.CreatedResource(
        util.GetViewName(
            namespace_ref.catalogsId,
            namespace_ref.namespacesId,
            view_id,
            project_id=namespace_ref.projectsId,
        ),
        'view',
    )
    return response

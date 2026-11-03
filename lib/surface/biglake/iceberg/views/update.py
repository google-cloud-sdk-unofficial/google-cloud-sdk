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
"""The update command for BigLake Iceberg REST catalogs views."""

import json
import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import arguments
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import log

help_text = textwrap.dedent("""\
    To add or update properties in a view `my-view` in parent catalog `my-catalog` and namespace `my-namespace`, with properties `key1=value1,key2=value2`, run:

      $ {command} my-view --namespace=my-namespace --catalog=my-catalog --update-properties=key1=value1,key2=value2

    To remove properties `key1,key2` from a view, run:

      $ {command} my-view --namespace=my-namespace --catalog=my-catalog --remove-properties=key1,key2

    To clear all properties from a view, run:

      $ {command} my-view --namespace=my-namespace --catalog=my-catalog --clear-properties
    """)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
class Update(base.UpdateCommand):
  """Update a BigLake Iceberg view."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddViewResourceArg(parser, 'to update', positional=True)
    arguments.AddUpdatePropertiesArgs(parser)

  def Run(self, args):
    view_ref = args.CONCEPTS.view.Parse()
    catalog_id = view_ref.catalogsId
    namespace_id = view_ref.namespacesId
    view_id = view_ref.viewsId
    project_id = view_ref.projectsId

    # Fetch current view metadata
    raw_metadata = util.GetView(
        catalog_id, namespace_id, view_id, project_id=project_id
    )
    view_data = json.loads(raw_metadata)
    metadata = view_data.get('metadata', view_data)

    view_uuid = metadata.get('view-uuid')
    current_properties = metadata.get('properties', {})

    requirements = []
    if view_uuid:
      requirements.append({'type': 'assert-view-uuid', 'uuid': view_uuid})

    updates = []
    removals = []
    if args.clear_properties:
      removals.extend(current_properties.keys())
    if args.remove_properties:
      for prop in args.remove_properties:
        if prop not in removals:
          removals.append(prop)

    if removals:
      updates.append({'action': 'remove-properties', 'removals': removals})

    if args.update_properties:
      updates.append(
          {'action': 'set-properties', 'updates': args.update_properties}
      )

    commit_request = {
        'identifier': {
            'name': view_id,
            'namespace': [namespace_id],
        },
        'requirements': requirements,
        'updates': updates,
    }

    response_json = util.UpdateView(
        catalog_id,
        namespace_id,
        view_id,
        commit_request,
        project_id=project_id,
    )
    view_name = util.GetViewName(
        catalog_id, namespace_id, view_id, project_id=project_id
    )
    log.UpdatedResource(view_name, 'view')
    return json.loads(response_json)

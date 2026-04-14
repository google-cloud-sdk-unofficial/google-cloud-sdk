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
"""The update command for BigLake Iceberg REST catalogs tables."""

import json
import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import arguments
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import log


help_text = textwrap.dedent("""\
    To add or update properties in a table `my-table` in parent catalog `my-catalog` and namespace `my-namespace`, with properties `key1=value1,key2=value2`, run:

      $ {command} my-table --namespace=my-namespace --catalog=my-catalog --update-properties=key1=value1,key2=value2

    To remove properties `key1,key2` from a table, run:

      $ {command} my-table --namespace=my-namespace --catalog=my-catalog --remove-properties=key1,key2

    To clear all properties from a table, run:

      $ {command} my-table --namespace=my-namespace --catalog=my-catalog --clear-properties
    """)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class Update(base.UpdateCommand):
  """Update a BigLake Iceberg table."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddTableResourceArg(parser, 'to update', positional=True)
    arguments.AddUpdatePropertiesArgs(parser)

  def Run(self, args):
    table_ref = args.CONCEPTS.table.Parse()
    catalog_id = table_ref.catalogsId
    namespace_id = table_ref.namespacesId
    table_id = table_ref.tablesId

    # Get current table state
    # Iceberg REST API is OSS compliant, so it actually sends and/or receives a
    # raw HTTP body not protos. There is trouble setting and accessing those
    # HTTP body fields without manual creation.
    raw_metadata = util.GetTable(catalog_id, namespace_id, table_id)
    table_data = json.loads(raw_metadata)
    metadata = table_data.get('metadata', {})

    # Construct Update/CommitTableRequest
    table_uuid = metadata.get('table-uuid')
    current_snapshot_id = metadata.get('current-snapshot-id')
    current_properties = metadata.get('properties', {})

    requirements = [
        {'type': 'assert-table-uuid', 'uuid': table_uuid},
    ]
    if current_snapshot_id is not None and current_snapshot_id != -1:
      requirements.append({
          'type': 'assert-ref-snapshot-id',
          'ref': 'main',
          'snapshot-id': current_snapshot_id,
      })

    updates = []
    if args.clear_properties:
      to_remove = list(current_properties.keys())
      if to_remove:
        updates.append({'action': 'remove-properties', 'removals': to_remove})

    if args.remove_properties:
      updates.append(
          {'action': 'remove-properties', 'removals': args.remove_properties}
      )

    if args.update_properties:
      updates.append(
          {'action': 'set-properties', 'updates': args.update_properties}
      )

    commit_request = {
        'identifier': {
            'name': table_id,
            'namespace': [namespace_id],
        },
        'requirements': requirements,
        'updates': updates,
    }

    # Call update
    # Iceberg REST API is OSS compliant, so it actually sends and/or receives a
    # raw HTTP body not protos. There is trouble setting and accessing those
    # HTTP body fields without manual creation.
    response_json = util.UpdateTable(
        catalog_id, namespace_id, table_id, commit_request
    )
    table_name = util.GetTableName(catalog_id, namespace_id, table_id)
    log.UpdatedResource(table_name, 'table')
    return json.loads(response_json)

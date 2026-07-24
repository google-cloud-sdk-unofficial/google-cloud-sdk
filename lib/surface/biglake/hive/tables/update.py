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
"""The update command for BigLake Hive tables."""

import textwrap
from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import arguments
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


help_text = textwrap.dedent("""\
    To update a table `my_table` in parent catalog `my-catalog` and database `my-database`
    with a new description and location URI, run:

      $ {command} my_table --database=my-database --catalog=my-catalog --description="New description" --location-uri="gs://my-bucket/my-database/my_table_new_location"

    To update columns from a file, run:

      $ {command} my_table --database=my-database --catalog=my-catalog --columns-from-file=columns.yaml

    Example `columns.yaml`:

    ```yaml
      - name: id
        type: int
        comment: "identifier column"
      - name: name
        type: string
    ```
    """)


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA
)
@base.DefaultUniverseOnly
class Update(base.UpdateCommand):
  """Update a BigLake Hive table."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddTableResourceArg(
        parser, 'to update', positional=True, table_type='Hive'
    )
    arguments.AddHiveTableUpdateArgs(parser)

  def Run(self, args):
    table_ref = args.CONCEPTS.table.Parse()

    update_flags = [
        'description',
        'parameters',
        'location_uri',
        'columns_from_file',
    ]
    if not any(args.IsSpecified(flag) for flag in update_flags):
      raise exceptions.Error(
          'At least one field to update must be specified. Use --description,'
          ' --parameters, --location-uri, or --columns-from-file.'
      )

    # We use v1beta client for Hive metastore operations.
    client = apis.GetClientInstance('biglake', 'v1beta')
    messages = apis.GetMessagesModule('biglake', 'v1beta')

    hive_table = messages.HiveTable()

    if args.IsSpecified('description'):
      hive_table.description = args.description

    if args.IsSpecified('parameters'):
      hive_table.parameters = messages.HiveTable.ParametersValue(
          additionalProperties=[
              messages.HiveTable.ParametersValue.AdditionalProperty(
                  key=k, value=v
              )
              for k, v in args.parameters.items()
          ]
      )

    if args.IsSpecified('location_uri') or args.IsSpecified(
        'columns_from_file'
    ):
      hive_table.storageDescriptor = messages.StorageDescriptor()
      if args.IsSpecified('location_uri'):
        hive_table.storageDescriptor.locationUri = args.location_uri
      if args.IsSpecified('columns_from_file'):
        hive_table.storageDescriptor.columns = util.ParseHiveTableColumns(
            args.columns_from_file, messages
        )

    # Set the name to the full resource name as required by the API.
    name = table_ref.RelativeName()
    hive_table.name = name

    mask_paths = []
    if args.IsSpecified('description'):
      mask_paths.append('description')
    if args.IsSpecified('parameters'):
      mask_paths.append('parameters')
    if args.IsSpecified('location_uri'):
      mask_paths.append('storage_descriptor.location_uri')
    if args.IsSpecified('columns_from_file'):
      mask_paths.append('storage_descriptor.columns')
    update_mask = ','.join(mask_paths)

    request = (
        messages.BiglakeHiveV1betaProjectsCatalogsDatabasesTablesPatchRequest(
            name=name,
            hiveTable=hive_table,
            updateMask=update_mask,
        )
    )

    response = client.hive_v1beta_projects_catalogs_databases_tables.Patch(
        request
    )

    log.UpdatedResource(name, 'table')
    return response

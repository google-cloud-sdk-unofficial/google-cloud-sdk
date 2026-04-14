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
"""The update command for BigLake Iceberg REST catalogs namespaces."""

import json
import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import arguments
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import log


help_text = textwrap.dedent("""\
    To clear all properties from a namespace in parent catalog `my-catalog`, run:

      $ {command} my-namespace --catalog=my-catalog --clear-properties

    To add or update properties in a namespace in parent catalog `my-catalog`, with properties `key1=value1,key2=value2`, run:

      $ {command} my-namespace --catalog=my-catalog --update-properties=key1=value1,key2=value2

    To remove properties `key1,key2` from a namespace in parent catalog `my-catalog`, run:

      $ {command} my-namespace --catalog=my-catalog --remove-properties=key1,key2
    """)


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.DefaultUniverseOnly
class UpdateNamespace(base.UpdateCommand):
  """Update a BigLake Iceberg REST namespace."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddNamespaceResourceArg(parser, 'to update', positional=True)
    arguments.AddUpdatePropertiesArgs(parser)

  def Run(self, args):
    client = util.GetClientInstance(self.ReleaseTrack())
    messages = client.MESSAGES_MODULE

    namespace_name = util.GetNamespaceName(args.catalog, args.namespace)
    update_keys = (
        args.update_properties.keys() if args.update_properties else []
    )
    if args.clear_properties:
      get_request = messages.BiglakeIcebergV1RestcatalogV1ProjectsCatalogsNamespacesGetRequest(
          name=namespace_name
      )
      get_response = (
          client.iceberg_v1_restcatalog_v1_projects_catalogs_namespaces.Get(
              get_request
          )
      )
      if (
          get_response.properties
          and get_response.properties.additionalProperties
      ):
        all_properties = [
            p.key for p in get_response.properties.additionalProperties
        ]
        # Do not remove properties to update and `location` is a required
        # property, so it cannot be removed.
        remove_properties = [
            p
            for p in all_properties
            if p not in update_keys and p != 'location'
        ]
      else:
        remove_properties = []
    else:
      remove_properties = args.remove_properties or []

    update_properties = None
    if args.update_properties:
      update_properties = messages.IcebergNamespaceUpdate.UpdatesValue(
          additionalProperties=[
              messages.IcebergNamespaceUpdate.UpdatesValue.AdditionalProperty(
                  key=k, value=v
              )
              for k, v in args.update_properties.items()
          ]
      )

    namespace = messages.IcebergNamespaceUpdate(
        removals=remove_properties,
        updates=update_properties,
    )

    request = messages.BiglakeIcebergV1RestcatalogV1ProjectsCatalogsNamespacesUpdatePropertiesRequest(
        name=namespace_name,
        icebergNamespaceUpdate=namespace,
    )
    response = client.iceberg_v1_restcatalog_v1_projects_catalogs_namespaces.UpdateProperties(
        request
    )
    log.UpdatedResource(namespace_name, 'namespace')
    log_response = {
        'removed': response.removed,
        'added': response.added,
        'missing': response.missing,
    }
    log.status.Print(json.dumps(log_response))
    return response

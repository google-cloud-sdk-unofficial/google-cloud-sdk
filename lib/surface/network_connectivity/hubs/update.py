# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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


"""Command for updating hubs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_api
from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_connectivity import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Update(base.Command):
  """Update a hub.

  Update the details of a hub.
  """

  @staticmethod
  def Args(parser):
    flags.AddHubResourceArg(parser, 'to be updated')
    flags.AddDescriptionFlag(parser, 'New description of the hub.')
    flags.AddExportPscFlag(parser)
    flags.AddAsyncFlag(parser)
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    client = networkconnectivity_api.HubsClient(
        release_track=self.ReleaseTrack()
    )
    hub_ref = args.CONCEPTS.hub.Parse()
    update_mask = []
    description = args.description
    if description is not None:
      update_mask.append('description')
    export_psc = args.export_psc
    if export_psc is not None:
      update_mask.append('export_psc')

    labels = None
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      original_hub = client.Get(hub_ref)
      labels_update = labels_diff.Apply(
          client.messages.GoogleCloudNetworkconnectivityV1betaHub.LabelsValue,
          original_hub.labels,
      )
      if labels_update.needs_update:
        labels = labels_update.labels
        update_mask.append('labels')

    hub = client.messages.GoogleCloudNetworkconnectivityV1betaHub(
        description=description, exportPsc=export_psc, labels=labels
    )
    op_ref = client.UpdateHubBeta(hub_ref, hub, update_mask)

    log.status.Print('Update request issued for: [{}]'.format(hub_ref.Name()))

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='networkconnectivity.projects.locations.operations',
        api_version=networkconnectivity_util.VERSION_MAP[self.ReleaseTrack()],
    )
    poller = waiter.CloudOperationPoller(
        client.hub_service, client.operation_service
    )

    if op_ref.done:
      log.UpdatedResource(hub_ref.Name(), kind='hub')
      return poller.GetResult(op_resource)

    res = waiter.WaitFor(
        poller,
        op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name),
    )
    log.UpdatedResource(hub_ref.Name(), kind='hub')
    return res


Update.detailed_help = {
    'EXAMPLES': """ \
  To update the description of a hub named ``my-hub'', run:

    $ {command} my-hub --description="The new description of my-hub".
  """,
    'API REFERENCE': """ \
  This command uses the networkconnectivity/v1beta API. The full documentation
  for this API can be found at:
  https://cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  """,
}

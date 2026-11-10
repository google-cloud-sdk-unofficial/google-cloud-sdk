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
"""Delete Software Delivery Trust verification authority command."""

from googlecloudsdk.api_lib.software_delivery_trust import authorities
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.software_delivery_trust import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  r"""Delete a Software Delivery Trust verification authority.

  ## EXAMPLES

  To delete authority 'my-authority' in location 'us-central1':

    $ {command} my-authority --location=us-central1
  """

  @classmethod
  def Args(cls, parser):
    flags.AddAuthorityResourceArg(
        parser, 'The authority to delete.', required=True, positional=True
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    client = authorities.AuthoritiesClient()
    authority_ref = args.CONCEPTS.authority.Parse()
    op = client.Delete(authority_ref)

    if op.done or args.async_:
      return op

    op_resource = resources.REGISTRY.ParseRelativeName(
        op.name,
        collection='softwaredeliverytrust.projects.locations.operations',
    )
    poller = waiter.CloudOperationPollerNoResources(
        client.client.projects_locations_operations
    )
    res = waiter.WaitFor(
        poller,
        op_resource,
        'Waiting for operation [{}] to complete'.format(op.name),
    )
    log.DeletedResource(authority_ref.Name(), kind='authority')
    return res

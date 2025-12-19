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
"""'vmware datastores update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware import datastores
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DatastoresClient = datastores.DatastoresClient
DETAILED_HELP = {
    'DESCRIPTION': """
          Update a datastore.
        """,
    'EXAMPLES': """
          To update a datastore named `my-datastore` in location `us-west2-a` with a new description, run:

          $ {command} my-datastore --location=us-west2-a --project=my-project --description="new description"

          Or:

          $ {command} my-datastore --description="new description"

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a datastore."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddDatastoreArgToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--description',
        help="""\
        New description for the datastore.
        """,
    )

  def Run(self, args):
    datastore = args.CONCEPTS.datastore.Parse()
    client = DatastoresClient()
    is_async = args.async_
    operation = client.Update(datastore, description=args.description)
    if is_async:
      log.UpdatedResource(operation.name, kind='datastore', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for datastore [{}] to be updated'.format(
            datastore.RelativeName()
        ),
    )
    log.UpdatedResource(datastore.RelativeName(), kind='datastore')
    return resource

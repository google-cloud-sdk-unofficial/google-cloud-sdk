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
"""'vmware datastores delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.datastores import DatastoresClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """
          Delete a datastore.
        """,
    'EXAMPLES': """
          To delete a datastore named `my-datastore` in location `us-west2-a`, run:

          $ {command} my-datastore --location=us-west2-a --project=my-project

          Or:

          $ {command} my-datastore

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a datastore."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddDatastoreArgToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.add_argument(
        '--etag',
        help="""\
        Etag of the datastore.
        """,
    )

  def Run(self, args):
    datastore = args.CONCEPTS.datastore.Parse()
    client = DatastoresClient()
    is_async = args.async_
    operation = client.Delete(datastore, etag=args.etag)
    if is_async:
      log.DeletedResource(operation.name, kind='datastore', is_async=True)
      return operation

    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for datastore [{}] to be deleted'.format(
            datastore.RelativeName()
        ),
        has_result=False,
    )

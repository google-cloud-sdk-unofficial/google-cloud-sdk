# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Get the public certificate of an Azure Client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.azure import util as azure_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.core import log


_EXAMPLES = """
To get the public certificate of an Azure client named ``my-client'' in
location ``us-west1'', run:

$ {command} my-client --location=us-west1

To store the certificate in a file named ``client.crt'', run:

$ {command} my-client --location=us-west1 --output-file=client.crt
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetPublicCert(base.DescribeCommand):
  """Get the public certificate of an Azure client."""

  detailed_help = {"EXAMPLES": _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAzureClientResourceArg(parser,
                                            "to get the public certificate")
    flags.AddOutputFile(parser, "to store PEM")

  def Run(self, args):
    """Runs the get-public-cert command."""
    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAzureClientResourceArg(args).locationsId,
        self.ReleaseTrack()):
      client_ref = resource_args.ParseAzureClientResourceArg(args)
      api_client = azure_api_util.ClientsClient(track=self.ReleaseTrack())
      client = api_client.Get(client_ref)
      log.WriteToFileOrStdout(
          args.output_file if args.output_file else "-",
          client.certificate,
          overwrite=True,
          binary=False,
          private=True)

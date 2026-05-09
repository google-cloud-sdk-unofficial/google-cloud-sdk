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

"""Command to download the server connect configuration."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import transports
from googlecloudsdk.core.util import files


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class DownloadServerConnectConfig(base.Command):
  """Download the server connect configuration for a Network Monitoring Provider."""

  detailed_help = {
      'BRIEF': 'Download the server connect configuration.',
      'DESCRIPTION': (
          """\
          Downloads the server connect configuration for a given Network Monitoring Provider.
          The response is a zip file.
          """
      ),
      'EXAMPLES': (
          """\
          To download the server connect configuration for provider `my-provider`, run:

            $ {command} --network-monitoring-provider=my-provider --location=global --output-file=config.zip
          """
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--network-monitoring-provider',
        required=True,
        help='The ID of the Network Monitoring Provider.',
    )
    parser.add_argument(
        '--location',
        required=True,
        help=(
            'The location of the Network Monitoring Provider (example:'
            ' `global`).'
        ),
    )
    parser.add_argument(
        '--output-file',
        required=True,
        help='The path to save the downloaded server connect configuration.',
    )

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    location = args.location
    provider_id = args.network_monitoring_provider
    release_track = self.ReleaseTrack()
    if release_track == base.ReleaseTrack.ALPHA:
      api_version = 'v1alpha1'
    else:
      api_version = 'v1'

    parent = f'projects/{project}/locations/{location}/networkMonitoringProviders/{provider_id}'
    request_path = (
        f'{api_version}/{parent}/monitoringPoints:downloadServerConnectConfig'
    )

    base_uri = apis.GetEffectiveApiEndpoint('networkmanagement', api_version)
    uri = f'{base_uri}{request_path}'
    http = transports.GetApitoolsTransport(response_encoding=None)

    response, body = http.request(
        uri,
        method='GET',
        headers={},
    )

    if response.status != 200:
      raise exceptions.HttpException(
          f'API request failed with status {response.status}:'
          f' {body.decode("utf-8")}'
      )

    content_type = (
        response['content-type'] if 'content-type' in response else 'unknown'
    )

    try:
      with files.BinaryFileWriter(args.output_file) as f:
        f.write(body)
      log.status.Print(
          f'Downloaded {content_type} server connect configuration to'
          f' [{args.output_file}]'
      )
    except Exception as e:
      raise exceptions.BadFileException(
          f'Failed to write file [{args.output_file}]: {e}'
      )

    return None


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.DefaultUniverseOnly
class DownloadServerConnectConfigGa(DownloadServerConnectConfig):
  """Download the server connect configuration."""

  pass

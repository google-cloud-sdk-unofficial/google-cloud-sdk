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
"""'vmware datastores list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Any, Dict

from googlecloudsdk.api_lib.vmware import datastores
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DatastoresClient = datastores.DatastoresClient


def _GetServiceType(r: Dict[str, Any]) -> str:
  """Gets the service type from a datastore resource.

  Args:
    r: The datastore resource.

  Returns:
    A string representing the service type, or an empty string if not found.
  """
  if r.get('nfsDatastore'):
    if r['nfsDatastore'].get('googleFileService'):
      if r['nfsDatastore']['googleFileService'].get('netappVolume'):
        return 'NETAPP'
      if r['nfsDatastore']['googleFileService'].get('filestoreInstance'):
        return 'FILESTORE'
    if r['nfsDatastore'].get('thirdPartyFileService'):
      return 'THIRD_PARTY'
  return ''


def _GetVolume(r: Dict[str, Any]) -> str:
  """Gets the volume information from a datastore resource.

  Args:
    r: The datastore resource.

  Returns:
    A string representing the volume, or an empty string if not found.
  """
  if r.get('nfsDatastore'):
    nfs = r['nfsDatastore']
    if nfs.get('googleFileService'):
      gfs = nfs['googleFileService']
      if gfs.get('netappVolume'):
        return gfs['netappVolume'].split('/')[-1]
      if gfs.get('filestoreInstance'):
        return gfs['filestoreInstance'].split('/')[-1]
    if nfs.get('thirdPartyFileService'):
      tfs = nfs['thirdPartyFileService']
      file_share = tfs.get('fileShare', '')
      servers = tfs.get('servers', [])
      if servers:
        return ','.join(servers) + ':' + file_share
      return file_share
  return ''


TRANSFORMS = {'service_type': _GetServiceType, 'volume': _GetVolume}
DETAILED_HELP = {
    'DESCRIPTION': """
          List datastores.
        """,
    'EXAMPLES': """
          To list datastores in location `us-west2-a`, run:

          $ {command} --location=us-west2-a --project=my-project

          Or:

          $ {command}

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List datastores."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddLocationArgToParser(parser)
    parser.display_info.AddTransforms(TRANSFORMS)
    parser.display_info.AddFormat('table(name.segment(-1):label=NAME,'
                                  'name.segment(-5):label=PROJECT,'
                                  'name.segment(-3):label=LOCATION,'
                                  'createTime,state,'
                                  'service_type():label=SERVICE_TYPE,'
                                  'volume():label=VOLUME)')

  def Run(self, args):
    location = args.CONCEPTS.location.Parse()
    client = DatastoresClient()
    return client.List(location)

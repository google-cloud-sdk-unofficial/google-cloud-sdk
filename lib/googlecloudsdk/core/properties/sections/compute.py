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
"""Contains the properties for the 'compute' section."""

from googlecloudsdk.core.properties.completers import COMPLETERS
from googlecloudsdk.core.properties.types import _Section


class _SectionCompute(_Section):
  """Contains the properties for the 'compute' section."""

  def __init__(self):
    super(_SectionCompute, self).__init__('compute')
    self.zone = self._Add(
        'zone',
        help_text=(
            'Default zone to use when working with zonal Compute Engine'
            ' resources. When a `--zone` flag is required but not provided, the'
            ' command will fall back to this value, if set. To see valid'
            ' choices, run `gcloud compute zones list`.'
        ),
        completer=COMPLETERS['ZonesCompleter'],
    )
    self.region = self._Add(
        'region',
        help_text=(
            'Default region to use when working with regional Compute Engine'
            ' resources. When a `--region` flag is required but not provided,'
            ' the command will fall back to this value, if set. To see valid'
            ' choices, run `gcloud compute regions list`.'
        ),
        completer=COMPLETERS['RegionsCompleter'],
    )
    self.gce_metadata_read_timeout_sec = self._Add(
        'gce_metadata_read_timeout_sec',
        default=20,
        help_text='Timeout of requesting data from gce metadata endpoints.',
        hidden=True,
    )
    self.gce_metadata_check_timeout_sec = self._Add(
        'gce_metadata_check_timeout_sec',
        default=3,
        help_text='Timeout of checking if it is on gce environment.',
        hidden=True,
    )
    self.use_new_list_usable_subnets_api = self._AddBool(
        'use_new_list_usable_subnets_api',
        default=False,
        help_text=(
            'If True, use the new API for listing usable subnets which only '
            'returns subnets in the current project.'
        ),
    )
    self.image_family_scope = self._Add(
        'image_family_scope',
        help_text=(
            'Sets how images are selected with image families for '
            'disk and instance creation. By default, zonal image resources '
            'are used when using an image family in a public image project, '
            'and global image resources are used for all other projects. '
            'To override the default behavior, set this property to `zonal` '
            'or `global`. '
        ),
    )
    self.iap_tunnel_use_new_websocket = self._AddBool(
        'iap_tunnel_use_new_websocket',
        default=False,
        help_text='Bool that indicates if we should use new websocket.',
        hidden=True,
    )
    self.force_batch_request = self._AddBool(
        'force_batch_request',
        default=False,
        help_text='Bool that force all requests are sent as batch request',
        hidden=True,
    )
    self.disable_batch_request = self._AddBool(
        'disable_batch_request',
        default=False,
        help_text=(
            'If True, all requests are sent as individual requests instead '
            'of batch requests.'
        ),
        hidden=True,
    )
    self.allow_partial_error = self._AddBool(
        'allow_partial_error',
        default=True,
        help_text=(
            'Allow AggregatedList to return partial response when there are'
            ' partial server down'
        ),
        hidden=True,
    )

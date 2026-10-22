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
"""Contains the properties for the 'ssh' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionSsh(_Section):
  """Contains SSH-related properties."""

  def __init__(self):
    super(_SectionSsh, self).__init__('ssh')
    self.putty_force_connect = self._AddBool(
        'putty_force_connect',
        default=True,  # For backwards compatibility only.
        help_text=(
            'Whether or not `gcloud` should automatically accept new or '
            'changed host keys when executing plink/pscp commands on Windows. '
            'Defaults to True, but can be set to False to present these '
            'interactive prompts to the user for host key checking.'
        ),
    )
    self.verify_internal_ip = self._AddBool(
        'verify_internal_ip',
        default=True,
        help_text=(
            'Whether or not `gcloud` should perform an initial SSH connection'
            ' to verify an instance ID is correct when connecting via its'
            ' internal IP. Without this check, `gcloud` will simply connect to'
            ' the internal IP of the desired instance, which may be wrong if'
            ' the desired instance is in a different subnet but happens to'
            ' share the same internal IP as an instance in the current subnet.'
            ' Defaults to True.'
        ),
    )

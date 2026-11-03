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
"""Contains the properties for the 'access_context_manager' section."""

from googlecloudsdk.core.properties.exceptions import InvalidValueError
from googlecloudsdk.core.properties.types import _Section
from googlecloudsdk.core.properties.validators import AccessPolicyValidator


class _SectionAccessContextManager(_Section):
  """Contains the properties for the 'access_context_manager' section."""

  def OrganizationValidator(self, org):
    """Checks to see if the Organization string is valid."""
    if org is None:
      return
    if not org.isdigit():
      raise InvalidValueError(
          'The access_context_manager.organization property must be set '
          'to the organization ID number, not a string.'
      )

  def __init__(self):
    super(_SectionAccessContextManager, self).__init__(
        'access_context_manager', hidden=True
    )

    self.policy = self._Add(
        'policy',
        validator=AccessPolicyValidator,
        help_text=(
            'ID of the policy resource to operate on. Can be found '
            'by running the `access-context-manager policies list` '
            'command.'
        ),
    )
    self.organization = self._Add(
        'organization',
        validator=self.OrganizationValidator,
        help_text=(
            'Default organization cloud-bindings command group will operate on.'
        ),
    )

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
"""Cloud AutoProtectionBindings client."""

from typing import Any

from googlecloudsdk.api_lib.backupdr import util


class AutoProtectionBindingsClient(util.BackupDrClientBase):
  """Cloud AutoProtectionBindings client."""

  def __init__(self, api_version=util.DEFAULT_API_VERSION):
    """Initializes the instance.

    Args:
      api_version: The version of the API to use.
    """
    super(AutoProtectionBindingsClient, self).__init__(api_version=api_version)
    self.service = (
        self.client.projects_locations_autoProtectionPolicies_bindings
    )

  def InitiateDelete(self, binding_ref: Any):
    """Initiates deletion of an AutoProtectionBinding."""
    request = self.messages.BackupdrProjectsLocationsAutoProtectionPoliciesBindingsInitiateDeleteRequest(
        name=binding_ref.RelativeName(),
        initiateDeleteAutoProtectionPolicyBindingRequest=self.messages.InitiateDeleteAutoProtectionPolicyBindingRequest()
    )
    return self.service.InitiateDelete(request)

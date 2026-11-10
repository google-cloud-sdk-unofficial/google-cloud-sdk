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
"""API wrapper for `gcloud network-security security-profiles scm` commands."""

from googlecloudsdk.api_lib.network_security.security_profiles import sp_api
from googlecloudsdk.core import exceptions

SCM_PROFILE_TYPE = 'SCM'


class Client(sp_api.Client):
  """API client for SCM commands."""

  def CreateScmProfile(
      self,
      sp_id,
      parent,
      description=None,
      labels=None,
  ):
    """Calls the Create Security Profile API to create an SCM Profile.

    Args:
      sp_id: The ID of the Security Profile to create, e.g. "my-scm-sp".
      parent: The parent resource path, e.g.
        "organizations/123/locations/global".
      description: Optional user-specified description of the Security Profile,
        or None if not specified.
      labels: Optional LabelsValue message containing labels for the Security
        Profile, or None if not specified.

    Returns:
      The long-running Operation message returned by the Create API.
    """
    profile = self.messages.SecurityProfile(
        type=self._ParseSecurityProfileType(SCM_PROFILE_TYPE),
        description=description,
        labels=labels,
    )
    return self._security_profile_client.Create(
        self._create_request(
            parent=parent,
            securityProfile=profile,
            securityProfileId=sp_id,
        )
    )

  def ListScmProfiles(self, parent, limit=None, page_size=None):
    """Calls the ListSecurityProfiles API, filtering by type.

    Args:
      parent: The parent resource path, e.g.
        "organizations/123/locations/global".
      limit: Optional maximum number of profiles to return, or None for no
        limit.
      page_size: Optional number of profiles to fetch per API page, or None for
        the server default.

    Returns:
      A list of SecurityProfile messages of type SCM.
    """
    scm_profiles = [
        profile
        for profile in self.ListSecurityProfiles(
            parent, limit=None, page_size=page_size
        )
        if profile.type
        == self._ParseSecurityProfileType(SCM_PROFILE_TYPE)
    ]
    if limit is not None:
      return scm_profiles[:limit]
    return scm_profiles

  def GetSecurityProfile(self, name):
    """Calls the GetSecurityProfile API, filtering by type.

    Args:
      name: Fully qualified Security Profile resource name.

    Returns:
      The SecurityProfile message of type SCM.

    Raises:
      exceptions.Error: If the retrieved security profile is not of type SCM.
    """
    profile = super().GetSecurityProfile(name)
    if profile.type != self._ParseSecurityProfileType(SCM_PROFILE_TYPE):
      raise exceptions.Error(
          f'Security profile [{name}] is not an SCM profile.'
      )
    return profile

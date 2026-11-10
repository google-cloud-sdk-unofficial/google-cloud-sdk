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
"""Client library for Software Delivery Trust Authorities."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions

API_NAME = 'softwaredeliverytrust'
API_VERSION = 'v1alpha'


class AuthoritiesClient(object):
  """Client wrapper for Software Delivery Trust Authority API resources."""

  def __init__(self, client=None, messages=None):
    self.client = client or apis.GetClientInstance(API_NAME, API_VERSION)
    self.messages = messages or apis.GetMessagesModule(API_NAME, API_VERSION)
    self.service = self.client.projects_locations_authorities

  def Get(self, authority_ref):
    """Retrieves an Authority by resource reference."""
    req = self.messages.SoftwaredeliverytrustProjectsLocationsAuthoritiesGetRequest(
        name=authority_ref.RelativeName()
    )
    return self.service.Get(req)

  def Create(self, authority_ref, description=None, public_keys=None):
    """Creates a new Authority."""
    authority = self.messages.Authority(
        description=description,
        publicKeys=public_keys or [],
    )
    req = self.messages.SoftwaredeliverytrustProjectsLocationsAuthoritiesCreateRequest(
        parent=authority_ref.Parent().RelativeName(),
        authorityId=authority_ref.Name(),
        authority=authority,
    )
    return self.service.Create(req)

  def Update(
      self,
      authority_ref,
      description=None,
      public_keys=None,
      update_mask=None,
      etag=None,
  ):
    """Updates an existing Authority with field mask support."""
    authority = self.messages.Authority(etag=etag)
    mask_fields = []

    if description is not None:
      authority.description = description
      mask_fields.append('description')

    if public_keys is not None:
      authority.publicKeys = public_keys
      mask_fields.append('public_keys')

    final_mask = update_mask or ','.join(mask_fields)
    req = self.messages.SoftwaredeliverytrustProjectsLocationsAuthoritiesPatchRequest(
        name=authority_ref.RelativeName(),
        authority=authority,
        updateMask=final_mask,
    )
    return self.service.Patch(req)

  def Delete(self, authority_ref, etag=None):
    """Deletes an Authority."""
    req = self.messages.SoftwaredeliverytrustProjectsLocationsAuthoritiesDeleteRequest(
        name=authority_ref.RelativeName(),
        etag=etag,
    )
    return self.service.Delete(req)

  def List(self, parent_ref, page_size=100, limit=None):
    """Lists Authorities under a parent location."""
    req = self.messages.SoftwaredeliverytrustProjectsLocationsAuthoritiesListRequest(
        parent=parent_ref.RelativeName(),
    )
    return list_pager.YieldFromList(
        self.service,
        req,
        batch_size=page_size,
        limit=limit,
        field='authorities',
        batch_size_attribute='pageSize',
    )

  def AddKey(self, authority_ref, new_public_key):
    """Atomically adds a public key to an existing Authority via Read-Modify-Write."""
    current = self.Get(authority_ref)

    if new_public_key.keyId:
      for existing_key in current.publicKeys or []:
        if existing_key.keyId == new_public_key.keyId:
          raise exceptions.InvalidArgumentException(
              '--key-id',
              'A key with ID "{}" already exists in authority "{}".'.format(
                  new_public_key.keyId, authority_ref.Name()
              ),
          )

    updated_keys = list(current.publicKeys or []) + [new_public_key]
    return self.Update(
        authority_ref,
        public_keys=updated_keys,
        update_mask='public_keys',
        etag=current.etag,
    )

  def RemoveKey(self, authority_ref, key_id=None, fingerprint=None):
    """Atomically removes a public key from an existing Authority via Read-Modify-Write."""
    current = self.Get(authority_ref)

    matching_idx = None
    for idx, key in enumerate(current.publicKeys or []):
      if key_id and key.keyId == key_id:
        matching_idx = idx
        break
      if fingerprint and getattr(key, 'fingerprint', None) == fingerprint:
        matching_idx = idx
        break

    if matching_idx is None:
      identifier = key_id or fingerprint
      flag_name = '--key-id' if key_id else '--fingerprint'
      raise exceptions.InvalidArgumentException(
          flag_name,
          'No public key matching "{}" found in authority "{}".'.format(
              identifier, authority_ref.Name()
          ),
      )

    remaining_keys = list(current.publicKeys)
    remaining_keys.pop(matching_idx)
    return self.Update(
        authority_ref,
        public_keys=remaining_keys,
        update_mask='public_keys',
        etag=current.etag,
    )

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
"""Utility for updating Memorystore instances."""


def UpdateAuthMode(unused_instance_ref, args, patch_request):
  """Hook to fix auth mode in the memorystore instance update mask."""
  if patch_request.updateMask and args.IsSpecified('auth_mode'):
    # Replace 'authorizationMode' with 'auth_mode' in the update mask.
    # The framework generates 'authorizationMode' based on the api_field,
    # but the backend expects 'auth_mode'.
    # TODO(b/499106935): Add a test for this.
    mask_fields = patch_request.updateMask.split(',')
    if 'authorizationMode' in mask_fields:
      mask_fields = [
          f if f != 'authorizationMode' else 'auth_mode' for f in mask_fields
      ]
      patch_request.updateMask = ','.join(mask_fields)
  return patch_request

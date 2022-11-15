# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utility for updating Memorystore Redis clusters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def AddFieldToUpdateMask(field, patch_request):
  update_mask = patch_request.updateMask
  if update_mask:
    if update_mask.count(field) == 0:
      patch_request.updateMask = update_mask + ',' + field
  else:
    patch_request.updateMask = field
  return patch_request


def UpdateTotalMemorySizeGb(unused_instance_ref, args, patch_request):
  """Python hook to add size to the redis cluster update request."""
  if args.IsSpecified('total_memory_size_gb'):
    patch_request.cluster.totalMemorySizeGb = args.total_memory_size_gb
    patch_request = AddFieldToUpdateMask('total_memory_size_gb', patch_request)
  return patch_request

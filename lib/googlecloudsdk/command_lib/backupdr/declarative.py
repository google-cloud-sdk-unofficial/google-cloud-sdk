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
"""Functions for Backupdr gcloud declarative commands."""


def SetBasicViewByDefaultRequestHook(ref, args, request):
  """Add basic view as a default field to list request.

  Args:
    ref: A parsed resource reference; unused.
    args: The parsed args namespace from CLI; unused.
    request: List request for the API call.

  Returns:
    Modified request that includes the view field set to basic view.
  """
  del ref, args  # Unused.
  # Access the ViewValueValuesEnum from the request instance's own class.
  # This ensures compatibility across v1, v1beta, and v1alpha.
  if hasattr(request, 'ViewValueValuesEnum'):
    request.view = request.ViewValueValuesEnum.BACKUP_VIEW_BASIC

  return request

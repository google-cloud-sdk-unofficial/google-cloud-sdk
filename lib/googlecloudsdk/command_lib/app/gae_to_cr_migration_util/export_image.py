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

"""Utility functions for exporting an App Engine image to Artifact Registry."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.core import exceptions


def export_image(
    project: str,
    service: str,
    version: str,
    destination_repository: str,
    api_client: appengine_api_client.AppengineApiClient,
    export_service_account: str | None = None,
) -> appengine_api_client.ExportImageResult:
  """Exports the App Engine image to Artifact Registry.

  Args:
    project: The project ID.
    service: The service ID.
    version: The version ID.
    destination_repository: The destination Artifact Registry repository.
    api_client: The App Engine API client.
    export_service_account: The service account to use for exporting the image.

  Returns:
    An ExportImageResult object.

  Raises:
    exceptions.Error: If image export fails.
  """

  try:
    return api_client.ExportImageAndWait(
        app_id=project,
        service_id=service,
        version_id=version,
        destination_repository=destination_repository,
        export_service_account=export_service_account,
    )
  except exceptions.Error as e:
    raise exceptions.Error(f'Failed to export image: {e!r}') from e

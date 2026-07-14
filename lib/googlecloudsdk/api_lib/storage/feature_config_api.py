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
"""API client for Storage Feature Configurations."""

from collections.abc import Iterator

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.generated_clients.apis.storage.v2 import storage_v2_messages

API_NAME = 'storage'
API_VERSION = 'v2'
PAGE_SIZE = 100


class FeatureConfigApi:
  """API client for feature configurations.

  Attributes:
    client: The API client for interacting with the storage API.
    messages: The API messages for constructing requests and handling responses.
  """

  def __init__(self):
    self.client = apis.GetClientInstance(API_NAME, API_VERSION)
    self.messages = apis.GetMessagesModule(API_NAME, API_VERSION)
    self._service = self.client.projects_locations_featureConfigs

  def create_feature_config(
      self,
      parent: str,
      feature_config_id: str,
      description: str | None = None,
      auto_annotate_models: list[str] | None = None,
      include_locations: list[str] | None = None,
      exclude_locations: list[str] | None = None,
      include_bucket_id_regexes: list[str] | None = None,
      exclude_bucket_id_regexes: list[str] | None = None,
  ) -> 'storage_v2_messages.Operation':
    """Creates a feature configuration.

    Args:
      parent: The parent resource. Format:
        projects/{project}/locations/{location}
      feature_config_id: The user-specified ID of the feature config.
      description: The description of the feature configuration.
      auto_annotate_models: List of models to configure.
      include_locations: List of locations to include.
      exclude_locations: List of locations to exclude.
      include_bucket_id_regexes: List of bucket ID regexes to include.
      exclude_bucket_id_regexes: List of bucket ID regexes to exclude.

    Returns:
      Operation message.
    """
    feature_config = self.messages.FeatureConfig()
    if description is not None:
      feature_config.description = description

    if auto_annotate_models:
      models = [self.messages.Model(name=m) for m in auto_annotate_models if m]
      feature_config.autoAnnotateConfig = self.messages.AutoAnnotateConfig(
          models=models
      )

    # Build Filter
    has_filter = (
        include_locations
        or exclude_locations
        or include_bucket_id_regexes
        or exclude_bucket_id_regexes
    )
    if has_filter:
      feature_filter = self.messages.FeatureConfigFilter()
      if include_locations:
        feature_filter.includedCloudStorageLocations = (
            self.messages.StorageLocations(locations=include_locations)
        )
      if exclude_locations:
        feature_filter.excludedCloudStorageLocations = (
            self.messages.StorageLocations(locations=exclude_locations)
        )
      if include_bucket_id_regexes:
        feature_filter.includedCloudStorageBuckets = (
            self.messages.StorageBuckets(
                bucketIdRegexes=include_bucket_id_regexes
            )
        )
      if exclude_bucket_id_regexes:
        feature_filter.excludedCloudStorageBuckets = (
            self.messages.StorageBuckets(
                bucketIdRegexes=exclude_bucket_id_regexes
            )
        )
      feature_config.filter = feature_filter

    request = self.messages.StorageProjectsLocationsFeatureConfigsCreateRequest(
        parent=parent,
        featureConfigId=feature_config_id,
        featureConfig=feature_config,
    )
    return self._service.Create(request)

  def delete_feature_config(
      self,
      name: str,
  ) -> 'storage_v2_messages.Operation':
    """Deletes a feature configuration.

    Args:
      name: The resource name of the feature configuration. Format:
        projects/{project}/locations/{location}/featureConfigs/{config}

    Returns:
      Operation message.
    """
    request = self.messages.StorageProjectsLocationsFeatureConfigsDeleteRequest(
        name=name
    )
    return self._service.Delete(request)

  def get_feature_config(
      self,
      name: str,
  ) -> 'storage_v2_messages.FeatureConfig':
    """Gets details of a feature configuration.

    Args:
      name: The resource name of the feature configuration. Format:
        projects/{project}/locations/{location}/featureConfigs/{config}

    Returns:
      FeatureConfig message.
    """
    request = self.messages.StorageProjectsLocationsFeatureConfigsGetRequest(
        name=name
    )
    return self._service.Get(request)

  def list_feature_configs(
      self,
      parent: str,
      filter_expression: str | None = None,
      page_size: int | None = None,
  ) -> Iterator['storage_v2_messages.FeatureConfig']:
    """Lists feature configurations.

    Args:
      parent: The parent resource to list feature configs for. Format:
        projects/{project}/locations/{location}
      filter_expression: Filter expression to filter the results.
      page_size: The maximum number of items to return per page.

    Returns:
      Generator of FeatureConfig messages.
    """
    request = self.messages.StorageProjectsLocationsFeatureConfigsListRequest(
        parent=parent,
        filter=filter_expression,
    )
    return list_pager.YieldFromList(
        self._service,
        request,
        batch_size=page_size if page_size is not None else PAGE_SIZE,
        batch_size_attribute='pageSize',
        field='featureConfigs',
    )

  def _get_feature_config_update_mask(
      self,
      description: str | None = None,
      auto_annotate_models: list[str] | None = None,
      include_locations: list[str] | None = None,
      exclude_locations: list[str] | None = None,
      include_bucket_id_regexes: list[str] | None = None,
      exclude_bucket_id_regexes: list[str] | None = None,
  ):
    """Returns the update_mask list."""
    update_mask = []
    if description is not None:
      update_mask.append('description')
    if auto_annotate_models is not None:
      update_mask.append('autoAnnotateConfig')

    if include_locations is not None or exclude_locations is not None:
      update_mask.append('filter.includedCloudStorageLocations')
      update_mask.append('filter.excludedCloudStorageLocations')

    if (
        include_bucket_id_regexes is not None
        or exclude_bucket_id_regexes is not None
    ):
      update_mask.append('filter.includedCloudStorageBuckets')
      update_mask.append('filter.excludedCloudStorageBuckets')
    return update_mask

  def update_feature_config(
      self,
      name: str,
      description: str | None = None,
      auto_annotate_models: list[str] | None = None,
      include_locations: list[str] | None = None,
      exclude_locations: list[str] | None = None,
      include_bucket_id_regexes: list[str] | None = None,
      exclude_bucket_id_regexes: list[str] | None = None,
  ) -> 'storage_v2_messages.Operation':
    """Updates an existing feature configuration.

    Args:
      name: The resource name of the feature configuration. Format:
        projects/{project}/locations/{location}/featureConfigs/{config}
      description: The description of the feature configuration.
      auto_annotate_models: List of models to configure.
      include_locations: List of locations to include.
      exclude_locations: List of locations to exclude.
      include_bucket_id_regexes: List of bucket ID regexes to include.
      exclude_bucket_id_regexes: List of bucket ID regexes to exclude.

    Returns:
      Operation message.
    """
    update_mask = self._get_feature_config_update_mask(
        description=description,
        auto_annotate_models=auto_annotate_models,
        include_locations=include_locations,
        exclude_locations=exclude_locations,
        include_bucket_id_regexes=include_bucket_id_regexes,
        exclude_bucket_id_regexes=exclude_bucket_id_regexes,
    )

    if not update_mask:
      raise errors.CloudApiError(
          'Nothing to update for feature config: {}'.format(name)
      )

    # Construct FeatureConfig proto
    models = []
    if auto_annotate_models:
      models = [self.messages.Model(name=m) for m in auto_annotate_models if m]
    auto_annotate_config = (
        self.messages.AutoAnnotateConfig(models=models)
        if auto_annotate_models is not None
        else None
    )

    included_locations = None
    if include_locations:
      included_locations = self.messages.StorageLocations(
          locations=include_locations
      )
    excluded_locations = None
    if exclude_locations:
      excluded_locations = self.messages.StorageLocations(
          locations=exclude_locations
      )
    included_buckets = None
    if include_bucket_id_regexes:
      included_buckets = self.messages.StorageBuckets(
          bucketIdRegexes=include_bucket_id_regexes
      )
    excluded_buckets = None
    if exclude_bucket_id_regexes:
      excluded_buckets = self.messages.StorageBuckets(
          bucketIdRegexes=exclude_bucket_id_regexes
      )

    feature_filter = None
    if (
        include_locations is not None
        or exclude_locations is not None
        or include_bucket_id_regexes is not None
        or exclude_bucket_id_regexes is not None
    ):
      feature_filter = self.messages.FeatureConfigFilter(
          includedCloudStorageLocations=included_locations,
          excludedCloudStorageLocations=excluded_locations,
          includedCloudStorageBuckets=included_buckets,
          excludedCloudStorageBuckets=excluded_buckets,
      )

    feature_config = self.messages.FeatureConfig(
        description=description,
        autoAnnotateConfig=auto_annotate_config,
        filter=feature_filter,
    )

    request = self.messages.StorageProjectsLocationsFeatureConfigsPatchRequest(
        name=name,
        featureConfig=feature_config,
        updateMask=','.join(update_mask),
    )
    return self._service.Patch(request)

# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Cloud Marketplace Solutions client."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import io
import json
import re


from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions as apilib_exceptions
from googlecloudsdk.calliope.parser_errors import DetailedArgumentError
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer
import six

_REGIONAL_IAM_REGEX = re.compile(
    "PERMISSION_DENIED: Permission (.+) denied on 'projects/(.+?)/.*")
_DEFAULT_API_VERSION = 'v1alpha1'
_GLOBAL_REGION = 'global'

_PFORG = 'pforg'
_ALLOWED_PRODUCTS = [_PFORG]


def _ValidateProduct(product):
  """Validates product property. Returns custom error message if invalid."""
  if product in _ALLOWED_PRODUCTS:
    pass
  else:
    raise DetailedArgumentError('Allowed products are %s' %
                                json.dumps(_ALLOWED_PRODUCTS))


def _ParseError(error):
  """Returns a best-effort error message created from an API client error."""
  if isinstance(error, apitools_exceptions.HttpError):
    parsed_error = apilib_exceptions.HttpException(error,
                                                   error_format='{message}')
    error_message = parsed_error.message
  else:
    error_message = six.text_type(error)
  return error_message


def _CollapseRegionalIAMErrors(errors):
  """If all errors are PERMISSION_DENIEDs, use a single global error instead."""
  if errors:
    matches = [_REGIONAL_IAM_REGEX.match(e) for e in errors]
    if (all(match is not None for match in matches)
        and len(set(match.group(1) for match in matches)) == 1):
      errors = ['PERMISSION_DENIED: Permission %s denied on projects/%s' %
                (matches[0].group(1), matches[0].group(2))]
  return errors


# TODO(b/271949365) Add support for aggregated list
class MpsClient(object):
  """Cloud Marketplace Solutions client."""

  def __init__(self, api_version=_DEFAULT_API_VERSION):
    self._client = apis.GetClientInstance('marketplacesolutions', api_version)
    self._messages = apis.GetMessagesModule('marketplacesolutions', api_version)

    self.power_instances_service = (
        self._client.projects_locations_powerInstances
    )
    self.power_volumes_service = self._client.projects_locations_powerVolumes
    self.power_images_service = self._client.projects_locations_powerImages
    self.power_networks_service = self._client.projects_locations_powerNetworks
    self.power_sshkeys_service = self._client.projects_locations_powerSshKeys

    self.locations_service = self._client.projects_locations

  @property
  def client(self):
    return self._client

  @property
  def messages(self):
    return self._messages

  def AggregateYieldFromList(self,
                             service,
                             project_resource,
                             request_class,
                             resource,
                             global_params=None,
                             limit=None,
                             method='List',
                             predicate=None,
                             skip_global_region=True,
                             allow_partial_server_failure=True):
    """Make a series of List requests, across locations in a project.

    Args:
      service: apitools_base.BaseApiService, A service with a .List() method.
      project_resource: str, The resource name of the project.
      request_class: class, The class type of the List RPC request.
      resource: string, The name (in plural) of the resource type.
      global_params: protorpc.messages.Message, The global query parameters to
        provide when calling the given method.
      limit: int, The maximum number of records to yield. None if all available
        records should be yielded.
      method: str, The name of the method used to fetch resources.
      predicate: lambda, A function that returns true for items to be yielded.
      skip_global_region: bool, True if global region must be filtered out while
      iterating over regions
      allow_partial_server_failure: bool, if True don't fail and only print a
        warning if some requests fail as long as at least one succeeds. If
        False, fail the complete command if at least one request fails.

    Yields:
      protorpc.message.Message, The resources listed by the service.

    """
    response_count = 0
    errors = []
    for location in self.ListLocations(project_resource):
      # TODO(b/198857865): Global region will be used when it is ready.
      location_name = location.name.split('/')[-1]
      if skip_global_region and location_name == _GLOBAL_REGION:
        continue
      request = request_class(parent=location.name)
      try:
        response = getattr(service, method)(
            request, global_params=global_params)
        response_count += 1
      except Exception as e:  # pylint: disable=broad-except
        errors.append(_ParseError(e))
        continue
      items = getattr(response, resource)
      if predicate:
        items = list(filter(predicate, items))
      for item in items:
        yield item
        if limit is None:
          continue
        limit -= 1
        if not limit:
          break

    if errors:
      # If the command allows partial server errors, instead of raising an
      # exception to show something went wrong, we show a warning message that
      # contains the error messages instead.
      buf = io.StringIO()
      fmt = ('list[title="Some requests did not succeed.",'
             'always-display-title]')
      if allow_partial_server_failure and response_count > 0:
        resource_printer.Print(sorted(set(errors)), fmt, out=buf)
        log.warning(buf.getvalue())
      else:
        # If all requests failed, clean them up if they're duplicated IAM errors
        collapsed_errors = _CollapseRegionalIAMErrors(errors)
        resource_printer.Print(sorted(set(collapsed_errors)), fmt, out=buf)
        raise exceptions.Error(buf.getvalue())

  def ListLocations(self,
                    project_resource,
                    limit=None,
                    page_size=None):
    """Make a List Locations request."""
    request = self.messages.MarketplacesolutionsProjectsLocationsListRequest(
        name='projects/' + project_resource)
    return list_pager.YieldFromList(
        self.locations_service,
        request,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='locations')

  def AggregateListInstances(self, project_resource, product, limit=None):
    """Make a series of List Instance requests."""
    _ValidateProduct(product)
    try:
      if product == _PFORG:
        power_resource = 'powerInstances'
        return self.AggregateYieldFromList(
            self.power_instances_service,
            project_resource,
            self.messages.MarketplacesolutionsProjectsLocationsPowerInstancesListRequest,
            power_resource,
            limit=limit,
        )
    except exceptions.Error as e:
      return e

  def GetInstance(self, product, resource):
    """Make a Get Instance request. Return details of specified instance."""
    _ValidateProduct(product)
    resource = resource.RelativeName()
    try:
      if product == _PFORG:
        power_request = self.messages.MarketplacesolutionsProjectsLocationsPowerInstancesGetRequest(
            name=resource
        )
        return self.power_instances_service.Get(power_request)
    except exceptions.Error as e:
      return e

  def ListInstances(self, product, location_resource):
    """Make a List Instances request. Return list of instances."""
    _ValidateProduct(product)
    location = location_resource.RelativeName()
    try:
      if product == _PFORG:
        power_request = self.messages.MarketplacesolutionsProjectsLocationsPowerInstancesListRequest(
            parent=location
        )
        return self.power_instances_service.List(power_request).powerInstances
    except exceptions.Error as e:
      return e

  def AggregateListVolumes(self, project_resource, product, limit=None):
    """Make a series of List Volume requests."""
    _ValidateProduct(product)
    try:
      if product == _PFORG:
        power_resource = 'powerVolumes'
        return self.AggregateYieldFromList(
            self.power_volumes_service,
            project_resource,
            self.messages.MarketplacesolutionsProjectsLocationsPowerVolumesListRequest,
            power_resource,
            limit=limit,
        )
    except exceptions.Error as e:
      return e

  def GetVolume(self, product, resource):
    """Make a Get Volume request. Return details of specified volume."""
    _ValidateProduct(product)
    resource = resource.RelativeName()
    try:
      if product == _PFORG:
        power_request = self.messages.MarketplacesolutionsProjectsLocationsPowerVolumesGetRequest(
            name=resource
        )
        return self.power_volumes_service.Get(power_request)
    except exceptions.Error as e:
      return e

  def ListVolumes(self, product, location_resource):
    """Make a List Volumes request. Return list of volumes."""
    _ValidateProduct(product)
    location = location_resource.RelativeName()
    try:
      if product == _PFORG:
        power_request = self.messages.MarketplacesolutionsProjectsLocationsPowerVolumesListRequest(
            parent=location
        )
        return self.power_volumes_service.List(power_request).powerVolumes
    except exceptions.Error as e:
      return e

  def AggregateListImages(self, project_resource, product, limit=None):
    """Make a series of List Image requests."""
    _ValidateProduct(product)
    try:
      if product == _PFORG:
        power_resource = 'powerImages'
        return self.AggregateYieldFromList(
            self.power_images_service,
            project_resource,
            self.messages.MarketplacesolutionsProjectsLocationsPowerImagesListRequest,
            power_resource,
            limit=limit,
        )
    except exceptions.Error as e:
      return e

  def GetImage(self, product, resource):
    """Make a Get Image request. Return details of specified image."""
    _ValidateProduct(product)
    resource = resource.RelativeName()
    try:
      if product == _PFORG:
        power_request = self.messages.MarketplacesolutionsProjectsLocationsPowerImagesGetRequest(
            name=resource
        )
        return self.power_images_service.Get(power_request)
    except exceptions.Error as e:
      return e

  def ListImages(self, product, location_resource):
    """Make a List Images request. Return list of images."""
    _ValidateProduct(product)
    location = location_resource.RelativeName()
    try:
      if product == _PFORG:
        power_request = self.messages.MarketplacesolutionsProjectsLocationsPowerImagesListRequest(
            parent=location
        )
        return self.power_images_service.List(power_request).powerImages
    except exceptions.Error as e:
      return e

  def AggregateListNetworks(self, project_resource, product, limit=None):
    """Make a series of List Networks requests."""
    _ValidateProduct(product)
    try:
      if product == _PFORG:
        power_resource = 'powerNetworks'
        return self.AggregateYieldFromList(
            self.power_networks_service,
            project_resource,
            self.messages.MarketplacesolutionsProjectsLocationsPowerNetworksListRequest,
            power_resource,
            limit=limit,
        )
    except exceptions.Error as e:
      return e

  def GetNetwork(self, product, resource):
    """Make a Get Network request. Return details of specified network."""
    _ValidateProduct(product)
    resource = resource.RelativeName()
    try:
      if product == _PFORG:
        power_request = self.messages.MarketplacesolutionsProjectsLocationsPowerNetworksGetRequest(
            name=resource
        )
        return self.power_networks_service.Get(power_request)
    except exceptions.Error as e:
      return e

  def ListNetworks(self, product, location_resource):
    """Make a List Networks request. Return list of networks."""
    _ValidateProduct(product)
    location = location_resource.RelativeName()
    try:
      if product == _PFORG:
        power_request = self.messages.MarketplacesolutionsProjectsLocationsPowerNetworksListRequest(
            parent=location
        )
        return self.power_networks_service.List(power_request).powerNetworks
    except exceptions.Error as e:
      return e

  def AggregateListSSHKeys(self, project_resource, product, limit=None):
    """Make a series of List SSH keys requests."""
    _ValidateProduct(product)
    try:
      if product == _PFORG:
        power_resource = 'powerSshKeys'
        return self.AggregateYieldFromList(
            self.power_sshkeys_service,
            project_resource,
            self.messages.MarketplacesolutionsProjectsLocationsPowerSshKeysListRequest,
            power_resource,
            limit=limit,
        )
    except exceptions.Error as e:
      return e

  def GetSSHKey(self, product, resource):
    """Make a Get SSH Key request. Return details of specified SSH key."""
    _ValidateProduct(product)
    try:
      resource = resource.RelativeName()
      if product == _PFORG:
        power_request = self.messages.MarketplacesolutionsProjectsLocationsPowerSshKeysGetRequest(
            name=resource
        )
        return self.power_sshkeys_service.Get(power_request)
    except exceptions.Error as e:
      return e

  def ListSSHKeys(self, product, location_resource):
    """Make a List SSH Keys request. Return list of SSH keys."""
    _ValidateProduct(product)
    location = location_resource.RelativeName()
    try:
      if product == _PFORG:
        power_request = self.messages.MarketplacesolutionsProjectsLocationsPowerSshKeysListRequest(
            parent=location
        )
        return self.power_sshkeys_service.List(power_request).powerSshKeys
    except exceptions.Error as e:
      return e

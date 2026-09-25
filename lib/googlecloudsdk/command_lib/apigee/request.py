# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Generalized Apigee Management API request handler.

The Apigee Management APIs were designed before One Platform, and include some
design decisions incompatible with apitools (see b/151099218). So the gcloud
apigee surface must make its own HTTPS requests instead of relying on an
apitools-generated client.
"""


import collections
import json
import os
from typing import Any, Optional

from googlecloudsdk.command_lib.apigee import errors
from googlecloudsdk.command_lib.apigee import resource_args
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.credentials import requests
from googlecloudsdk.core.util import files
from six.moves import urllib


APIGEE_GLOBAL_HOST = "apigee.googleapis.com"
APIGEE_LEP_HOST = "%s-apigee.googleapis.com"
APIGEE_MREP_HOST = "apigee.%s.rep.googleapis.com"
ERROR_FIELD = "error"
MESSAGE_FIELD = "message"
SUPPORTED_MREP_REGIONS = ["us", "eu", "in", "sa", "ch"]


def _ResourceIdentifier(identifiers, entity_path):
  """Returns an OrderedDict uniquely identifying the resource to be accessed.

  Args:
    identifiers: a collection that maps entity type names to identifiers.
    entity_path: a list of entity type names from least to most specific.

  Raises:
    MissingIdentifierError: an entry in entity_path is missing from
      `identifiers`.
  """
  resource_identifier = collections.OrderedDict()

  for entity_name in entity_path:
    entity = resource_args.ENTITIES[entity_name]
    id_key = entity.plural + "Id"
    if id_key not in identifiers or identifiers[id_key] is None:
      raise errors.MissingIdentifierError(entity.singular)
    resource_identifier[entity] = identifiers[id_key]
  return resource_identifier


def _Communicate(url, method, body, headers):
  """Returns HTTP status, reason, and response body for a given HTTP request."""
  response = requests.GetSession().request(
      method, url, data=body, headers=headers, stream=True)
  status = response.status_code
  reason = response.reason
  data = response.content
  return status, reason, data


def _DecodeResponse(response):
  """Returns decoded string.

  Args:
    response: the raw string or bytes of JSON data

  Raises:
    ValueError: failure to load/decode JSON data
  """
  # In older versions of Python 3, the built-in JSON library will only
  # accept strings, not bytes.
  if not isinstance(response, str) and hasattr(response, "decode"):
    response = response.decode()
  return response


def _GetResourceType(entity_collection, entity_path):
  """Gets resource type from the inputed data."""
  return entity_collection or entity_path[-1]


def _BuildErrorIdentifier(resource_identifier):
  """Builds error identifier from inputed data."""
  return collections.OrderedDict([
      (key.singular, value) for key, value in resource_identifier.items()
  ])


def _ExtractErrorMessage(response):
  """Extracts error message from response, returns None if message not found."""
  json_response = json.loads(response)
  if ERROR_FIELD in json_response and isinstance(
      json_response[ERROR_FIELD],
      dict) and MESSAGE_FIELD in json_response[ERROR_FIELD]:
    return json_response[ERROR_FIELD][MESSAGE_FIELD]
  return None


def _CachedDataWithName(name: str) -> Optional[dict[str, Any]]:
  """Returns the contents of a named cache file.

  Cache files are saved as hidden YAML files in the gcloud config directory.

  Args:
    name: The name of the cache file.

  Returns:
    The decoded contents of the file, or an empty dictionary if the file could
    not be read for whatever reason.
  """
  config_dir = config.Paths().global_config_dir
  cache_path = os.path.join(config_dir, ".apigee-cached-" + name)
  if not os.path.isfile(cache_path):
    return {}
  try:
    return yaml.load_path(cache_path)
  except yaml.YAMLParseError:
    # Another gcloud command might be in the process of writing to the file.
    # Handle as a cache miss.
    return {}


def _SaveCachedDataWithName(data: dict[str, Any], name: str) -> None:
  """Saves `data` to a named cache file.

  Cache files are saved as hidden YAML files in the gcloud config directory.

  Args:
    data: The data to cache.
    name: The name of the cache file.
  """
  config_dir = config.Paths().global_config_dir
  cache_path = os.path.join(config_dir, ".apigee-cached-" + name)
  files.WriteFileContents(cache_path, yaml.dump(data))


def _DeleteCachedDataWithName(name: str) -> None:
  """Deletes a named cache file."""
  config_dir = config.Paths().global_config_dir
  cache_path = os.path.join(config_dir, ".apigee-cached-" + name)
  if os.path.isfile(cache_path):
    try:
      os.remove(cache_path)
    except OSError:
      return


def _GetProjectMappingFromApi(organization: Optional[str]) -> dict[str, Any]:
  """Returns the project mapping for `organization` from the global endpoint."""
  try:
    return ResponseToApiRequest(
        {"organizationsId": organization},
        ["organization"],
        method=":getProjectMapping",
        method_override="GET",
        location="global",
    )
  except errors.RequestError as error:
    # Rewrite error message to better describe what was attempted.
    raise error.RewrittenError("project mapping", "get")


def _ListOrganizationsGlobal() -> dict[str, Any]:
  """Returns a list of Apigee organizations on the global endpoint."""
  try:
    return ResponseToApiRequest(
        identifiers=None,
        entity_path=[],
        entity_collection="organization",
        location="global",
    )
  except errors.RequestError as error:
    # Rewrite error message to better describe what was attempted.
    raise error.RewrittenError("organization", "list")


def GetProjectMapping(
    project: Optional[str], user_provided_org: Optional[str] = None
) -> Optional[dict[str, Any]]:
  """Returns the project mapping for the given GCP project.

  Args:
    project: The GCP project name.
    user_provided_org: The organization ID provided by the user, if any.

  Returns:
    The project mapping for the given GCP project.
  """

  project_mappings = _CachedDataWithName("project-mapping-v2") or {}

  if user_provided_org:
    mapping = project_mappings.get(user_provided_org, None)
    if mapping:
      return mapping
    else:
      try:
        project_mapping = _GetProjectMappingFromApi(user_provided_org)
        if "organization" not in project_mapping:
          raise errors.UnauthorizedRequestError(
              message=(
                  'Permission denied on resource "organizations/%s" (or it may'
                  " not exist)"
              )
              % user_provided_org
          )

        project_mappings[project] = project_mapping
        _SaveCachedDataWithName(project_mappings, "project-mapping-v2")
        return project_mapping
      except (
          errors.EntityNotFoundError,
          errors.UnauthorizedRequestError,
      ) as exc:
        raise errors.UnauthorizedRequestError(
            message=(
                'Permission denied on resource "organizations/%s" (or it may'
                " not exist)"
            )
            % user_provided_org
        ) from exc
      except errors.RequestError as e:
        raise e

  if project not in project_mappings:
    try:
      project_mapping = _GetProjectMappingFromApi(project)
      if "organization" not in project_mapping:
        return None

      if project_mapping.get("projectId", None) != project:
        return None

      project_mappings[project] = project_mapping
      _SaveCachedDataWithName(project_mappings, "project-mapping-v2")
    except (errors.EntityNotFoundError, errors.UnauthorizedRequestError):
      return None
    except errors.RequestError as e:
      raise e

  return project_mappings[project]


def FindMappingForProject(project: Optional[str]) -> Optional[dict[str, Any]]:
  """Returns the Apigee organization for the given GCP project."""
  project_mapping = _CachedDataWithName("project-mapping-v2") or {}

  if project in project_mapping:
    return project_mapping[project]

  # Listing organizations is an expensive operation for users with a lot of GCP
  # projects. Since the GCP project -> Apigee organization mapping is immutable
  # once created, cache known mappings to avoid the extra API call.
  overrides = properties.VALUES.api_endpoint_overrides.apigee.Get()
  if overrides:
    list_orgs = ResponseToApiRequest({}, [], "organization")
  else:
    list_orgs = _ListOrganizationsGlobal()

  for organization in list_orgs["organizations"]:
    for matching_project in organization["projectIds"]:
      project_mapping[matching_project] = {}
      project_mapping[matching_project] = organization
  _SaveCachedDataWithName(project_mapping, "project-mapping-v2")
  _DeleteCachedDataWithName("project-mapping")

  if project not in project_mapping:
    return None

  return project_mapping[project]


def GetOrganizationLocation(organization: Optional[str]) -> Optional[str]:
  """Returns the location of the Apigee organization."""
  project = properties.VALUES.core.project.Get()
  mapping = GetProjectMapping(project, organization)
  if mapping:
    return mapping.get("location", None)

  # Project mapping is not available, assume projectId is not same as
  # organization.
  mapping = FindMappingForProject(project)
  if mapping:
    return mapping.get("location", None)

  raise errors.LocationResolutionError()


def _GetApigeeHostByOrganization(organization: Optional[str]) -> str:
  """Returns the Apigee host based on the organization."""
  location = GetOrganizationLocation(organization)
  return _GetApigeeHostByLocation(location)


def _GetApigeeHostByLocation(location: Optional[str] = None) -> str:
  """Returns the Apigee host based on the location."""
  if not location or location == "global":
    return APIGEE_GLOBAL_HOST

  if location in SUPPORTED_MREP_REGIONS:
    return APIGEE_MREP_HOST % location

  return APIGEE_LEP_HOST % location


def ResponseToApiRequest(identifiers,
                         entity_path,
                         entity_collection=None,
                         method="GET",
                         query_params=None,
                         accept_mimetype=None,
                         body=None,
                         body_mimetype="application/json",
                         method_override=None,
                         location=None):
  """Makes a request to the Apigee API and returns the response.

  Args:
    identifiers: a collection that maps entity type names to identifiers.
    entity_path: a list of entity type names from least to most specific.
    entity_collection: if provided, the final entity type; the request will not
      be specific as to which entity of that type is being referenced.
    method: an HTTP method string specifying what to do with the accessed
      entity. If the method begins with a colon, it will be interpreted as a
      Cloud custom method (https://cloud.google.com/apis/design/custom_methods)
      and appended to the request URL with the POST HTTP method.
    query_params: any extra query parameters to be sent in the request.
    accept_mimetype: the mimetype to expect in the response body. If not
      provided, the response will be parsed as JSON.
    body: data to send in the request body.
    body_mimetype: the mimetype of the body data, if not JSON.
    method_override: the HTTP method to use for the request, when method starts
      with a colon.
    location: the location of the apigee organization.

  Returns:
    an object containing the API's response. If accept_mimetype was set, this
      will be raw bytes. Otherwise, it will be a parsed JSON object.

  Raises:
    MissingIdentifierError: an entry in entity_path is missing from
      `identifiers`.
    RequestError: if the request itself fails.
  """
  headers = {}
  if body:
    headers["Content-Type"] = body_mimetype
  if accept_mimetype:
    headers["Accept"] = accept_mimetype

  resource_identifier = _ResourceIdentifier(identifiers, entity_path)
  url_path_elements = ["v1"]
  for key, value in resource_identifier.items():
    url_path_elements += [key.plural, urllib.parse.quote(value)]
  if entity_collection:
    collection_name = resource_args.ENTITIES[entity_collection].plural
    url_path_elements.append(urllib.parse.quote(collection_name))

  query_string = urllib.parse.urlencode(query_params) if query_params else ""

  endpoint_override = properties.VALUES.api_endpoint_overrides.apigee.Get()
  if location:
    scheme = "https"
    # Construct the host based on the location.
    host = _GetApigeeHostByLocation(location)
  elif endpoint_override:
    endpoint = urllib.parse.urlparse(endpoint_override)
    scheme = endpoint.scheme
    host = endpoint.netloc
  else:
    scheme = "https"
    # Construct the host based on the organization location.
    organization = identifiers.get("organizationsId", None)
    host = _GetApigeeHostByOrganization(organization)

  url_path = "/".join(url_path_elements)
  if method and method[0] == ":":
    url_path += method
    method = "POST"
    if method_override:
      method = method_override
  url = urllib.parse.urlunparse((scheme, host, url_path, "", query_string, ""))

  status, reason, response = _Communicate(url, method, body, headers)

  if status >= 400:
    resource_type = _GetResourceType(entity_collection, entity_path)
    if status == 404:
      exception_class = errors.EntityNotFoundError
    elif status in (401, 403):
      exception_class = errors.UnauthorizedRequestError
    else:
      exception_class = errors.RequestError
    error_identifier = _BuildErrorIdentifier(resource_identifier)

    try:
      user_help = _ExtractErrorMessage(_DecodeResponse(response))
    except ValueError:
      user_help = None

    raise exception_class(resource_type, error_identifier, method,
                          reason, response, user_help=user_help)

  if accept_mimetype is None:
    try:
      response = _DecodeResponse(response)
      response = json.loads(response)
    except ValueError as error:
      resource_type = _GetResourceType(entity_collection, entity_path)
      error_identifier = _BuildErrorIdentifier(resource_identifier)
      raise errors.ResponseNotJSONError(error, resource_type, error_identifier,
                                        response)

  return response

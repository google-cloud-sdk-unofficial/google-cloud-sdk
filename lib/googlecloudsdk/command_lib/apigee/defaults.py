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
"""Default values and fallbacks for missing surface arguments."""


import collections

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.apigee import errors
from googlecloudsdk.command_lib.apigee import request
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml


class Fallthrough(deps.Fallthrough):
  """Base class for Apigee resource argument fallthroughs."""
  _handled_fields = []

  def __init__(self, hint, active=False, plural=False):
    super(Fallthrough, self).__init__(None, hint, active, plural)

  def __contains__(self, field):
    """Returns whether `field` is handled by this fallthrough class."""
    return field in self._handled_fields

  def _Call(self, parsed_args):
    raise NotImplementedError(
        "Subclasses of googlecloudsdk.commnand_lib.apigee.Fallthrough must "
        "actually provide a fallthrough."
    )


def OrganizationFromGCPProject():
  """Returns the organization associated with the active GCP project."""
  project = properties.VALUES.core.project.Get()
  if project is None:
    log.warning("Neither Apigee organization nor GCP project is known.")
    return None

  # Use the cached project_mapping_v2 if available. This should handle all the
  # cases where the project name is same as the organization name when cache
  # miss happens.
  project_mapping = request.GetProjectMapping(project)
  if project_mapping:
    return project_mapping["organization"]

  # Otherwise, list all organizations and update the project_mapping cache for
  # all the projects in the response.
  mapping = request.FindMappingForProject(project)
  if mapping:
    return mapping["organization"]

  log.warning("No Apigee organization is known for GCP project %s.", project)
  log.warning(
      "Please provide the argument [--organization] on the command "
      "line, or set the property [api_endpoint_overrides/apigee]."
  )
  return None


class GCPProductOrganizationFallthrough(Fallthrough):
  """Falls through to the organization for the active GCP project."""

  _handled_fields = ["organization"]

  def __init__(self):
    super(GCPProductOrganizationFallthrough, self).__init__(
        "set the property [project] or provide the argument [--project] on the "
        "command line, using a Cloud Platform project with an associated "
        "Apigee organization"
    )

  def _Call(self, parsed_args):
    return OrganizationFromGCPProject()


class StaticFallthrough(Fallthrough):
  """Falls through to a hardcoded value."""

  def __init__(self, argument, value):
    super(StaticFallthrough, self).__init__(
        "leave the argument unspecified for it to be chosen automatically")
    self._handled_fields = [argument]
    self.value = value

  def _Call(self, parsed_args):
    return self.value


def FallBackToDeployedProxyRevision(args):
  """If `args` provides no revision, adds the deployed revision, if unambiguous.

  Args:
    args: a dictionary of resource identifiers which identifies an API proxy and
      an environment, to which the deployed revision should be added.

  Raises:
    EntityNotFoundError: no deployment that matches `args` exists.
    AmbiguousRequestError: more than one deployment matches `args`.
  """
  deployments = apigee.DeploymentsClient.List(args)

  if not deployments:
    error_identifier = collections.OrderedDict([
        ("organization", args["organizationsId"]),
        ("environment", args["environmentsId"]), ("api", args["apisId"])
    ])
    raise errors.EntityNotFoundError("deployment", error_identifier, "undeploy")

  if len(deployments) > 1:
    message = "Found more than one deployment that matches this request.\n"
    raise errors.AmbiguousRequestError(message + yaml.dump(deployments))

  deployed_revision = deployments[0]["revision"]
  log.status.Print("Using deployed revision `%s`" % deployed_revision)
  args["revisionsId"] = deployed_revision

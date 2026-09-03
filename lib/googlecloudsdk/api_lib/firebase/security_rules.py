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
"""API client helper for Firebase Security Rules management."""

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.firebase import exceptions as firebase_exceptions
from googlecloudsdk.api_lib.firebase import util as firebase_util

_RULESET_UPDATE_MASK = 'ruleset_name'


def _FormatProjectName(project_id):
  """Formats project ID into full resource name."""
  if project_id.startswith('projects/'):
    return project_id
  return 'projects/{}'.format(project_id)


def _FormatReleaseName(project_id, release_name):
  """Formats release name into full resource name."""
  if release_name.startswith('projects/'):
    return release_name
  return 'projects/{}/releases/{}'.format(project_id, release_name)


def _FormatRulesetName(project_id, ruleset_name):
  """Formats ruleset name into full resource name."""
  if ruleset_name.startswith('projects/'):
    return ruleset_name
  return 'projects/{}/rulesets/{}'.format(project_id, ruleset_name)


class SecurityRulesClient:
  """Client for Firebase Security Rules API."""

  def __init__(self, client=None, messages=None):
    self.client = client or firebase_util.GetRulesClientInstance()
    self.messages = messages or firebase_util.GetRulesMessagesModule()

  def ListReleases(self, project_id, page_size=None, limit=None):
    """Lists security rules releases for a project.

    Args:
      project_id: str, Google Cloud project ID or full resource name.
      page_size: int or None, number of items to request per page.
      limit: int or None, maximum number of items to return.

    Returns:
      A generator yielding Release message resources.
    """
    parent = _FormatProjectName(project_id)
    request = self.messages.FirebaserulesProjectsReleasesListRequest(
        name=parent
    )
    try:
      return list_pager.YieldFromList(
          service=self.client.projects_releases,
          request=request,
          limit=limit,
          batch_size=page_size,
          field='releases',
          batch_size_attribute='pageSize',
      )
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)

  def ListRulesets(self, project_id, page_size=None, limit=None):
    """Lists security rulesets for a project.

    Args:
      project_id: str, Google Cloud project ID or full resource name.
      page_size: int or None, number of items to request per page.
      limit: int or None, maximum number of items to return.

    Returns:
      A generator yielding Ruleset message resources.
    """
    parent = _FormatProjectName(project_id)
    request = self.messages.FirebaserulesProjectsRulesetsListRequest(
        name=parent
    )
    try:
      return list_pager.YieldFromList(
          service=self.client.projects_rulesets,
          request=request,
          limit=limit,
          batch_size=page_size,
          field='rulesets',
          batch_size_attribute='pageSize',
      )
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)

  def GetRelease(self, project_id, release_name):
    """Gets a specific release by name.

    Args:
      project_id: str, Google Cloud project ID or full resource name.
      release_name: str, short name or full resource name of the release.

    Returns:
      The Release message resource.
    """
    name = _FormatReleaseName(project_id, release_name)
    request = self.messages.FirebaserulesProjectsReleasesGetRequest(
        name=name
    )
    try:
      return self.client.projects_releases.Get(request)
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)

  def GetRuleset(self, project_id, ruleset_name):
    """Gets a specific ruleset by name or ID.

    Args:
      project_id: str, Google Cloud project ID or full resource name.
      ruleset_name: str, ID or full resource name of the ruleset.

    Returns:
      The Ruleset message resource.
    """
    name = _FormatRulesetName(project_id, ruleset_name)
    request = self.messages.FirebaserulesProjectsRulesetsGetRequest(
        name=name
    )
    try:
      return self.client.projects_rulesets.Get(request)
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)

  def CreateRuleset(self, project_id, files_content_map, attachment_point=None):
    """Creates a new security ruleset from a map of filename to content.

    Args:
      project_id: str, Google Cloud project ID or full resource name.
      files_content_map: dict[str, str], mapping of file names to their text
        content for the ruleset source.
      attachment_point: str or None, optional attachment point for the
        ruleset.

    Returns:
      The created Ruleset message resource.
    """
    parent = _FormatProjectName(project_id)
    files = []
    for filename, content in files_content_map.items():
      files.append(
          self.messages.File(
              name=filename,
              content=content,
          )
      )
    source = self.messages.Source(files=files)
    ruleset = self.messages.Ruleset(
        name=parent,
        source=source,
        attachmentPoint=attachment_point,
    )
    try:
      return self.client.projects_rulesets.Create(ruleset)
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)

  def ReleaseRules(self, project_id, release_name, ruleset_name=None,
                   source_files=None):
    """Releases rules by creating/updating a Release to point to a Ruleset.

    Args:
      project_id: str, Google Cloud project ID or full resource name.
      release_name: str, short name or full resource name of the release.
      ruleset_name: str or None, existing ruleset name or ID to release.
      source_files: dict[str, str] or None, mapping of filename to rules
        file content to create a new ruleset from before releasing. Exactly
        one of ruleset_name or source_files must be provided.

    Returns:
      The created or updated Release message resource.

    Raises:
      firebase_exceptions.FirebaseError: If neither ruleset_name nor source_files
        is provided.
    """
    full_release_name = _FormatReleaseName(project_id, release_name)

    if source_files:
      ruleset = self.CreateRuleset(project_id, source_files)
      ruleset_name = ruleset.name

    if not ruleset_name:
      raise firebase_exceptions.FirebaseError(
          'Must provide either ruleset_name or source_files.'
      )

    full_ruleset_name = _FormatRulesetName(project_id, ruleset_name)

    exists = False
    try:
      _ = self.client.projects_releases.Get(
          self.messages.FirebaserulesProjectsReleasesGetRequest(
              name=full_release_name
          )
      )
      exists = True
    except apitools_exceptions.HttpNotFoundError:
      exists = False
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)

    try:
      if exists:
        patch_req = self.messages.FirebaserulesProjectsReleasesPatchRequest(
            name=full_release_name,
            updateReleaseRequest=self.messages.UpdateReleaseRequest(
                release=self.messages.Release(
                    name=full_release_name,
                    rulesetName=full_ruleset_name,
                ),
                updateMask=_RULESET_UPDATE_MASK,
            ),
        )
        return self.client.projects_releases.Patch(patch_req)
      else:
        create_req = self.messages.Release(
            name=full_release_name,
            rulesetName=full_ruleset_name,
        )
        return self.client.projects_releases.Create(create_req)
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)

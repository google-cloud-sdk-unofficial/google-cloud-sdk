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
"""The container scope that owns a VM extension policy."""

from typing import Optional
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _Qualify(collection: str, resource_id: str) -> str:
  """Returns 'collection/resource_id', unless it is already qualified."""
  prefix = collection + '/'
  return resource_id if resource_id.startswith(prefix) else prefix + resource_id


class Scope(object):
  """The container (project, folder, or organization) that owns a policy.

  Exactly one of the three attributes is set. `folder` and `organization` hold
  fully qualified IDs ('folders/123456', 'organizations/654321') because that is
  the form the API expects, while `project` holds a bare project ID.

  Build instances with FromArgs, for commands that take no resource reference
  (the list commands), or with FromRef, for commands that resolve one.
  """

  def __init__(
      self,
      project: Optional[str] = None,
      folder: Optional[str] = None,
      organization: Optional[str] = None,
  ):
    self.project = project
    self.folder = folder
    self.organization = organization

  @classmethod
  def FromArgs(cls, args: parser_extensions.Namespace) -> 'Scope':
    """Returns the scope selected by --folder, --organization, or the project.

    Args:
      args: the arguments the command was invoked with. The --folder and
        --organization flags are only registered on the release tracks that
        support them, so they are tested with IsKnownAndSpecified rather than
        read directly.
    """
    if args.IsKnownAndSpecified('folder'):
      return cls(folder=_Qualify('folders', args.folder))
    if args.IsKnownAndSpecified('organization'):
      return cls(organization=_Qualify('organizations', args.organization))
    return cls(project=properties.VALUES.core.project.GetOrFail())

  @classmethod
  def FromRef(cls, ref: resources.Resource) -> 'Scope':
    """Returns the scope of an already resolved resource reference.

    Args:
      ref: a reference parsed against one of the project, folder, or
        organization collections. A reference only carries the attributes of its
        own collection, so a missing 'folder' attribute is what distinguishes
        the scopes.
    """
    folder = getattr(ref, 'folder', None)
    if folder:
      return cls(folder=_Qualify('folders', folder))
    organization = getattr(ref, 'organization', None)
    if organization:
      return cls(organization=_Qualify('organizations', organization))
    return cls(project=ref.project)

  @property
  def is_folder(self) -> bool:
    return self.folder is not None

  @property
  def is_organization(self) -> bool:
    return self.organization is not None

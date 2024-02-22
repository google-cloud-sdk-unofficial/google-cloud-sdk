# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Command to list Container Registry usage."""

import frozendict
from googlecloudsdk.api_lib.container.images import gcr_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.asset import flags as asset_flags
from googlecloudsdk.command_lib.asset import utils as asset_utils


_DETAILED_HELP = frozendict.frozendict({
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To list Container Registry usage in a project:

          $ {command} --project=my-proj

        To list Container Registry usage in an organization:

          $ {command} --organization=my-org

        To list Container Registry usage in a folder:

          $ {command} --folder=my-folder
        """,
})


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListGCRUsage(base.ListCommand):
  """List Container Registry usage.

  List Container Registry usage for all projects in the specified scope
  (project/organization/folder). Caller must have
  `cloudasset.assets.searchAllResources` permission on the requested scope and
  `storage.objects.list permission` on the Cloud Storage buckets used by
  Container Registry.

  REDIRECTED: Container Registry projects that have been redirected to Artifact
  Registry.

  ACTIVE: Container Registry projects that have had a pull or push in the last
  30 days.

  INACTIVE: Container Registry projects that have not had a pull or push in the
  last 30 days.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    asset_flags.AddParentArgs(
        parser,
        'Project ID.',
        'Organization ID.',
        'Folder ID.',
    )
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    parent = asset_utils.GetParentNameForExport(
        args.organization,
        args.project,
        args.folder,
    )
    gcr_repos = gcr_utils.ListGCRRepos(parent)
    for gcr_repo in gcr_repos:
      yield gcr_utils.CheckGCRUsage(gcr_repo)

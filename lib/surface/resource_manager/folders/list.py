# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Command to list all folder IDs associated with the active user."""

import textwrap

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import flags
from googlecloudsdk.command_lib.resource_manager import folders_base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(folders_base.FolderCommand, base.ListCommand):
  """List folders accessible by the active account.

  List all folders to which the user has access under the specified
  parent (either an Organization or a Folder). Exactly one of --folder
  or --organization must be provided.
  """

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
          The following command lists folders under org with ID
          `123456789`:

            $ {command} --organization=123456789

          The following command lists folders under folder with ID
          `123456789`:

            $ {command} --folder=123456789
    """),
  }

  @staticmethod
  def Args(parser):
    flags.FolderIdFlag('to list folders under').AddToParser(parser)
    flags.OrganizationIdFlag('to list folders under').AddToParser(parser)

  def Run(self, args):
    """Run the list command."""
    flags.CheckParentFlags(args)
    return list_pager.YieldFromList(
        folders.FoldersService(),
        folders.FoldersMessages().CloudresourcemanagerFoldersListRequest(
            parent=flags.GetParentFromFlags(args)),
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        field='folders')

  def Format(self, args):
    return 'table({fields})'.format(fields=','.join([
        'displayName:label=DISPLAY_NAME', 'parent:label=PARENT_NAME',
        'name.segment():label=ID:align=right:sort=1'
    ]))

# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""List Artifact Registry files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.command_lib.artifacts import util

DEFAULT_LIST_FORMAT = """\
    table(
      name:label=FILE,
      createTime.date(tz=LOCAL),
      updateTime.date(tz=LOCAL),
      sizeBytes.size(zero='0',precision=3,units_out=M):label="SIZE (MB)",
      owner:label=OWNER
    )"""


@base.Hidden
class List(base.ListCommand):
  """List Artifact Registry files.

  List all Artifact Registry files in the specified repository and location.

  To specify the maximum number of files to list, use the --limit flag.
  """

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
      To list files in the current project under repository `my-repo` in `us-central1`:

          $ {command} --repository=my-repo --location=us-central1

      The following command lists a maximum of five files:

          $ {command} --repository=my-repo --location=us-central1 --limit=5
      """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(DEFAULT_LIST_FORMAT)
    base.URI_FLAG.RemoveFromParser(parser)
    flags.GetRepoFlag().AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A list of files.
    """

    return util.ListFiles(args)

# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Implementation of rsync command for Cloud Storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Rsync(base.Command):
  """Synchronize content of two buckets/directories."""

  detailed_help = {
      'DESCRIPTION': """
      *{command}* copies to and updates objects at `DESTINATION` to match
      `SOURCE`. `SOURCE` must specify a directory, bucket, or bucket
      subdirectory. *{command}* does not copy empty directory trees,
      since storage providers use a [flat namespace](https://cloud.google.com/storage/docs/folders).

      Note, shells (like bash, zsh) sometimes attempt to expand wildcards in
      ways that can be surprising. Also, attempting to copy files whose names
      contain wildcard characters can result in problems.

      If synchronizing a large amount of data between clouds you might consider
      setting up a Google Compute Engine account and running *{command}* there.
      Since *{command}* cross-provider data transfers flow through the machine
      where *{command}* is running, doing this can make your transfer run
      significantly faster than on your local workstation.

      """,
      'EXAMPLES': """
      To sync the contents of the local directory ``data'' to the bucket
      gs://my-bucket/data:

        $ {command} data gs://my-bucket/data
      """,
      # TODO(b/267511499): Code for rest of examples in bug.
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('source', help='The source container path.')
    parser.add_argument('destination', help='The destination container path.')
    # TODO(b/267511499): Code for unimplemented flags in bug.

  def Run(self, args):
    del args  # Unused.
    # TODO(b/267511499): Not-so-pseudocode in bug.
    raise NotImplementedError

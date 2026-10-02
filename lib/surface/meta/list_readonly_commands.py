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

"""A command that lists all gcloud commands designated as read-only."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.meta import list_readonly_commands as readonly_util

# Re-export for backward compatibility with external imports.
NormalizeRestrict = readonly_util.NormalizeRestrict
_NormalizeRestrict = NormalizeRestrict
DisplayReadOnlyCommands = readonly_util.DisplayReadOnlyCommands
ReadOnlyCommandWalker = readonly_util.ReadOnlyCommandWalker


@base.UniverseCompatible
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListReadOnlyCommands(base.Command):
  """List gcloud CLI commands filtered by their read_only metadata state."""

  detailed_help = {
      'DESCRIPTION': """\
          `{command}` traverses the `gcloud` CLI command tree and lists leaf
          commands matching the requested `read_only` metadata state
          (`--state=readonly`, `--state=mutating`, or `--state=unannotated`).

          Output is streamed progressively line by line as each matching
          command path is visited in depth-first lexicographical order.
      """,
      'EXAMPLES': """\
          To list all visible `gcloud` CLI commands explicitly annotated as
          read-only, run:

            $ {command}

          To list all visible mutating commands under `gcloud compute
          instances`, run:

            $ {command} compute.instances --state=mutating

          To list all unannotated commands (including hidden commands and
          groups) across `gcloud compute instances` and `gcloud storage
          buckets`, run:

            $ {command} compute.instances storage.buckets --state=unannotated --hidden
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--state',
        choices=['readonly', 'mutating', 'unannotated'],
        default='readonly',
        help=(
            'Filter commands by their `read_only` metadata state. '
            '`readonly` lists commands explicitly marked `read_only: true`. '
            '`mutating` lists commands explicitly marked `read_only: false`. '
            '`unannotated` lists commands that lack explicit `read_only` '
            'metadata.'
        ),
    )
    parser.add_argument(
        '--hidden',
        action='store_true',
        help='If set, include hidden commands and groups in the scan.',
    )
    parser.add_argument(
        'restrict',
        metavar='COMMAND/GROUP',
        nargs='*',
        help=(
            'Dotted or space-separated command or group path prefixes to '
            'restrict the scan (for example, `gcloud.compute.instances` or '
            '`compute.instances`). Multiple paths may be specified; '
            'non-existent paths are ignored.'
        ),
    )

  def Run(self, args):
    top_name = getattr(self._cli_power_users_only, 'name', 'gcloud')
    restrict = readonly_util.NormalizeRestrict(args.restrict, top_name=top_name)
    cmd_walker = readonly_util.ReadOnlyCommandWalker(
        self._cli_power_users_only,
        restrict=restrict,
        state=args.state,
    )
    return cmd_walker.Walk(hidden=args.hidden, restrict=restrict)

  def Display(self, args, result):
    del args  # Unused.
    readonly_util.DisplayReadOnlyCommands(result)


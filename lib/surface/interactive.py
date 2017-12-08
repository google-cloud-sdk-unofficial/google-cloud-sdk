# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Extensible interactive shell with auto completion and help."""

from __future__ import unicode_literals

import StringIO

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.shell import application
from googlecloudsdk.core.document_renderers import render_document


_SPLASH = """
# Welcome to the gcloud interactive shell environment.

Features in this release include:

* auto-completion for gcloud commands, flags and resource arguments
* support for other CLIs including *bq*, *gsutil* and *kubectl*
* state preserved across commands: *cd*, local and environment variables
* as-you-type help snippets for the current command or flag

Run `$ gcloud feedback` to report bugs or request new features.

"""


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Interactive(base.Command):
  """Start the gcloud interactive shell.

  *{command}* features include:

  * auto-completion for gcloud commands, flags and resource arguments
  * support for other CLIs including *bq*, *gsutil* and *kubectl*
  * state preserved across commands: *cd*, local and environment variables
  * as-you-type help snippets for the current command or flag

  Run `$ gcloud feedback` to report bugs or request new features.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--hidden',
        hidden=True,
        action='store_true',
        help='Enable completion of hidden commands and flags.')
    parser.add_argument(
        '--prompt',
        default='$ ',
        help='The interactive shell prompt.')

  def Run(self, args):
    if not args.quiet:
      render_document.RenderDocument(fin=StringIO.StringIO(_SPLASH))
    application.main(
        cli=self._cli_power_users_only,
        args=args,
        hidden=args.hidden,
        prompt=args.prompt,
    )

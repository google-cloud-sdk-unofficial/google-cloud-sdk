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

"""`gcloud alpha interactive` implementation."""

from __future__ import unicode_literals

import StringIO

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.shell import application
from googlecloudsdk.command_lib.shell import config as configuration
from googlecloudsdk.core.document_renderers import render_document


_SPLASH = """
# Welcome to the gcloud interactive shell environment.

Run `gcloud feedback` to report bugs or feature requests.

"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Shell(base.Command):
  """Start the gcloud interactive shell.

  *{command}* has menu based auto completion and displays help snippets
  as each part of a *gcloud* sub-command is typed. The initial context is
  set to *gcloud*; you only need to enter subcommands.
  """

  def Run(self, args):
    if not args.quiet:
      render_document.RenderDocument(fin=StringIO.StringIO(_SPLASH))
    config = configuration.Config(context='gcloud ')
    application.main(args=args, config=config)

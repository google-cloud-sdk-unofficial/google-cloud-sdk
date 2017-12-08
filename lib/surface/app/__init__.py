# Copyright 2013 Google Inc. All Rights Reserved.
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

"""The gcloud app group."""

import sys

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import checks
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import platforms


DETAILED_HELP = {
    'brief': 'Manage your App Engine app.',
    'DESCRIPTION': """
        This set of commands allows you to deploy your app, manage your existing
        deployments, and also run your app locally.  These commands replace
        their equivalents in the appcfg tool.
        """,
    'EXAMPLES': """\
        To run your app locally in the development application server, run:

          $ dev_appserver.py DEPLOYABLES

        To create a new deployment of one or more services, run:

          $ {command} deploy DEPLOYABLES

        To list your existing deployments, run:

          $ {command} versions list

        To generate config files for your source directory:

          $ {command} gen-config
        """
}


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class AppengineGA(base.Group):

  def Filter(self, unused_context, unused_args):
    checks.RaiseIfNotPython27()


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.PREVIEW)
class AppenginePreview(base.Group):

  def Filter(self, unused_context, unused_args):
    log.warn('The `gcloud preview app` command group is deprecated; please use '
             'the `gcloud app` commands instead.')
    checks.RaiseIfNotPython27()


AppengineGA.detailed_help = DETAILED_HELP
AppenginePreview.detailed_help = DETAILED_HELP

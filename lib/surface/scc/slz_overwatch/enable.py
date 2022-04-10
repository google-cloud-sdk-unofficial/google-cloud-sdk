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
"""Command to enables overwatch in an organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
import textwrap

from googlecloudsdk.api_lib.scc.slz_overwatch import overwatch as api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.scc.slz_overwatch import overwatch_flags as flags
from googlecloudsdk.command_lib.scc.slz_overwatch import util
from googlecloudsdk.core import properties

_DETAILED_HELP = {
    'BRIEF':
        'Enable Secured Landing Zone overwatch in an organization.',
    'EXAMPLES':
        textwrap.dedent("""\
        The following command enables overwatch in organization with ID `123`.

        $ {command} organizations/123
        """)
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Enable(base.Command):
  """Enable overwatch in an organization."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.get_organization_id_flag().AddToParser(parser)

  def Run(self, args):
    org_id = args.ORGANIZATION
    if not re.match('organizations/[0-9]+', org_id):
      raise exceptions.InvalidArgumentException(
          'ORGANIZATION', 'The organization id should be of the form'
          ' organizations/<organization_id>, found {}'.format(org_id))
    with util.override_endpoint():
      client = api.SLZOverwatchClient()
      return client.Enable(org_id,
                           properties.VALUES.scc.slz_overwatch_location.Get())

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
"""Command to create a login configuration file used to enable browser based sign-in using third-party user identities via gcloud auth login.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

RESOURCE_TYPE = 'login configuration file'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateLoginConfig(base.CreateCommand):
  """Create a login configuration file to enable sign-in via a web-based authorization flow using Workforce Identity Federation.

  This command creates a configuration file to enable browser based
  third-party sign in with Workforce Identity Federation through
  `gcloud auth login --login-config=/path/to/config.json`.
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To create a login configuration for your project, run:

            $ {command} locations/global/workforcePools/$WORKFORCE_POOL_ID/providers/$PROVIDER_ID --output-file=login-config.json
          """),
  }

  @classmethod
  def Args(cls, parser):
    # Required args.
    parser.add_argument(
        'audience', help='Workforce pool provider resource name.')
    parser.add_argument(
        '--output-file',
        help='Location to store the generated login configuration file.',
        required=True)

  def Run(self, args):
    output = {
        'type': 'external_account_authorized_user_login_config',
        'audience': '//iam.googleapis.com/' + args.audience,
        'auth_url': 'https://auth.cloud.google/authorize',
        'token_url': 'https://sts.googleapis.com/v1/oauth/token',
        'token_info_url': 'https://sts.googleapis.com/v1/instrospect',
    }
    files.WriteFileContents(args.output_file, json.dumps(output, indent=2))
    log.CreatedResource(args.output_file, RESOURCE_TYPE)

# -*- coding: utf-8 -*- #
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
"""The gcloud serverless group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


DETAILED_HELP = {
    'brief': 'Manage your Serverless applications.',
    'DESCRIPTION': """
        The gcloud serverless command group lets you deploy container images
        to Google Serverless Engine.
        """,
    'EXAMPLES': """\
        To deploy your container, use the `gcloud serverless deploy` command:

          $ gcloud serverless deploy <service-name> --image <image_name>

        For more information, run:
          $ gcloud serverless deploy --help
        """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Serverless(base.Group):
  """Manage your Serverless resources."""

  detailed_help = DETAILED_HELP


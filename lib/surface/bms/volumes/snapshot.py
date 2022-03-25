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
"""'Bare Metal Solution volumes "snapshot" command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a snapshot of a Bare Metal Solution volume.
        """,
    'EXAMPLES':
        """
          To create a snapshot of a volume named ``my-volume'' in region
          ``us-central1'' with the description ``my-description'', run:

          $ {command} my-volume --region=us-central1 --description=my-description
    """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a snapshot of a Bare Metal Solution volume."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddVolumeArgToParser(parser, positional=True)
    parser.add_argument('--description',
                        help='Textual description of the snapshot.')

  def Run(self, args):
    volume = args.CONCEPTS.volume.Parse()
    client = BmsClient()

    res = client.CreateVolumeSnapshot(resource=volume,
                                      description=args.description)
    log.CreatedResource(res.name.split('/')[-1], 'snapshot')
    return res


Create.detailed_help = DETAILED_HELP

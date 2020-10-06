# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Deploy a Knative service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To update one or more env vars:

            $ {command} --update-env-vars=KEY1=VALUE1,KEY2=VALUE2
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(kuberun_command.KubeRunStreamingCommand, base.UpdateCommand):
  """Updates a Knative service."""

  detailed_help = _DETAILED_HELP
  flags = [
      flags.ClusterConnectionFlags(),
      flags.CommonServiceFlags(),
      flags.NoTrafficFlag(),
      flags.AsyncFlag()
  ]

  @classmethod
  def Args(cls, parser):
    super(Update, cls).Args(parser)
    parser.add_argument(
        'service',
        help='ID of the service or fully qualified identifier for the service.')

  def BuildKubeRunArgs(self, args):
    return [args.service] + super(Update, self).BuildKubeRunArgs(args)

  def OperationResponseHandler(self, response, args):
    if response.failed:
      log.error(response.stderr)
      return None

    if response.stderr:
      log.status.Print(response.stderr)

    return response.stdout

  def Command(self):
    return ['clusters', 'services', 'update']
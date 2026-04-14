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
"""Command to SSH into a Cloud Run job."""

from googlecloudsdk.api_lib.run import ssh as run_ssh
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import ssh_command


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.DefaultUniverseOnly
class Ssh(ssh_command.BaseSshCommand):
  """SSH into a job instance."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Starts a secure, interactive shell session with an instance of a Cloud Run job.
          """
      ),
      'EXAMPLES': (
          """\
          To start an interactive shell session with a Cloud Run job:

              $ {command} my-job --instance=my-instance-id
          """
      ),
  }

  @classmethod
  def Args(cls, parser):
    flags.AddInstanceArg(parser)
    cls.AddBaseArgs(parser)
    parser.add_argument('job', help='The name of the job to SSH into.')

  def Run(self, args):
    self.RunSsh(
        args,
        run_ssh.Ssh.WorkloadType.JOB,
        args.job,
        getattr(args, 'instance', None),
    )

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
"""Base class for Cloud Run SSH commands."""

from googlecloudsdk.api_lib.run import ssh as run_ssh
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags


class BaseSshCommand(base.Command):
  """Base class for Cloud Run SSH commands."""

  @staticmethod
  def AddBaseArgs(parser):
    """Add flags common to all SSH commands."""
    flags.AddContainerArg(parser)
    parser.add_argument(
        '--iap-tunnel-url-override',
        hidden=True,
        help=(
            'Allows for overriding the connection endpoint for integration'
            ' testing.'
        ),
    )

  def RunSsh(
      self,
      args,
      workload_type,
      deployment_name,
      instance_id=None,
  ):
    """Common Run logic for SSH commands."""
    args.project = flags.GetProjectID(args)
    args.region = flags.GetRegion(args, prompt=False)
    args.deployment_name = deployment_name
    args.instance = instance_id
    args.release_track = self.ReleaseTrack()

    if not args.region:
      raise exceptions.ArgumentError(
          'Missing required argument [region]. Set --region flag or set'
          ' run/region property.'
      )
    if (
        args.release_track != base.ReleaseTrack.ALPHA
        and instance_id
        and getattr(args, 'revision', None) is None
    ):
      raise exceptions.ArgumentError(
          'Revision must be specified with instance. Set --revision flag when'
          ' --instance flag is set.'
      )
    run_ssh.Ssh(args, workload_type).Run()

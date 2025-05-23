# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command to list Airflow plugins for a Cloud Composer environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import storage_util

DETAILED_HELP = {
    'EXAMPLES':
        """\
        To list the plugins for the Cloud Composer environment
        ``environment-1'' and location ``us-central1'', run:

          $ {command} --environment=environment-1 --location=us-central1
        """
}


class List(base.Command):
  """List the plugins for a Cloud Composer environment."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(
        parser, 'for which to list plugins.', positional=False)
    parser.display_info.AddFormat('table(name)')

  def Run(self, args):
    env_ref = args.CONCEPTS.environment.Parse()
    return storage_util.List(
        env_ref, 'plugins', release_track=self.ReleaseTrack())

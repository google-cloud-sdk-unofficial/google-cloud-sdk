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
"""Command that stores environment snapshot for State/Disaster recovery."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.api_lib.composer import operations_util as operations_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import log
import six

DETAILED_HELP = {
    'EXAMPLES':
        textwrap.dedent("""\
          To create a snapshot of the environment state using state store
          operation in an environment named ``env-1``, run:

            $ {command} env-1
        """)
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class StoreEnvironmentState(base.Command):
  """Store state of the environment by creating a snapshot."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(parser,
                                            'to store state of environment')
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        '--snapshot-location',
        type=str,
        help='The Cloud Storage location to store the snapshot. It must start '
        'with prefix gs://. Default value is /snapshots directory in the Cloud '
        'Storage bucket of the environment.')

  def Run(self, args):
    env_resource = args.CONCEPTS.environment.Parse()
    operation = environments_api_util.StoreEnvironmentState(
        env_resource, args.snapshot_location, release_track=self.ReleaseTrack())
    if args.async_:
      return self._AsynchronousExecution(env_resource, operation)
    else:
      return self._SynchronousExecution(env_resource, operation)

  def _AsynchronousExecution(self, env_resource, operation):
    log.UpdatedResource(
        env_resource.RelativeName(),
        kind='environment',
        is_async=True,
        details='with operation [{}]'.format(operation.name))
    return operation

  def _SynchronousExecution(self, env_resource, operation):
    try:
      operations_api_util.WaitForOperation(
          operation,
          'Waiting for [{}] to be updated with [{}]'.format(
              env_resource.RelativeName(), operation.name),
          release_track=self.ReleaseTrack())
    except command_util.Error as e:
      raise command_util.Error(
          'Failed to store the state of the environment [{}]: {}'.format(
              env_resource.RelativeName(), six.text_type(e)))

# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to list Knative revisions in a Kubernetes cluster."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.kuberun import revision
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.command_lib.kuberun import pretty_print
from googlecloudsdk.core import exceptions

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To show all Knative revisions in the default namespace, run

            $ {command}

        To show all Knative revisions in a namespace, run

            $ {command} --namespace=my-namespace

        To show all Knative revisions from all namespaces, run

            $ {command} --all-namespaces
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(kuberun_command.KubeRunCommandWithOutput, base.ListCommand):
  """Lists revisions in a Knative cluster."""

  @staticmethod
  def _Flags(parser):
    kuberun_command.KubeRunCommandWithOutput._Flags(parser)
    base.FILTER_FLAG.AddToParser(parser)
    base.LIMIT_FLAG.AddToParser(parser)
    base.PAGE_SIZE_FLAG.AddToParser(parser)
    base.SORT_BY_FLAG.AddToParser(parser)
    List._SetFormat(parser)

  @staticmethod
  def _SetFormat(parser):
    """Set display format for output.

    Args:
      parser: args parser to use to set the display format
    """
    columns = [
        pretty_print.READY_COLUMN,
        'name:label=REVISION',
        'namespace:label=NAMESPACE',
        'url',
        'last_modifier:label="LAST DEPLOYED BY"',
        'last_transition_time:label="LAST DEPLOYED AT"',
    ]
    parser.display_info.AddFormat('table({})'.format(','.join(columns)))

  @staticmethod
  def Args(parser):
    flags.AddNamespaceFlagsMutexGroup(parser)

  def BuildKubeRunArgs(self, args):
    return []

  def Command(self):
    return ['clusters', 'revisions', 'list']

  def FormatOutput(self, out, args):
    if out:
      json_object = json.loads(out)
      return [revision.Revision(x) for x in json_object]
    else:
      raise exceptions.Error('Cannot list revisions')


List.detailed_help = _DETAILED_HELP

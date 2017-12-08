# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Stackdriver logging sinks group."""

from googlecloudsdk.calliope import base


class Sinks(base.Group):
  """Manages sinks used to export logs."""

  @staticmethod
  def Args(parser):
    """Add log name and log service name flags, used by sinks subcommands."""
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--log',
        help=('DEPRECATED. The name of a log. Use this argument only '
              'if the sink applies to a single log.'))
    group.add_argument(
        '--log-service', dest='service',
        help=('DEPRECATED. The name of a log service. Use this argument '
              'only if the sink applies to all logs from '
              'a log service.'))

  def Filter(self, context, args):
    """Modify the context that will be given to this group's commands when run.

    Args:
      context: The current context.
      args: The argparse namespace given to the corresponding .Run() invocation.

    Returns:
      Updated context, with sink reference added based on args.
    """
    if 'sink_name' not in args:
      return context

    if args.log:
      collection = 'logging.projects.logs.sinks'
      params = {'logsId': args.log}
    elif args.service:
      collection = 'logging.projects.logServices.sinks'
      params = {'logServicesId': args.service}
    else:
      collection = 'logging.projects.sinks'
      params = {}

    context['sink_reference'] = context['logging_resources'].Parse(
        args.sink_name, params=params, collection=collection)
    return context

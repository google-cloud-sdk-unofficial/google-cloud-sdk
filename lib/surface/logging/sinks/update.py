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

"""'logging sinks update' command."""

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log


class Update(base.UpdateCommand):
  """Updates a sink."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'sink_name', help='The name of the sink to update.')
    parser.add_argument(
        'destination', nargs='?',
        help=('A new destination for the sink. '
              'If omitted, the sink\'s existing destination is unchanged.'))
    parser.add_argument(
        '--log-filter', required=False,
        help=('A new filter expression for the sink. '
              'If omitted, the sink\'s existing filter (if any) is unchanged.'))
    parser.add_argument(
        '--output-version-format', required=False,
        help=('Format of the log entries being exported. Detailed information: '
              'https://cloud.google.com/logging/docs/api/introduction_v2'),
        choices=('V1', 'V2'))
    parser.add_argument(
        '--unique-writer-identity', required=False, action='store_true',
        default=True,
        help=('Whether to create a new writer identity for this sink. Only '
              'available for project sinks.'))
    util.AddNonProjectArgs(parser, 'Update a sink')

  def Collection(self):
    return 'logging.sinks'

  def GetLogSink(self):
    """Returns a log sink specified by the arguments."""
    client = util.GetClientV1()
    ref = self.context['sink_reference']
    return client.projects_logs_sinks.Get(
        client.MESSAGES_MODULE.LoggingProjectsLogsSinksGetRequest(
            projectsId=ref.projectsId,
            logsId=ref.logsId,
            sinksId=ref.sinksId))

  def GetLogServiceSink(self):
    """Returns a log service sink specified by the arguments."""
    client = util.GetClientV1()
    ref = self.context['sink_reference']
    return client.projects_logServices_sinks.Get(
        client.MESSAGES_MODULE.LoggingProjectsLogServicesSinksGetRequest(
            projectsId=ref.projectsId,
            logServicesId=ref.logServicesId,
            sinksId=ref.sinksId))

  def GetSink(self, parent):
    """Returns a sink specified by the arguments."""
    # Use V2 logging API.
    sink_ref = self.context['sink_reference']
    return util.GetClient().projects_sinks.Get(
        util.GetMessages().LoggingProjectsSinksGetRequest(
            sinkName=util.CreateResourceName(
                parent, 'sinks', sink_ref.sinksId)))

  def UpdateLogSink(self, sink_data):
    """Updates a log sink specified by the arguments."""
    messages = util.GetMessagesV1()
    sink_ref = self.context['sink_reference']
    return util.GetClientV1().projects_logs_sinks.Update(
        messages.LoggingProjectsLogsSinksUpdateRequest(
            projectsId=sink_ref.projectsId, logsId=sink_ref.logsId,
            sinksId=sink_data['name'], logSink=messages.LogSink(**sink_data)))

  def UpdateLogServiceSink(self, sink_data):
    """Updates a log service sink specified by the arguments."""
    messages = util.GetMessagesV1()
    sink_ref = self.context['sink_reference']
    return util.GetClientV1().projects_logServices_sinks.Update(
        messages.LoggingProjectsLogServicesSinksUpdateRequest(
            projectsId=sink_ref.projectsId,
            logServicesId=sink_ref.logServicesId, sinksId=sink_data['name'],
            logSink=messages.LogSink(**sink_data)))

  def UpdateSink(self, parent, sink_data, unique_writer_identity):
    """Updates a sink specified by the arguments."""
    # Use V2 logging API.
    messages = util.GetMessages()
    # Change string value to enum.
    sink_data['outputVersionFormat'] = getattr(
        messages.LogSink.OutputVersionFormatValueValuesEnum,
        sink_data['outputVersionFormat'])
    return util.GetClient().projects_sinks.Update(
        messages.LoggingProjectsSinksUpdateRequest(
            sinkName=util.CreateResourceName(
                parent, 'sinks', sink_data['name']),
            logSink=messages.LogSink(**sink_data),
            uniqueWriterIdentity=unique_writer_identity))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated sink with its new destination.
    """
    util.CheckSinksCommandArguments(args)

    if not args.unique_writer_identity:
      log.warn(
          '--unique-writer-identity is deprecated and will soon be removed.')

    # One of the flags is required to update the sink.
    # log_filter can be an empty string, so check explicitly for None.
    if not (args.destination or args.log_filter is not None or
            args.output_version_format):
      raise calliope_exceptions.ToolException(
          '[destination], --log-filter or --output-version-format is required')

    # Calling Update on a non-existing sink creates it.
    # We need to make sure it exists, otherwise we would create it.
    try:
      if args.log:
        sink = self.GetLogSink()
      elif args.service:
        sink = self.GetLogServiceSink()
      else:
        sink = self.GetSink(util.GetParentFromArgs(args))
    except apitools_exceptions.HttpError as error:
      v2_sink = not args.log and not args.service
      # Suggest the user to add --log or --log-service flag.
      if v2_sink and exceptions.HttpException(error).payload.status_code == 404:
        log.status.Print(('Sink was not found. '
                          'Did you forget to add --log or --log-service flag?'))
      raise error

    # Only update fields that were passed to the command.
    if args.destination:
      destination = args.destination
    else:
      destination = sink.destination

    if args.log_filter is not None:
      log_filter = args.log_filter
    else:
      log_filter = sink.filter

    sink_ref = self.context['sink_reference']
    sink_data = {'name': sink_ref.sinksId, 'destination': destination,
                 'filter': log_filter}

    if args.log:
      result = util.TypedLogSink(self.UpdateLogSink(sink_data),
                                 log_name=args.log)
      kind = 'log sink'
    elif args.service:
      result = util.TypedLogSink(self.UpdateLogServiceSink(sink_data),
                                 service_name=args.service)
      kind = 'service log sink'
    else:
      if args.output_version_format:
        sink_data['outputVersionFormat'] = args.output_version_format
      else:
        sink_data['outputVersionFormat'] = sink.outputVersionFormat.name
      result = util.TypedLogSink(
          self.UpdateSink(util.GetParentFromArgs(args), sink_data,
                          args.unique_writer_identity))
      kind = 'sink'
    log.UpdatedResource(sink_ref, kind=kind)
    util.PrintPermissionInstructions(result.destination, result.writer_identity)
    return result


Update.detailed_help = {
    'DESCRIPTION': """\
        Changes the *[destination]* or *--log-filter* associated with a sink.
        If you don't include one of the *--log* or *--log-service* flags,
        this command updates a v2 sink.
        The new destination must already exist and Stackdriver Logging must have
        permission to write to it.
        Log entries are exported to the new destination immediately.
    """,
    'EXAMPLES': """\
        To only update a sink filter, run:

          $ {command} my-sink --log-filter='severity>=ERROR'

        Detailed information about filters can be found at:
        [](https://cloud.google.com/logging/docs/view/advanced_filters)
   """,
}

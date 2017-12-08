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
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log


class Update(base.Command):
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

  def Collection(self):
    return 'logging.sinks'

  def GetLogSink(self):
    """Returns a log sink specified by the arguments."""
    client = self.context['logging_client_v1beta3']
    return client.projects_logs_sinks.Get(
        self.context['sink_reference'].Request())

  def GetLogServiceSink(self):
    """Returns a log service sink specified by the arguments."""
    client = self.context['logging_client_v1beta3']
    return client.projects_logServices_sinks.Get(
        self.context['sink_reference'].Request())

  def GetProjectSink(self):
    """Returns a project sink specified by the arguments."""
    # Use V2 logging API for project sinks.
    client = self.context['logging_client_v2beta1']
    messages = self.context['logging_messages_v2beta1']
    sink_ref = self.context['sink_reference']
    return client.projects_sinks.Get(
        messages.LoggingProjectsSinksGetRequest(
            projectsId=sink_ref.projectsId, sinksId=sink_ref.sinksId))

  def UpdateLogSink(self, sink_data):
    """Updates a log sink specified by the arguments."""
    client = self.context['logging_client_v1beta3']
    messages = self.context['logging_messages_v1beta3']
    sink_ref = self.context['sink_reference']
    return client.projects_logs_sinks.Update(
        messages.LoggingProjectsLogsSinksUpdateRequest(
            projectsId=sink_ref.projectsId, logsId=sink_ref.logsId,
            sinksId=sink_data['name'], logSink=messages.LogSink(**sink_data)))

  def UpdateLogServiceSink(self, sink_data):
    """Updates a log service sink specified by the arguments."""
    client = self.context['logging_client_v1beta3']
    messages = self.context['logging_messages_v1beta3']
    sink_ref = self.context['sink_reference']
    return client.projects_logServices_sinks.Update(
        messages.LoggingProjectsLogServicesSinksUpdateRequest(
            projectsId=sink_ref.projectsId,
            logServicesId=sink_ref.logServicesId, sinksId=sink_data['name'],
            logSink=messages.LogSink(**sink_data)))

  def UpdateProjectSink(self, sink_data):
    """Updates a project sink specified by the arguments."""
    # Use V2 logging API for project sinks.
    client = self.context['logging_client_v2beta1']
    messages = self.context['logging_messages_v2beta1']
    sink_ref = self.context['sink_reference']
    # Change string value to enum.
    sink_data['outputVersionFormat'] = getattr(
        messages.LogSink.OutputVersionFormatValueValuesEnum,
        sink_data['outputVersionFormat'])
    return client.projects_sinks.Update(
        messages.LoggingProjectsSinksUpdateRequest(
            projectsId=sink_ref.projectsId, sinksId=sink_data['name'],
            logSink=messages.LogSink(**sink_data)))

  @util.HandleHttpError
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated sink with its new destination.
    """
    util.CheckSinksCommandArguments(args)

    # One of the flags is required to update the sink.
    # log_filter can be an empty string, so check explicitly for None.
    if not (args.destination or args.log_filter is not None or
            args.output_version_format):
      raise exceptions.ToolException(
          '[destination], --log-filter or --output-version-format is required')

    # Calling Update on a non-existing sink creates it.
    # We need to make sure it exists, otherwise we would create it.
    try:
      if args.log:
        sink = self.GetLogSink()
      elif args.service:
        sink = self.GetLogServiceSink()
      else:
        sink = self.GetProjectSink()
    except apitools_exceptions.HttpError as error:
      project_sink = not args.log and not args.service
      # Suggest the user to add --log or --log-service flag.
      if project_sink and error.response.status == 404:
        log.status.Print(('Project sink was not found. '
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
    elif args.service:
      result = util.TypedLogSink(self.UpdateLogServiceSink(sink_data),
                                 service_name=args.service)
    else:
      if args.output_version_format:
        sink_data['outputVersionFormat'] = args.output_version_format
      else:
        sink_data['outputVersionFormat'] = sink.outputVersionFormat.name
      result = util.TypedLogSink(self.UpdateProjectSink(sink_data))
    log.UpdatedResource(sink_ref)
    self._epilog_result_destination = result.destination
    return result

  def Epilog(self, unused_resources_were_displayed):
    util.PrintPermissionInstructions(self._epilog_result_destination)


Update.detailed_help = {
    'DESCRIPTION': """\
        Changes the *[destination]* or *--log-filter* associated with a sink.
        If you don't include one of the *--log* or *--log-service* flags,
        this command updates a project sink.
        The new destination must already exist and Cloud Logging must have
        permission to write to it.
        Log entries are exported to the new destination immediately.
    """,
    'EXAMPLES': """\
        To only update a project sink filter, run:

          $ {command} my-sink --log-filter='metadata.severity>=ERROR'

        Detailed information about filters can be found at:
        [](https://cloud.google.com/logging/docs/view/advanced_filters)
   """,
}

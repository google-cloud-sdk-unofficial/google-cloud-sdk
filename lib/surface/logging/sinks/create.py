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

"""'logging sinks create' command."""

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Create(base.CreateCommand):
  """Creates a sink."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'sink_name', help='The name for the sink.')
    parser.add_argument(
        'destination', help='The destination for the sink.')
    parser.add_argument(
        '--log-filter', required=False,
        help=('A filter expression for the sink. If present, the filter '
              'specifies which log entries to export.'))
    parser.add_argument(
        '--output-version-format', required=False,
        help=('DEPRECATED. Format of the log entries being exported. Detailed '
              'information: '
              'https://cloud.google.com/logging/docs/api/introduction_v2'),
        choices=('V1', 'V2'), default='V1')
    parser.add_argument(
        '--unique-writer-identity', required=False, action='store_true',
        default=True,
        help=('DEPRECATED. Whether to create a new writer identity for this '
              'sink. Only available for v2 sinks.'))
    util.AddNonProjectArgs(parser, 'Create a sink')

  def Collection(self):
    return 'logging.sinks'

  def CreateLogSink(self, sink_data):
    """Creates a log sink specified by the arguments."""
    sink_ref = self.context['sink_reference']
    messages = util.GetMessagesV1()
    return util.GetClientV1().projects_logs_sinks.Create(
        messages.LoggingProjectsLogsSinksCreateRequest(
            projectsId=sink_ref.projectsId, logsId=sink_ref.logsId,
            logSink=messages.LogSink(**sink_data)))

  def CreateLogServiceSink(self, sink_data):
    """Creates a log service sink specified by the arguments."""
    messages = util.GetMessagesV1()
    sink_ref = self.context['sink_reference']
    return util.GetClientV1().projects_logServices_sinks.Create(
        messages.LoggingProjectsLogServicesSinksCreateRequest(
            projectsId=sink_ref.projectsId,
            logServicesId=sink_ref.logServicesId,
            logSink=messages.LogSink(**sink_data)))

  def CreateSink(self, parent, sink_data, unique_writer_identity):
    """Creates a v2 sink specified by the arguments."""
    messages = util.GetMessages()
    # Change string value to enum.
    sink_data['outputVersionFormat'] = getattr(
        messages.LogSink.OutputVersionFormatValueValuesEnum,
        sink_data['outputVersionFormat'])
    return util.GetClient().projects_sinks.Create(
        messages.LoggingProjectsSinksCreateRequest(
            parent=parent, logSink=messages.LogSink(**sink_data),
            uniqueWriterIdentity=unique_writer_identity))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The created sink with its destination.
    """
    util.CheckSinksCommandArguments(args)

    if not args.unique_writer_identity:
      log.warn(
          '--unique-writer-identity is deprecated and will soon be removed.')

    if not (args.log or args.service or args.log_filter):
      # Attempt to create a sink with an empty filter.
      console_io.PromptContinue(
          'Sink with empty filter matches all entries.', cancel_on_no=True)

    sink_ref = self.context['sink_reference']
    sink_data = {'name': sink_ref.sinksId, 'destination': args.destination,
                 'filter': args.log_filter}

    if args.log:
      result = util.TypedLogSink(self.CreateLogSink(sink_data),
                                 log_name=args.log)
    elif args.service:
      result = util.TypedLogSink(self.CreateLogServiceSink(sink_data),
                                 service_name=args.service)
    else:
      sink_data['outputVersionFormat'] = args.output_version_format
      result = util.TypedLogSink(
          self.CreateSink(util.GetParentFromArgs(args), sink_data,
                          args.unique_writer_identity))
    log.CreatedResource(sink_ref)
    self._epilog_result_destination = result.destination
    self._writer_identity = result.writer_identity
    return result

  def Epilog(self, unused_resources_were_displayed):
    util.PrintPermissionInstructions(self._epilog_result_destination,
                                     self._writer_identity)


Create.detailed_help = {
    'DESCRIPTION': """\
        Creates a sink used to export entries from one or more logs to
        a destination.
        A "log" sink exports a single log, specified by the *--log* flag.
        A "log service" sink exports all logs from a log service,
        specified by the *--log-service* flag.
        If you don't include one of the *--log* or *--log-service* flags,
        this command creates a "v2" sink.
        A "v2" sink exports all logs that matches *--log-filter* flag.
        An empty filter matches all logs.
        The sink's destination can be a Cloud Storage bucket,
        a BigQuery dataset, or a Cloud Pub/Sub topic.
        The destination must already exist and Stackdriver Logging must have
        permission to write to it.
        Log entries are exported as soon as the sink is created.
        See https://cloud.google.com/logging/docs/export/configure_export_v2#destination_authorization
    """,
    'EXAMPLES': """\
        To export all Google App Engine logs to BigQuery, run:

          $ {command} --log-service=appengine.googleapis.com my-bq-sink bigquery.googleapis.com/projects/my-project/datasets/my_dataset

        To export "syslog" from App Engine Flexible to Cloud Storage, run:

          $ {command} --log=appengine.googleapis.com/syslog my-gcs-sink storage.googleapis.com/my-bucket

        To export Google App Engine logs with ERROR severity, run:

          $ {command} my-error-logs bigquery.googleapis.com/projects/my-project/datasets/my_dataset --log-filter='resource.type="gae_app" AND severity=ERROR'

        Detailed information about filters can be found at:
        [](https://cloud.google.com/logging/docs/view/advanced_filters)
    """,
}

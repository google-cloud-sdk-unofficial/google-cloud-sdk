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

"""'logging sinks describe' command."""

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class Describe(base.DescribeCommand):
  """Displays information about a sink."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('sink_name', help='The name of the sink to describe.')
    util.AddNonProjectArgs(parser, 'Describe a sink')

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

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified sink with its destination.
    """
    util.CheckLegacySinksCommandArguments(args)

    try:
      if args.log:
        return util.TypedLogSink(self.GetLogSink(), log_name=args.log)
      elif args.service:
        return util.TypedLogSink(self.GetLogServiceSink(),
                                 service_name=args.service)
      else:
        return util.TypedLogSink(self.GetSink(util.GetParentFromArgs(args)))
    except apitools_exceptions.HttpError as error:
      v2_sink = not args.log and not args.service
      # Suggest the user to add --log or --log-service flag.
      if v2_sink and exceptions.HttpException(
          error).payload.status_code == 404:
        log.status.Print(('Sink was not found. '
                          'Did you forget to add --log or --log-service flag?'))
      raise error


Describe.detailed_help = {
    'DESCRIPTION': """\
        Displays information about a sink.
        If you don't include one of the *--log* or *--log-service* flags,
        this command displays information about a v2 sink.
     """,
}

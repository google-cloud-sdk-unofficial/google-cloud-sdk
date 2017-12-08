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

"""'logging sinks delete' command."""

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Deletes a sink."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('sink_name', help='The name of the sink to delete.')
    util.AddNonProjectArgs(parser, 'Delete a sink')

  def DeleteLogSink(self):
    """Deletes a log sink specified by the arguments."""
    messages = util.GetMessagesV1()
    sink_ref = self.context['sink_reference']
    return util.GetClientV1().projects_logs_sinks.Delete(
        messages.LoggingProjectsLogsSinksDeleteRequest(
            projectsId=sink_ref.projectsId, logsId=sink_ref.logsId,
            sinksId=sink_ref.sinksId))

  def DeleteLogServiceSink(self):
    """Deletes a log service sink specified by the arguments."""
    messages = util.GetMessagesV1()
    sink_ref = self.context['sink_reference']
    return util.GetClientV1().projects_logServices_sinks.Delete(
        messages.LoggingProjectsLogServicesSinksDeleteRequest(
            projectsId=sink_ref.projectsId,
            logServicesId=sink_ref.logServicesId, sinksId=sink_ref.sinksId))

  def DeleteSink(self, parent):
    """Deletes a sink specified by the arguments."""
    # Use V2 logging API.
    messages = util.GetMessages()
    sink_ref = self.context['sink_reference']
    return util.GetClient().projects_sinks.Delete(
        messages.LoggingProjectsSinksDeleteRequest(
            sinkName=util.CreateResourceName(
                parent, 'sinks', sink_ref.sinksId)))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.
    """
    util.CheckLegacySinksCommandArguments(args)
    sink_ref = self.context['sink_reference']

    if args.log:
      sink_description = 'log sink [%s] from [%s]' % (
          sink_ref.sinksId, sink_ref.logsId)
    elif args.service:
      sink_description = 'log-service sink [%s] from [%s]' % (
          sink_ref.sinksId, sink_ref.logServicesId)
    else:
      sink_description = 'sink [%s]' % sink_ref.sinksId

    if not console_io.PromptContinue('Really delete %s?' % sink_description):
      raise calliope_exceptions.ToolException('action canceled by user')

    try:
      if args.log:
        self.DeleteLogSink()
      elif args.service:
        self.DeleteLogServiceSink()
      else:
        self.DeleteSink(util.GetParentFromArgs(args))
      log.DeletedResource(sink_ref)
    except apitools_exceptions.HttpError as error:
      v2_sink = not args.log and not args.service
      # Suggest the user to add --log or --log-service flag.
      if v2_sink and exceptions.HttpException(
          error).payload.status_code == 404:
        log.status.Print(('Sink was not found. '
                          'Did you forget to add --log or --log-service flag?'))
      raise error


Delete.detailed_help = {
    'DESCRIPTION': """\
        Deletes a sink and halts the export of log entries associated
        with that sink.
        If you don't include one of the *--log* or *--log-service* flags,
        this command deletes a v2 sink.
        Deleting a sink does not affect log entries already exported
        through the deleted sink, and will not affect other sinks that are
        exporting the same log(s).
     """,
}

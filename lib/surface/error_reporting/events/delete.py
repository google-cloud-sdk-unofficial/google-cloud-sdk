# Copyright 2016 Google Inc. All Rights Reserved.
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

"""'error-reporting events delete' command."""

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
import googlecloudsdk.third_party.apis.clouderrorreporting.v1beta1 as cer_api


class Delete(base.Command):
  """Deletes all error events of the project."""

  @util.HandleHttpError
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.
    """
    client = self.context['clouderrorreporting_client_v1beta1']
    project = properties.VALUES.core.project.Get(required=True)

    if not console_io.PromptContinue(
        'Really delete all events for project \'%s\'?' % project):
      raise exceptions.ToolException('action canceled by user')

    client.projects.DeleteEvents(
        cer_api.ClouderrorreportingProjectsDeleteEventsRequest(
            projectName='projects/' + project))

    log.status.Print('All error events in the project were deleted.')
    log.status.Print()
    log.status.Print('It may take several minutes until '
                     'the deleted error events stop being visible.')

Delete.detailed_help = {
    'DESCRIPTION': """\
        {index}
        All error events which are stored for the given project are deleted and
        the error counters are reset to zero.
    """,
}

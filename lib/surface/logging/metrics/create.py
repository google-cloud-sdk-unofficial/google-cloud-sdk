# Copyright 2015 Google Inc. All Rights Reserved.
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

"""'logging metrics create' command."""

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Create(base.CreateCommand):
  """Creates a logs-based metric."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('metric_name', help='The name of the new metric.')
    parser.add_argument('description', help='The metric\'s description.')
    parser.add_argument('filter', help='The metric\'s filter expression.')

  def Collection(self):
    return 'logging.metrics'

  @util.HandleHttpError
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The created metric.
    """
    client = self.context['logging_client_v1beta3']
    messages = self.context['logging_messages_v1beta3']
    metric_filter = args.filter
    # This prevents a clash with the Cloud SDK --filter flag.
    args.filter = None
    project = properties.VALUES.core.project.Get(required=True)
    new_metric = messages.LogMetric(name=args.metric_name,
                                    description=args.description,
                                    filter=metric_filter)

    result = client.projects_metrics.Create(
        messages.LoggingProjectsMetricsCreateRequest(
            projectsId=project, logMetric=new_metric))
    log.CreatedResource(args.metric_name)
    return result


Create.detailed_help = {
    'DESCRIPTION': """\
        Creates a logs-based metric to count the number of log entries that
        match a filter expression.
        When creating a metric, the description field can be empty but the
        filter expression must not be empty.
    """,
    'EXAMPLES': """\
        To create a metric that counts the number of log entries with a
        severity level higher than WARNING, run:

          $ {command} high_severity_count "Number of high severity log entries" "metadata.severity > WARNING"

        Detailed information about filters can be found at:
        [](https://cloud.google.com/logging/docs/view/advanced_filters)
    """,
}

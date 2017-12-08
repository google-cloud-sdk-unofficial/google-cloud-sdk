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
"""Cloud Pub/Sub topics create command."""
import json
from googlecloudsdk.api_lib.pubsub import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import text
from googlecloudsdk.third_party.apitools.base.py import exceptions as api_ex


class Create(base.Command):
  """Creates one or more Cloud Pub/Sub topics."""

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    parser.add_argument('topic', nargs='+',
                        help='One or more topic names to create.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A 2-tuple of lists, one populated with the topic paths that were
      successfully created, the other one with the list of topic names
      that could not be created.
    """
    msgs = self.context['pubsub_msgs']
    pubsub = self.context['pubsub']

    succeeded = []
    failed = []

    for topic_name in args.topic:
      topic = msgs.Topic(name=util.TopicFormat(topic_name))
      try:
        succeeded.append(pubsub.projects_topics.Create(topic))
      except api_ex.HttpError as exc:
        failed.append((topic_name, json.loads(exc.content)['error']['message']))

    return succeeded, failed

  def Display(self, args, result):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    succeeded, failed = result
    successes = len(succeeded)
    failures = len(failed)

    if successes:
      fmt = 'list[title="{0} {1} created successfully"]'.format(
          successes, text.Pluralize(successes, 'topic'))
      resource_printer.Print([topic.name for topic in succeeded], fmt)

    if failures:
      fmt = 'list[title="{0} {1} failed"]'.format(
          failures, text.Pluralize(failures, 'topic'))
      resource_printer.Print(
          ['{0} (reason: {1})'.format(topic, desc) for topic, desc in failed],
          fmt)

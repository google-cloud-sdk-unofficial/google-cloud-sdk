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
"""Cloud Pub/Sub topics list command."""
from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import util


class List(base.ListCommand):
  """Lists Cloud Pub/Sub topics within a project.

  Lists all of the Cloud Pub/Sub topics that exist in a given project that
  match the given topic name filter.
  """

  detailed_help = {
      'EXAMPLES': """\
          To filter results by topic name (ie. only show topic 'mytopic'), run:

            $ {command} --filter=topicId:mytopic

          To combine multiple filters (with AND or OR), run:

            $ {command} --filter="topicId:mytopic AND topicId:myothertopic"

          To filter topics that match an expression:

            $ {command} --filter="topicId:mytopic_*"
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('yaml')
    parser.display_info.AddUriFunc(util.TopicUriFunc)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      Topic paths that match the regular expression in args.name_filter.
    """
    client = topics.TopicsClient()
    for topic in client.List(util.ParseProject(), page_size=args.page_size):
      yield util.ListTopicDisplayDict(topic)


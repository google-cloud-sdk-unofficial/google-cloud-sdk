# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Cloud Pub/Sub topics update command."""
from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.command_lib.util import labels_util
from googlecloudsdk.core import log


class Update(base.UpdateCommand):
  """Updates an existing Cloud Pub/Sub topic."""

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""

    parser.add_argument('topic',
                        help='Name of the topic to update.')

    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A serialized object (dict) describing the results of the operation.

    Raises:
      An HttpException if there was a problem calling the
      API topics.Patch command.
    """
    client = topics.TopicsClient()
    topic_ref = util.ParseTopic(args.topic)

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      original_topic = client.Get(topic_ref)
      labels = labels_diff.Apply(
          client.messages.Topic.LabelsValue, original_topic.labels)
    else:
      labels = None
    result = client.Patch(topic_ref, labels=labels)

    log.UpdatedResource(topic_ref.RelativeName(), kind='topic')
    return result

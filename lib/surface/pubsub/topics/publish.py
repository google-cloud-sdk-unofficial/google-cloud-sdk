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
"""Cloud Pub/Sub topics publish command."""
from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core.resource import resource_projector


class Publish(base.Command):
  """Publishes a message to the specified topic.

  Publishes a message to the specified topic name for testing and
  troubleshooting. Use with caution: all associated subscribers must be
  able to consume and acknowledge any message you publish, otherwise the
  system will continuously re-attempt delivery of the bad message for 7 days.

  ## EXAMPLES

  To publish messages in a batch to a specific Cloud Pub/Sub topic,
  run:

    $ {command} mytopic "Hello World!" --attribute KEY1=VAL1,KEY2=VAL2
  """

  @staticmethod
  def Args(parser):
    flags.AddTopicResourceArg(parser, 'to publish messages to.')
    flags.AddPublishMessageFlags(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      PublishResponse with the response of the Publish operation.

    Raises:
      topics.EmptyMessageException: if neither message or attributes is
        specified.
      topics.PublishOperationException: When something went wrong with the
        publish operation.
    """
    client = topics.TopicsClient()

    attributes = util.ParseAttributes(args.attribute, messages=client.messages)
    topic_ref = util.ParseTopic(args.topic)

    result = client.Publish(topic_ref, args.message_body, attributes)

    # We only allow to publish one message at a time, so do not return a
    # list of messageId.
    resource = resource_projector.MakeSerializable(result)
    resource['messageIds'] = result.messageIds[0]
    return resource

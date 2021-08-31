# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Implementation of create command for notifications."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base


@base.Hidden
class Create(base.Command):
  """Create a notification config on a bucket."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* creates a notification config on a bucket,
      establishing a flow of event notifications from Cloud Storage to a
      Cloud Pub/Sub topic. As part of creating this flow, it also verifies
      that the destination Cloud Pub/Sub topic exists, creating it if necessary,
      and verifies that the Cloud Storage bucket has permission to publish
      events to that topic, granting the permission if necessary.

      If a destination Cloud Pub/Sub topic is not specified with the `-t` flag,
      Cloud Storage chooses a topic name in the default project whose ID is
      the same as the bucket name. For example, if the default project ID
      specified is `default-project` and the bucket being configured is
      `gs://example-bucket`, the create command uses the Cloud Pub/Sub topic
      `projects/default-project/topics/example-bucket`.

      In order to enable notifications, your project's
      [Cloud Storage service agent](https://cloud.google.com/storage/docs/projects#service-accounts)
      must have the IAM permission "pubsub.topics.publish".
      This command checks to see if the destination Cloud Pub/Sub topic grants
      the service agent this permission.
      If not, the create command attempts to grant it.

      A bucket can have up to 100 total notification configurations and up to
      10 notification configurations set to trigger for a specific event.
      """,
      'EXAMPLES':
          """
      Begin sending notifications of all changes to the bucket
      `example-bucket` to the Cloud Pub/Sub topic
      `projects/default-project/topics/example-bucket`:

        $ {command} -f json gs://example-bucket

      The same as above, but specifies the destination topic ID
      `files-to-process` in the default project:

        $ {command} -f json -t files-to-process gs://example-bucket

      The same as above, but specifies a Cloud Pub/Sub topic belonging
      to the specific cloud project `example-project`:

        $ {command} -f json \
        -t projects/example-project/topics/files-to-process gs://example-bucket

      Create a notification config that only sends an event when a new object
      has been created:

        $ {command} -f json -e OBJECT_FINALIZE gs://example-bucket

      Create a topic and notification config that only sends an event when an
      object beginning with `photos/` is affected:

        $ {command} -p photos/ gs://example-bucket
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        help=('The url of the bucket for which the notification config'
              ' must be created.'))
    parser.add_argument(
        '-e',
        '--event-type',
        choices={
            'OBJECT_FINALIZE': 'An object has been created.',
            'OBJECT_METADATA_UPDATE': 'The metadata of an object has changed.',
            'OBJECT_DELETE': 'An object has been permanently deleted.',
            'OBJECT_ARCHIVE': ('A live version of an object has'
                               ' become a noncurrent version.'),
        },
        help=textwrap.dedent("""\
            Specify an event type filter for this notification config.
            Cloud Storage only sends notifications of this type.
            You may specify this parameter multiple times to allow multiple
            event types. If not specified,
            Cloud Storage sends notifications for all event types."""))
    parser.add_argument(
        '-f',
        '--payload-format',
        choices={
            'json': 'Payload matches the object metadata for the JSON API.',
            'none': 'No payload.',
        },
        help=textwrap.dedent("""\
            Specifies the payload format of notification messages.
            Notification details are available in the message attributes."""),
        required=True)
    parser.add_argument(
        '-m',
        '--metadata',
        help=textwrap.dedent("""\
            Specifies a key:value attribute that is appended to the set of
            attributes sent to Cloud Pub/Sub for all events associated with
            this notification config. You may specify this parameter multiple
            times to set multiple attributes."""))
    parser.add_argument(
        '-p',
        '--prefix',
        help=textwrap.dedent("""\
            Specifies a prefix path filter for this notification config.
            Cloud Storage only sends notifications for objects in this bucket
            whose names begin with the specified prefix."""))
    parser.add_argument(
        '-s',
        '--skip',
        help=textwrap.dedent("""\
            Skips creation and permission assignment of the Cloud Pub/Sub topic.
            This is useful if the caller does not have permission to access
            the topic in question, or if the topic already exists and has the
            appropriate publish permission assigned."""))
    parser.add_argument(
        '-t',
        '--topic',
        help=textwrap.dedent("""\
            The Cloud Pub/Sub topic to which notifications should be sent.
            If not specified, this command chooses a topic whose project is
            your default project and whose ID is the same as the
            Cloud Storage bucket name."""))

  def Run(self, args):
    raise NotImplementedError

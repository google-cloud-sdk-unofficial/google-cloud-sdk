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
"""Command to delete notification configs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Delete(base.DeleteCommand):
  """Delete notification configs from a bucket."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* deletes notification configs from a bucket. If a notification
      config name is passed as a parameter, that notification config alone
      is deleted. If a bucket name is passed, all notification configs
      associated with that bucket are deleted.

      Cloud Pub/Sub topics associated with this notification config
      are not deleted by this command. Those must be deleted separately,
      for example with the gcloud command gcloud beta pubsub topics delete.

      Object Change Notification subscriptions cannot be deleted with this
      command. For that, see the command gsutil notification stopchannel.
      """,
      'EXAMPLES':
          """
      Delete a single notification config (with ID 3) in the
      bucket `example-bucket`:

        $ {command} projects/_/buckets/example-bucket/notificationConfigs/3

      Delete all notification configs in the bucket `example-bucket`:

        $ {command} gs://example-bucket
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'urls',
        nargs='+',
        help='Specifies the notification config names or a buckets.')

  def Run(self, args):
    raise NotImplementedError

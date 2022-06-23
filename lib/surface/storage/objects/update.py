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
"""Implementation of objects update command for updating object settings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags


@base.Hidden
class Update(base.Command):
  """Update Cloud Storage objects."""

  detailed_help = {
      'DESCRIPTION':
          """
      Update Cloud Storage objects.
      """,
      'EXAMPLES':
          """

      Update a Google Cloud Storage object's custom-metadata:

        $ *{command}* gs://bucket/my-object --custom-metadata=key1=value1,key2=value2

      Set a temporary hold on JPG images:

        $ *{command}* gs://bucket/*.jpg --temporary-hold

       You can also provide a precondition on an object's metageneration in
       order to avoid potential race conditions:

        $ *{command}* gs://bucket/*.jpg --temporary-hold --if-metageneration-match=123456789
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url', nargs='+', help='Specifies URL of objects to update.')
    parser.add_argument(
        '--event-based-hold',
        action=arg_parsers.StoreTrueFalseAction,
        help='Enables or disables an event-based hold on objects.')
    parser.add_argument(
        '-p',
        '--preserve-acl',
        action='store_true',
        default=True,
        help='Preserves ACLs when copying in the cloud. This feature is'
        ' supported for only Google Cloud Storage and requires OWNER access'
        " to all copied objects. To use the destination bucket's default policy"
        ' (necessary for uniform bucket-level access), use --no-preserve-acl.')
    parser.add_argument(
        '--temporary-hold',
        action=arg_parsers.StoreTrueFalseAction,
        help='Enables or disables a temporary hold on objects.')
    flags.add_precondition_flags(parser)
    flags.add_object_metadata_flags(parser)

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError

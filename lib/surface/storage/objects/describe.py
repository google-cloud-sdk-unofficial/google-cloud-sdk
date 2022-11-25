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
"""Implementation of objects describe command for getting info on objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.core.resource import resource_projector


class Describe(base.DescribeCommand):
  """Describe a Cloud Storage object."""

  detailed_help = {
      'DESCRIPTION':
          """
      Describe a Cloud Storage object.
      """,
      'EXAMPLES':
          """

      Describe a Google Cloud Storage object with the url
      "gs://bucket/my-object":

        $ {command} gs://bucket/my-object

      Describe object with JSON formatting, only returning the "name" key:

        $ {command} gs://bucket/my-object --format="json(name)"
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('url', help='Specifies URL of object to describe.')
    flags.add_encryption_flags(parser, command_only_reads_data=True)

  def Run(self, args):
    encryption_util.initialize_key_store(args)
    if wildcard_iterator.contains_wildcard(args.url):
      raise errors.InvalidUrlError(
          'Describe does not accept wildcards because it returns a single'
          ' resource. Please use the `ls` or `objects list` command for'
          ' retrieving multiple resources.')
    url = storage_url.storage_url_from_string(args.url)
    errors.raise_error_if_not_cloud_object(args.command_path, url)
    object_resource = api_factory.get_api(url.scheme).get_object_metadata(
        url.bucket_name,
        url.object_name,
        fields_scope=cloud_api.FieldsScope.FULL)
    # MakeSerializable will omit all the None values.
    return resource_projector.MakeSerializable(object_resource.metadata)

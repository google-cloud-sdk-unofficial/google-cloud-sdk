# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Implementation of objects list command for getting info on objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.core.resource import resource_projector


class List(base.ListCommand):
  """Lists Cloud Storage objects."""

  detailed_help = {
      'DESCRIPTION':
          """
      List Cloud Storage objects.

      Bucket URLs like "gs://bucket" will match all the objects inside a bucket,
      but "gs://b*" will error because it matches a list of buckets.
      """,
      'EXAMPLES':
          """

      List all objects in bucket "my-bucket":

        $ {command} gs://my-bucket

      List all objects in bucket beginning with "o":

        $ {command} gs://my-bucket/o*

      List all objects in bucket with JSON formatting, only returning the
      value of the "name" metadata field:

        $ {command} gs://my-bucket --format="json(name)"
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'urls', nargs='+', help='Specifies URL of objects to list.')

  def Run(self, args):
    urls = []
    for url_string in args.urls:
      url = storage_url.storage_url_from_string(url_string)
      if url.is_provider() or (url.is_bucket() and
                               wildcard_iterator.contains_wildcard(
                                   url.bucket_name)):
        raise errors.InvalidUrlError(
            'URL does not match objects: {}'.format(url_string))
      if url.is_bucket():
        # Convert gs://bucket to gs://bucket/* to retrieve objects.
        urls.append(url.join('*'))
      else:
        urls.append(url)

    for url in urls:
      for resource in wildcard_iterator.get_wildcard_iterator(
          url.url_string,
          all_versions=True,
          fields_scope=cloud_api.FieldsScope.FULL):
        if isinstance(resource, resource_reference.ObjectResource):
          # MakeSerializable will omit all the None values.
          yield resource_projector.MakeSerializable(
              resource.get_displayable_object_data())

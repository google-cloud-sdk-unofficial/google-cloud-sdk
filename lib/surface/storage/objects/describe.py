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

from googlecloudsdk.calliope import base


@base.Hidden
class Describe(base.ListCommand):
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

        $ *{command}* gs://bucket/my-object

      Desribe object with JSON formatting, only returning the "name" key:

        $ *{command}* gs://bucket/my-object --format=json(name)
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('url', help='Specifies URL of object to describe.')

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError

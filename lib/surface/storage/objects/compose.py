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
"""Implementation of objects compose command for Cloud Storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base


@base.Hidden
class Compose(base.Command):
  """Concatenate a sequence of objects into a new composite object."""

  detailed_help = {
      'DESCRIPTION':
          """
      {command} creates a new object whose content is the concatenation
      of a given sequence of source objects in the same bucket.
      For more information, please see:
      [composite objects documentation](https://cloud.google.com/storage/docs/composite-objects).

      There is a limit (currently 32) to the number of components
      that can be composed in a single operation.
      """,
      'EXAMPLES':
          """
      The following command creates a new object `target.txt` by concatenating
      `a.txt` and `b.txt`:

        $ {command} gs://bucket/a.txt gs://bucket/b.txt gs://bucket/target.txt
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'source',
        nargs='+',
        help=textwrap.dedent("""\
            The list of source objects that will be concatenated into a
            single object."""))
    parser.add_argument('destination', help='The destination object.')

  def Run(self, args):
    raise NotImplementedError

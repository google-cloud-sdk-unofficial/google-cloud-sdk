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
"""Implementation of Unix-like cat command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base


@base.Hidden
class Cat(base.Command):
  """Outputs the contents of one or more URLs to stdout."""

  detailed_help = {
      'DESCRIPTION':
          """
      The cat command outputs the contents of one or more URLs to stdout. While
      the cat command does not compute a checksum, it is otherwise equivalent to
      doing:

        $ gcloud alpha storage cp url... -

      (The final '-' causes gcloud to stream the output to stdout.)
      """,
      'EXAMPLES':
          """

      The following command writes all text files in a bucket to stdout:

        $ {command} gs://bucket/*.txt

      The following command outputs a short header describing file.txt, along
      with its contents:

        $ {command} -d gs://my-bucket/file.txt

      The following command outputs bytes 256-939 of file.txt:

        $ {command} -r 256-939 gs://my-bucket/file.txt

      The following command outputs the last 5 bytes of file.txt:

        $ {command} -r -5 gs://my-bucket/file.txt
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('url', nargs='+', help='The url of objects to list.')
    parser.add_argument(
        '-d',
        '--description',
        action='store_true',
        help='Prints a short description before each object.')
    parser.add_argument(
        '-r',
        '--range',
        help=textwrap.dedent("""\
            Causes gcloud storage to output just the specified byte range of
            the object. Ranges are can be of these forms:
            `start-end` (e.g., `-r 256-5939`), `start-` (e.g., `-r 256-`),
            `-numbytes` (e.g., `-r -5`)

            When offsets start at 0, start-end means to return bytes start
            through end (inclusive), start- means to return bytes start through
            the end of the object, and -numbytes means to return the last
            numbytes of the object."""))

  def Run(self, args):
    raise NotImplementedError

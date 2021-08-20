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
"""Implementation of delete command for HMAC."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base


class Delete(base.Command):
  """Remove a service account HMAC."""

  detailed_help = {
      'DESCRIPTION': """
       *{command}* permanently deletes the specified HMAC key. Note that keys
       must be updated to be in the ``INACTIVE'' state before they can be
       deleted.
      """,
      'EXAMPLES': """
       To delete a specific HMAC key:

         $ {command} GOOG56JBMFZX6PMPTQ62VD2

       To be prompted for HMAC keys to delete:

         $ {command}
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'hmac',
        nargs='*',
        help=textwrap.dedent("""\
            Zero or more HMAC keys to remove. If none are given, a prompt will
            provide a choice of inactive HMAC keys to remove."""))

  def Run(self, args):
    raise NotImplementedError

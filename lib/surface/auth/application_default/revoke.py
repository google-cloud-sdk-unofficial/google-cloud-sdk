# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Revoke credentials being used by Application Default Credentials."""

from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core.credentials import store as c_store


class Revoke(base.Command):
  """Revoke Application Default Credentials.

  Revokes Application Default Credentials that have been set up by commands
  in the Google Cloud SDK. The credentials are revoked remotely only if
  they are user credentials. In all cases, the file storing the credentials is
  removed.

  This does not effect any credentials set up through other means,
  for example credentials referenced by the Application Default Credentials
  environment variable or service account credentials that are active on
  a Google Compute Engine virtual machine.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--brief', action='store_true',
        help='Minimal user output.')

  @c_exc.RaiseToolExceptionInsteadOf(c_store.Error)
  def Run(self, args):
    """Revoke Application Default Credentials."""

    auth_util.RevokeCredsInWellKnownFile(args.brief)

    return ''

  def Display(self, unused_args, result):
    pass

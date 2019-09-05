# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Create a new secret."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.secrets import args as secrets_args
from googlecloudsdk.command_lib.secrets import log as secrets_log
from googlecloudsdk.command_lib.secrets import util as secrets_util
from googlecloudsdk.command_lib.util.args import labels_util


class Create(base.CreateCommand):
  r"""Create a new secret.

  Create a secret with the given name and creates a secret version with the
  given data, if any. If a secret already exists with the given name, this
  command will return an error.

  ## EXAMPLES

  Create a secret without creating any versions:

    $ {command} my-secret --locations=us-central1

  Create a new secret named 'my-secret' in 'us-central1' with data from a file:

    $ {command} my-secret --data-file=/tmp/secret --locations=us-central1

  Create a new secret named 'my-secret' in 'us-central1' and 'us-east1' with
  the value "s3cr3t":

    $ echo "s3cr3t" | {command} my-secret --data-file=- \
        --locations=us-central1,us-east1
  """

  EMPTY_DATA_FILE_MESSAGE = (
      'The value provided for --data-file is the empty string. This can happen '
      'if you pass or pipe a variable that is undefined. Please verify that '
      'the --data-file flag is not the empty string. If you are not providing '
      'secret data, omit the --data-file flag.')

  @staticmethod
  def Args(parser):
    secrets_args.AddSecret(
        parser, purpose='to create', positional=True, required=True)
    secrets_args.AddLocations(parser, resource='secret', required=True)
    secrets_args.AddDataFile(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    messages = secrets_api.GetMessages()
    secret_ref = args.CONCEPTS.secret.Parse()
    data = secrets_util.ReadFileOrStdin(args.data_file)
    labels = labels_util.ParseCreateArgs(args, messages.Secret.LabelsValue)

    # Differentiate between the flag being provided with an empty value and the
    # flag being omitted. See b/138796299 for info.
    if args.data_file == '':  # pylint: disable=g-explicit-bool-comparison
      raise exceptions.ToolException(self.EMPTY_DATA_FILE_MESSAGE)

    # Create the secret
    response = secrets_api.Secrets().Create(
        secret_ref, labels=labels, locations=args.locations)

    # Create the version if data was given
    if data:
      version = secrets_api.Secrets().SetData(secret_ref, data)
      version_ref = secrets_args.ParseVersionRef(version.name)
      secrets_log.Versions().Created(version_ref)
    else:
      secrets_log.Secrets().Created(secret_ref)

    return response

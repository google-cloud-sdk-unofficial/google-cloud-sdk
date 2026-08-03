# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Enable managed rotation for a secret."""


from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.secrets import args as secrets_args


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class EnableManagedRotation(base.Command):
  r"""Enable managed rotation for a secret.

  Enable managed rotation for the specified secret. This command is used
  for the initial setup of managed rotation, currently supporting Cloud SQL
  single-user credentials.

  ## EXAMPLES

  To enable managed rotation for a secret `my-secret` targeting a Cloud SQL
  instance:

    $ {command} my-secret --location=us-central1
    --instance-id=my-project:my-instance --username=db-user

  To enable managed rotation and set an initial password:

    $ {command} my-secret --location=us-central1
    --instance-id=my-project:my-instance --username=db-user
    --password="s3cr3tPassword"
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddSecret(
        parser,
        purpose='to enable managed rotation for',
        positional=True,
        required=True,
    )
    secrets_args.AddLocation(
        parser, purpose='of the secret', hidden=False, required=True
    )

    secrets_args.AddCloudSqlCredentialsArgs(parser)

  def Run(self, args):
    api_version = secrets_api.GetApiFromTrack(self.ReleaseTrack())
    messages = secrets_api.GetMessages(version=api_version)
    secret_ref = args.CONCEPTS.secret.Parse()

    credentials = messages.CloudSQLSingleUserCredentials(
        instanceId=args.instance_id,
        username=args.username,
        password=args.password,
    )

    response = secrets_api.Secrets(
        api_version=api_version
    ).EnableManagedRotation(
        secret_ref,
        cloud_sql_single_user_credentials=credentials,
        location=args.location,
    )
    return response

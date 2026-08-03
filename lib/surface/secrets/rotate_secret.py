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
class RotateSecret(base.Command):
  r"""Rotate a secret.

  Rotate a secret and add a new version.

  ## EXAMPLES

  Rotate a secret named `my-secret` in `us-central1`:

    $ {command} my-secret --location=us-central1
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddSecret(
        parser,
        purpose='to rotate secret and add a new version',
        positional=True,
        required=True,
    )
    secrets_args.AddLocation(
        parser, purpose='of the secret', hidden=False, required=True
    )

  def Run(self, args):
    api_version = secrets_api.GetApiFromTrack(self.ReleaseTrack())
    secret_ref = args.CONCEPTS.secret.Parse()
    response = secrets_api.Secrets(api_version=api_version).RotateSecret(
        secret_ref,
        location=args.location,
    )
    return response

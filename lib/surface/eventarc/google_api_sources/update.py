# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command to update the specified Google API source."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import google_api_sources
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import flags
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To update the Google API source `my-google-api-source` in location `us-central1` with destination message bus `my-message-bus`, run:

          $ {command} my-google-api-source --location=us-central1 --destination-message-bus=my-message-bus

        To update the Google API source `my-google-api-source` in location `us-central1` with `INFO` level logging, run:

          $ {command} my-google-api-source --location=us-central1 --logging-config=INFO

        To update the Google API source `my-google-api-source` in location `us-central1` with a Cloud KMS CryptoKey, run:

          $ {command} my-google-api-source --location=us-central1 --crypto-key=projects/PROJECT_ID/locations/KMS_LOCATION/keyRings/KEYRING/cryptoKeys/KEY

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class Update(base.UpdateCommand):
  """Update an Eventarc Google API source."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddUpdateGoogleApiSourceResourceArgs(parser)
    flags.AddLoggingConfigArg(
        parser, 'The logging config of the Google API source.'
    )
    flags.AddCryptoKeyArg(parser, with_clear=True)
    flags.AddLabelsArg(
        parser, help_text='Labels to apply to the Google API source.'
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run the update command."""
    client = google_api_sources.GoogleApiSourceClientV1()
    google_api_source_ref = args.CONCEPTS.google_api_source.Parse()

    log.debug(
        'Updating Google API source {} for project {} in location {}'.format(
            google_api_source_ref.googleApiSourcesId,
            google_api_source_ref.projectsId,
            google_api_source_ref.locationsId,
        )
    )

    update_mask = client.BuildUpdateMask(
        destination=args.IsSpecified('destination_message_bus'),
        logging_config=args.IsSpecified('logging_config'),
        crypto_key=args.IsSpecified('crypto_key'),
        clear_crypto_key=args.clear_crypto_key,
        labels=args.IsSpecified('labels'),
    )

    operation = client.Patch(
        google_api_source_ref,
        client.BuildGoogleApiSource(
            google_api_source_ref=google_api_source_ref,
            destination_ref=args.CONCEPTS.destination_message_bus.Parse(),
            logging_config=args.logging_config,
            crypto_key_name=args.crypto_key,
            labels=args.labels,
        ),
        update_mask,
    )

    if args.async_:
      return operation
    return client.WaitFor(operation, 'Updating', google_api_source_ref)

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
"""Cloud Speech-to-text recognizers update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml.speech import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml.speech import flag_validations
from googlecloudsdk.command_lib.ml.speech import flags_v2
from googlecloudsdk.core import log


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Update a Speech-to-text recognizer."""

  def ValidateUpdateRecognizerFlags(self, args):
    """Validates update flags."""
    flag_validations.ValidateLocation(args)
    flag_validations.ValidateDecodingConfig(args)

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags_v2.AddAllFlagsToParser(parser)

  def Run(self, args):
    recognizer = args.CONCEPTS.recognizer.Parse()

    speech_client = client.SpeechV2Client()
    is_async = args.async_

    self.ValidateUpdateRecognizerFlags(args)

    update_mask = []

    recognition_config, features, update_mask = (
        speech_client.SeparateArgsForRecognizeCommand(
            args, record_updates=True, update_mask=update_mask
        )
    )

    if args.model is not None:
      recognition_config.model = args.model
      update_mask.append('default_recognition_config.model')
    if args.language_codes is not None:
      recognition_config.languageCodes = args.language_codes
      update_mask.append('default_recognition_config.language_codes')

    operation = speech_client.UpdateRecognizer(
        recognizer,
        args.display_name,
        args.model,
        args.language_codes,
        recognition_config,
        features,
        update_mask,
    )

    if is_async:
      log.UpdatedResource(
          operation.name, kind='speech recognizer', is_async=True
      )
      return operation

    resource = speech_client.WaitForRecognizerOperation(
        location=recognizer.Parent().Name(),
        operation_ref=speech_client.GetOperationRef(operation),
        message='waiting for recognizer [{}] to be updated'.format(
            recognizer.RelativeName()
        ),
    )
    log.UpdatedResource(resource.name, kind='speech recognizer')

    return resource

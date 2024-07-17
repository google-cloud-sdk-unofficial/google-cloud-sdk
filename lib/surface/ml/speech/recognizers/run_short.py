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
"""Cloud Speech-to-text recognizers run short audio command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import os
from googlecloudsdk.api_lib.ml.speech import client
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.ml.speech import flags_v2


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RunShort(base.Command):
  """Get transcripts of short (less than 60 seconds) audio from an audio file."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags_v2.AddRunShortFlagsToParser(parser)

  def Run(self, args):
    resource = args.CONCEPTS.recognizer.Parse()
    speech_client = client.SpeechV2Client()
    if (
        args.encoding is not None
        and args.encoding not in client.ENCODING_OPTIONS
    ):
      raise exceptions.InvalidArgumentException(
          '--encoding',
          '[--encoding] must be set to LINEAR16, MULAW, ALAW, or AUTO.',
      )

    if args.encoding is not None and args.encoding != 'AUTO':
      if args.sample_rate is None:
        raise exceptions.InvalidArgumentException(
            '--sample-rate',
            (
                '[--sample-rate] must be specified when configuring explicit'
                ' encoding option options LINEAR16, MULAW, or ALAW.'
            ),
        )
      if args.audio_channel_count is None:
        raise exceptions.InvalidArgumentException(
            '--audio-channel-count',
            (
                '[--audio-channel-count] must be specified when configuring'
                ' explicit encoding options LINEAR16, MULAW, or ALAW.'
            ),
        )
      if not os.path.isfile(
          args.audio
      ) and not storage_util.ObjectReference.IsStorageUrl(args.audio):
        raise exceptions.InvalidArgumentException(
            '--audio',
            'Invalid audio source [{}]. The source must either be a local '
            'path or a Google Cloud Storage URL '
            '(such as gs://bucket/object).'.format(args.audio),
        )

    return speech_client.RunShort(
        resource,
        args.audio,
        args.model,
        args.language_codes,
        args.encoding,
        args.sample_rate,
        args.audio_channel_count,
    )

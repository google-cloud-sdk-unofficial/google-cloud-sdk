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
"""Contains the properties for the 'functions' section."""

from googlecloudsdk.core.properties.completers import COMPLETERS
from googlecloudsdk.core.properties.types import _Section


class _SectionFunctions(_Section):
  """Contains the properties for the 'functions' section."""

  def __init__(self):
    super(_SectionFunctions, self).__init__('functions')
    self.region = self._Add(
        'region',
        default='us-central1',
        help_text=(
            'Default region to use when working with Cloud Functions resources.'
            ' When a `--region` flag is required but not provided, the command'
            ' will fall back to this value, if set. To see valid choices, run'
            ' `gcloud beta functions regions list`.'
        ),
        completer=COMPLETERS['FunctionsLocationsCompleter'],
    )
    self.gen2 = self._AddBool(
        'gen2',
        default=False,
        help_text=(
            'Default environment to use when working with Cloud Functions'
            ' resources. When neither `--gen2` nor `--no-gen2` is provided, the'
            ' decision of whether to use Generation 2 falls back to this value'
            ' if set.'
        ),
    )
    self.v2 = self._AddBool(
        'v2',
        default=False,
        hidden=True,
        help_text=(
            'DEPRECATED. Use `functions/gen2` instead. '
            'This property will be removed in a future release.'
        ),
    )

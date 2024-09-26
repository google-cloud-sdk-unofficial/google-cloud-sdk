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
"""The command lists the models in Model Garden that support deployment."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class List(base.Command):
  """List the deploy-able model names in Model Garden."""

  def Run(self, args):
    # This is the initial list that we support. In the next phase, the list
    # will be fetched from the server.
    supported_models = [
        # Gemma 2
        'google/gemma2/gemma-2-2b-it',
        'google/gemma2/gemma-2-2b',
        'google/gemma2/gemma-2-9b-it',
        'google/gemma2/gemma-2-9b',
        'google/gemma2/gemma-2-27b-it',
        'google/gemma2/gemma-2-27b',
        # Gemma 1.1
        'google/gemma/gemma-1.1-2b-it',
        'google/gemma/gemma-1.1-7b-it',
        # Gemma
        'google/gemma/gemma-2b-it',
        'google/gemma/gemma-2b',
        'google/gemma/gemma-7b-it',
        'google/gemma/gemma-7b',
        # Code Gemma
        'google/codegemma/codegemma-2b',
        'google/codegemma/codegemma-7b-it',
        'google/codegemma/codegemma-7b',
        # Llama 3.1
        'meta/llama3_1/meta-llama-3.1-8b-instruct',
        'meta/llama3_1/meta-llama-3.1-8b',
        'meta/llama3_1/meta-llama-3.1-70b-instruct',
        'meta/llama3_1/meta-llama-3.1-70b',
        'meta/llama3_1/meta-llama-3.1-405b-instruct-fp8',
        'meta/llama3_1/meta-llama-3.1-405b-fp8',
        # Llama 3
        'meta/llama3/meta-llama-3-8b-instruct',
        'meta/llama3/meta-llama-3-8b',
        'meta/llama3/meta-llama-3-70b-instruct',
        'meta/llama3/meta-llama-3-70b',
        # Llama 2
        'meta/llama2/llama-2-7b-chat',
        'meta/llama2/llama-2-7b',
        'meta/llama2/llama-2-13b-chat',
        'meta/llama2/llama-2-13b',
        'meta/llama2/llama-2-70b-chat',
        'meta/llama2/llama-2-70b',
        # Llama Guard
        'meta/llama-guard/llama-guard-3-8b',
        # Mistral
        'mistral-ai/mistral/mistral-7b-instruct-v0.1',
        'mistral-ai/mistral/mistral-7b-v0.1',
        'mistral-ai/mistral/mistral-7b-instruct-v0.2',
        'mistral-ai/mistral/mistral-7b-instruct-v0.3',
        'mistral-ai/mistral/mistral-7b-v0.3',
        'mistral-ai/mistral/mistral-nemo-instruct-2407',
        'mistral-ai/mistral/mistral-nemo-base-2407',
        # Mixtral
        'mistral-ai/mixtral/mixtral-8x7b-instruct-v0.1',
        'mistral-ai/mixtral/mixtral-8x7b-v0.1',
        'mistral-ai/mixtral/mixtral-8x22b-instruct-v0.1',
        'mistral-ai/mixtral/mixtral-8x22b-v0.1',
    ]
    return '\n'.join(supported_models)

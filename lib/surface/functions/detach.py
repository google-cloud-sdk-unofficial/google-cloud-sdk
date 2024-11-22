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
"""Detach GCF 2nd gen function from GCF and make it a native Cloud run function."""

from googlecloudsdk.api_lib.functions.v2 import client as client_v2
from googlecloudsdk.api_lib.functions.v2 import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DetachAlpha(base.Command):
  """Detach a GCF 2nd gen function from GCF and make it a native Cloud run function."""

  @staticmethod
  def Args(parser):
    flags.AddFunctionResourceArg(parser, 'to detach')

  def Run(self, args):
    client = client_v2.FunctionsClient(self.ReleaseTrack())
    function_ref = args.CONCEPTS.name.Parse()
    function_name = function_ref.RelativeName()
    message = (
        f'WARNING: This will detach function {function_name} from Cloud'
        ' Functions permantly. After detach, you cannot manage the function'
        ' with the Cloud Functions API or `gcloud functions <command>`. You'
        ' should use the Cloud Run API or `gcloud run <command>` instead.'
    )
    if console_io.CanPrompt():
      console_io.PromptContinue(message, default=True, cancel_on_no=True)

    operation = client.DetachFunction(function_name)
    description = 'Detaching function from Cloud Functions.'
    api_util.WaitForOperation(
        client.client, client.messages, operation, description
    )

    log.status.Print()
    log.status.Print(
        f'Function {function_name} has been detached successfully!'
    )

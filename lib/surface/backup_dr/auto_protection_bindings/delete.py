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
"""Command to delete an auto protection policy binding."""

from googlecloudsdk.api_lib.backupdr import auto_protection_bindings
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.backupdr import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
class Delete(base.DeleteCommand):
  """Delete a Backup and DR auto-protection policy binding."""

  detailed_help = {
      'DESCRIPTION': 'Delete a Backup and DR auto-protection policy binding.',
      'EXAMPLES': """\
        To delete a Backup and DR auto-protection policy binding, run:

          $ {command} my-binding-id --auto-protection-policy=my-auto-protection-policy --location=us-central1
        """,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddAutoProtectionPolicyBindingResourceArg(
        parser,
        'The auto-protection policy binding to delete.',
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    api_version = util.GetApiVersion(self.ReleaseTrack())
    binding_ref = args.CONCEPTS.auto_protection_policy_binding.Parse()

    client = auto_protection_bindings.AutoProtectionBindingsClient(
        api_version=api_version
    )
    operation = client.InitiateDelete(binding_ref)

    if args.async_:
      log.status.Print(
          'Delete initiated for auto protection policy binding [{}].'.format(
              binding_ref.Name()))
      return operation

    client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='Initiating deletion for auto protection policy binding [{}]'
        .format(binding_ref.Name()),
        has_result=False)

    log.status.Print(
        'Delete initiated for auto protection policy binding [{}]. '
        'The binding will be removed after its backup plan associations '
        'are deleted.'.format(binding_ref.Name()))

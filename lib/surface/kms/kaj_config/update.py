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
"""Update the KeyAccessJustificationsPolicyConfig."""

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import maps


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  r"""Updates the KeyAccessJustificationsPolicyConfig of an organization/folder/project.

  {command} can be used to update the KeyAccessJustificationsPolicyConfig of an
  organization/folder/project. This command includes adding/removing allowed
  KAJ enums to/from a KeyAccessJustificationsPolicyConfig. Clearing all allowed
  KAJ enums is also
  supported. Note that an empty KeyAccessJustificationsPolicyConfig is an
  "allow-all" policy, i.e.
  any KAJ enums are allowed in this kajPolicyConfig.

  For details about KAJ enums, please check
  https://cloud.google.com/assured-workloads/key-access-justifications/docs/justification-codes

  Note that on successful completion, this command does not display the updated
  resource by default. To view the updated KeyAccessJustificationsPolicyConfig,
  use the --format flag, for example, --format=yaml.

  ## EXAMPLES

  The following command will set the
  KeyAccessJustificationsPolicyConfig of
  folders/123 with CUSTOMER_INITIATED_ACCESS:

  $ {command} --folder=123
  --allowed-access-reasons=customer-initiated-access

  To update the policy for project 'abc' with CUSTOMER_INITIATED_ACCESS and
  display the updated configuration as YAML, run:

  $ {command} --project=abc
  --allowed-access-reasons=customer-initiated-access --format=yaml

  The following command resets the KeyAccessJustificationsPolicyConfig
  in organizations/123 to a default value (allow-all access reasons).

  $ {command} --organizations=123 --reset-kaj-policy-config
  """

  @staticmethod
  def Args(parser):
    flags.AddKajPolicyParentFlag(parser)
    flags.AddKajPolicyUpdateFlag(parser)

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    if args.reset_kaj_policy_config:
      new_kaj_default_policy = None
    elif args.allowed_access_reasons is not None:
      allowed_reasons_list = args.allowed_access_reasons
      if not allowed_reasons_list:
        raise exceptions.ArgumentError(
            '--allowed-access-reasons cannot be empty. At least one access'
            ' reason is required.'
        )
      allowed_reasons_enums = {
          maps.ACCESS_REASON_MAPPER.GetEnumForChoice(r)
          for r in args.allowed_access_reasons
      }
      new_kaj_default_policy = messages.KeyAccessJustificationsPolicy(
          allowedAccessReasons=list(allowed_reasons_enums)
      )
    else:
      return

    if args.organization:
      return client.organizations.UpdateKajPolicyConfig(
          messages.CloudkmsOrganizationsUpdateKajPolicyConfigRequest(
              name='organizations/{0}/kajPolicyConfig'.format(
                  args.organization
              ),
              updateMask='defaultKeyAccessJustificationPolicy',
              keyAccessJustificationsPolicyConfig=messages.KeyAccessJustificationsPolicyConfig(
                  name='organizations/{0}/kajPolicyConfig'.format(
                      args.organization
                  ),
                  defaultKeyAccessJustificationPolicy=new_kaj_default_policy,
              ),
          )
      )
    elif args.folder:
      return client.folders.UpdateKajPolicyConfig(
          messages.CloudkmsFoldersUpdateKajPolicyConfigRequest(
              name='folders/{0}/kajPolicyConfig'.format(args.folder),
              updateMask='defaultKeyAccessJustificationPolicy',
              keyAccessJustificationsPolicyConfig=messages.KeyAccessJustificationsPolicyConfig(
                  name='folders/{0}/kajPolicyConfig'.format(args.folder),
                  defaultKeyAccessJustificationPolicy=new_kaj_default_policy,
              ),
          )
      )
    elif args.project:
      return client.projects.UpdateKajPolicyConfig(
          messages.CloudkmsProjectsUpdateKajPolicyConfigRequest(
              name='projects/{0}/kajPolicyConfig'.format(args.project),
              updateMask='defaultKeyAccessJustificationPolicy',
              keyAccessJustificationsPolicyConfig=messages.KeyAccessJustificationsPolicyConfig(
                  name='projects/{0}/kajPolicyConfig'.format(args.project),
                  defaultKeyAccessJustificationPolicy=new_kaj_default_policy,
              ),
          )
      )
    raise exceptions.ArgumentError(
        'Require an organization/folder/project ID of the parent of'
        ' KeyAccessJustificationsPolicyConfig.'
    )

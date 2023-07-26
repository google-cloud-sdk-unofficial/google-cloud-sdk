# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Sets configuration properties of the Policy Controller component deployments."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import util as fleet_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import deployment_configs as deployment
from googlecloudsdk.core import exceptions


@calliope_base.Hidden
@calliope_base.ReleaseTracks(
    calliope_base.ReleaseTrack.ALPHA, calliope_base.ReleaseTrack.BETA
)
class Set(base.UpdateCommand):
  """Sets configuration of the Policy Controller components.

  Customizes on-cluster components of Policy Controller. Supported
  properties may be set with this command, or removed with 'remove'. These
  components are managed as individual kubernetes deployments (e.g. 'admission')
  in the gatekeeper-system namespace.

  When setting cpu or memory limits and requests, Kubernetes-standard resource
  units are used.

  All properties set using this command will overwrite previous properties, with
  the exception of tolerations which can only be added, and any number may be
  added. To edit a toleration, use 'remove' to first delete it, and then 'set'
  the desired toleration.

  ## EXAMPLES

  To set the replica count for a component:

    $ {command} admission replica-count 3

  To set the replica count for a component across all fleet memberships:

    $ {command} admission replica-count 3 --all-memberships

  To set a toleration with key 'my-key' on a component (which is an 'Exists'
  operator):

    $ {command} admission toleration my-key

  To set a toleration with key 'my-key' and 'my-value' on a component (which is
  an 'Equal' operator):

    $ {command} admission toleration my-key=my-value

  To set a toleration with key 'my-key' and 'my-value' on a component, along
  with the effect 'NoSchedule' (which is an 'Equal' operator):

    $ {command} admission toleration my-key=my-value --effect=NoSchedule

  To set a memory limit:

    $ {command} audit memory-limit 4Gi

  To set a memory request:

    $ {command} mutation memory-request 2Gi

  To set a cpu limit:

    $ {command} admission cpu-limit 500m

  To set a cpu request:

    $ {command} audit cpu-request 250m
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'deployment',
        choices=deployment.G8R_COMPONENTS,
        help=(
            'The PolicyController deployment component (e.g. "admission", '
            ' "audit" or "mutation") upon which to set configuration.'
        ),
    )
    parser.add_argument(
        'property',
        choices=deployment.SUPPORTED_PROPERTIES,
        help='Property to be set.',
    )
    parser.add_argument(
        'value',
        help=(
            'The value to set the property to. Valid input varies'
            ' based on the property being set.'
        ),
    )
    resources.AddMembershipResourceArg(
        parser,
        plural=True,
        membership_help=(
            'The membership names to update, separated by commas if multiple'
            ' are supplied. Ignored if --all-memberships is supplied; if'
            ' neither is supplied, a prompt will appear with all available'
            ' memberships.'
        ),
    )
    parser.add_argument(
        '--all-memberships',
        action='store_true',
        help=(
            'If supplied, update Policy Controller for all memberships in the'
            ' fleet.'
        ),
        default=False,
    )
    parser.add_argument(
        '--effect',
        choices=deployment.K8S_SCHEDULING_OPTIONS,
        type=str,
        help='Applies only to "toleration" property.',
    )

  def Run(self, args):
    # All the membership specs for this feature.
    specs = self._membership_specs(args)

    for _, spec in specs.items():
      cfgs = deployment.get_configurations(spec)
      deployment_cfg = cfgs.get(
          args.deployment,
          self.messages.PolicyControllerPolicyControllerDeploymentConfig(),
      )

      cfgs[args.deployment] = self.set_deployment_config(
          deployment_cfg,
          args.property,
          args.value,
          args.effect,
      )

      # Convert back to a list of additionalProperties
      cfg_values = [
          self.cfg_to_additional_property(key, cfg) for key, cfg in cfgs.items()
      ]

      # Rebuild DeploymentConfigValues and assign back to spec.
      dcv = self.messages.PolicyControllerHubConfig.DeploymentConfigsValue()
      dcv.additionalProperties = cfg_values
      spec.policycontroller.policyControllerHubConfig.deploymentConfigs = dcv

    return self.merge_specs(specs)

  def _membership_specs(self, args):
    memberships = [
        fleet_util.MembershipPartialName(p)
        for p in base.ParseMembershipsPlural(
            args, search=True, prompt=True, prompt_cancel=False, autoselect=True
        )
    ]
    specs = self.hubclient.ToPyDict(self.GetFeature().membershipSpecs)
    return {
        path: spec
        for path, spec in specs.items()
        if fleet_util.MembershipPartialName(path) in memberships
    }

  def set_deployment_config(self, deployment_cfg, prop, value, effect):
    if prop == 'toleration':
      return deployment.add_toleration(
          self.messages, deployment_cfg, value, effect
      )
    if effect is not None:
      raise exceptions.Error(
          '"effect" flag only accepted when setting a toleration.'
      )
    if prop == 'cpu-limit':
      return deployment.update_cpu_limit(self.messages, deployment_cfg, value)
    if prop == 'cpu-request':
      return deployment.update_cpu_request(self.messages, deployment_cfg, value)
    if prop == 'memory-limit':
      return deployment.update_mem_limit(self.messages, deployment_cfg, value)
    if prop == 'memory-request':
      return deployment.update_mem_request(self.messages, deployment_cfg, value)
    if prop == 'replica-count':
      return deployment.update_replica_count(deployment_cfg, value)

  def cfg_to_additional_property(self, key, cfg):
    return self.messages.PolicyControllerHubConfig.DeploymentConfigsValue.AdditionalProperty(
        key=key, value=cfg
    )

  def merge_specs(self, specs):
    orig = self.hubclient.ToPyDict(self.GetFeature().membershipSpecs)
    merged = {path: specs.get(path, spec) for path, spec in orig.items()}
    self.Update(
        ['membership_specs'],
        self.messages.Feature(
            membershipSpecs=self.hubclient.ToMembershipSpecs(merged)
        ),
    )

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
"""Fleet API type helpers.

Because the Fleet API is split into multiple API tracks, this file provides
helpers to make it easier to work with the different tracks. TypeAlias is not
used because it is only supported in Python 3.10+. These type aliases are
intended to be used in type hints when the specific track is not known.
"""

from typing import Generator

from googlecloudsdk.generated_clients.apis.gkehub.v1 import gkehub_v1_client as ga_client
from googlecloudsdk.generated_clients.apis.gkehub.v1 import gkehub_v1_messages as ga_messages
from googlecloudsdk.generated_clients.apis.gkehub.v1alpha import gkehub_v1alpha_client as alpha_client
from googlecloudsdk.generated_clients.apis.gkehub.v1alpha import gkehub_v1alpha_messages as alpha_messages
from googlecloudsdk.generated_clients.apis.gkehub.v1beta import gkehub_v1beta_client as beta_client
from googlecloudsdk.generated_clients.apis.gkehub.v1beta import gkehub_v1beta_messages as beta_messages
from googlecloudsdk.generated_clients.apis.gkehub.v2 import gkehub_v2_client as v2_ga_client
from googlecloudsdk.generated_clients.apis.gkehub.v2alpha import gkehub_v2alpha_client as v2_alpha_client
from googlecloudsdk.generated_clients.apis.gkehub.v2beta import gkehub_v2beta_client as v2_beta_client


BinaryAuthorizationConfig = (
    alpha_messages.BinaryAuthorizationConfig
    | beta_messages.BinaryAuthorizationConfig
    | ga_messages.BinaryAuthorizationConfig
)

BinaryAuthorizationConfigEvaluationModeValueValuesEnum = (
    alpha_messages.BinaryAuthorizationConfig.EvaluationModeValueValuesEnum
    | beta_messages.BinaryAuthorizationConfig.EvaluationModeValueValuesEnum
    | ga_messages.BinaryAuthorizationConfig.EvaluationModeValueValuesEnum
)

CompliancePostureConfig = (
    alpha_messages.CompliancePostureConfig
    | beta_messages.CompliancePostureConfig
    | ga_messages.CompliancePostureConfig
)

DefaultClusterConfig = (
    alpha_messages.DefaultClusterConfig
    | beta_messages.DefaultClusterConfig
    | ga_messages.DefaultClusterConfig
)

Fleet = alpha_messages.Fleet | beta_messages.Fleet | ga_messages.Fleet

GkehubProjectsLocationsFleetsCreateRequest = (
    alpha_messages.GkehubProjectsLocationsFleetsCreateRequest
    | beta_messages.GkehubProjectsLocationsFleetsCreateRequest
    | ga_messages.GkehubProjectsLocationsFleetsCreateRequest
)

GkehubProjectsLocationsFleetsDeleteRequest = (
    alpha_messages.GkehubProjectsLocationsFleetsDeleteRequest
    | beta_messages.GkehubProjectsLocationsFleetsDeleteRequest
    | ga_messages.GkehubProjectsLocationsFleetsDeleteRequest
)

GkehubProjectsLocationsFleetsPatchRequest = (
    alpha_messages.GkehubProjectsLocationsFleetsPatchRequest
    | beta_messages.GkehubProjectsLocationsFleetsPatchRequest
    | ga_messages.GkehubProjectsLocationsFleetsPatchRequest
)

GkehubProjectsLocationsOperationsListRequest = (
    alpha_messages.GkehubProjectsLocationsOperationsListRequest
    | beta_messages.GkehubProjectsLocationsOperationsListRequest
    | ga_messages.GkehubProjectsLocationsOperationsListRequest
)

GkehubProjectsLocationsOperationsGetRequest = (
    alpha_messages.GkehubProjectsLocationsOperationsGetRequest
    | beta_messages.GkehubProjectsLocationsOperationsGetRequest
    | ga_messages.GkehubProjectsLocationsOperationsGetRequest
)

GkehubProjectsLocationsRolloutsCreateRequest = (
    alpha_messages.GkehubProjectsLocationsRolloutsCreateRequest
    # Rollouts are not yet available in beta or GA.
    # | beta_messages.GkehubProjectsLocationsRolloutsCreateRequest
    # | ga_messages.GkehubProjectsLocationsRolloutsCreateRequest
)

GkehubProjectsLocationsRolloutsDeleteRequest = (
    alpha_messages.GkehubProjectsLocationsRolloutsDeleteRequest
    # Rollouts are not yet available in beta or GA.
    # | beta_messages.GkehubProjectsLocationsRolloutsDeleteRequest
    # | ga_messages.GkehubProjectsLocationsRolloutsDeleteRequest
)

GkehubProjectsLocationsRolloutsForceCompleteStageRequest = (
    alpha_messages.GkehubProjectsLocationsRolloutsForceCompleteStageRequest
    # Rollouts are not yet available in beta or GA.
    # | beta_messages.GkehubProjectsLocationsRolloutsForceCompleteStageRequest
    # | ga_messages.GkehubProjectsLocationsRolloutsForceCompleteStageRequest
)

GkehubProjectsLocationsRolloutsCancelRequest = (
    alpha_messages.GkehubProjectsLocationsRolloutsCancelRequest
    # Rollouts are not yet available in beta or GA.
    # | beta_messages.GkehubProjectsLocationsRolloutsCancelRequest
    # | ga_messages.GkehubProjectsLocationsRolloutsCancelRequest
)

GkehubProjectsLocationsRolloutsGetRequest = (
    alpha_messages.GkehubProjectsLocationsRolloutsGetRequest
    # Rollouts are not yet available in beta or GA.
    # | beta_messages.GkehubProjectsLocationsRolloutsGetRequest
    # | ga_messages.GkehubProjectsLocationsRolloutsGetRequest
)

GkehubProjectsLocationsRolloutsListRequest = (
    alpha_messages.GkehubProjectsLocationsRolloutsListRequest
    # Rollouts are not yet available in beta or GA.
    # | beta_messages.GkehubProjectsLocationsRolloutsListRequest
    # | ga_messages.GkehubProjectsLocationsRolloutsListRequest
)

GkehubProjectsLocationsRolloutsPauseRequest = (
    alpha_messages.GkehubProjectsLocationsRolloutsPauseRequest
    # Rollouts are not yet available in beta or GA.
    # | beta_messages.GkehubProjectsLocationsRolloutsPauseRequest
    # | ga_messages.GkehubProjectsLocationsRolloutsPauseRequest
)

GkehubProjectsLocationsRolloutsResumeRequest = (
    alpha_messages.GkehubProjectsLocationsRolloutsResumeRequest
    # Rollouts are not yet available in beta or GA.
    # | beta_messages.GkehubProjectsLocationsRolloutsResumeRequest
    # | ga_messages.GkehubProjectsLocationsRolloutsResumeRequest
)

GkehubProjectsLocationsRolloutSequencesCreateRequest = (
    alpha_messages.GkehubProjectsLocationsRolloutSequencesCreateRequest
    # RolloutSequences are not yet available in beta or GA.
    # | beta_messages.GkehubProjectsLocationsRolloutSequencesCreateRequest
    # | ga_messages.GkehubProjectsLocationsRolloutSequencesCreateRequest
)

GkehubProjectsLocationsRolloutSequencesGetRequest = (
    alpha_messages.GkehubProjectsLocationsRolloutSequencesGetRequest
    # RolloutSequences are not yet available in beta or GA.
    # | beta_messages.GkehubProjectsLocationsRolloutSequencesGetRequest
    # | ga_messages.GkehubProjectsLocationsRolloutSequencesGetRequest
)

GkehubProjectsLocationsRolloutSequencesListRequest = (
    alpha_messages.GkehubProjectsLocationsRolloutSequencesListRequest
    # RolloutSequences are not yet available in beta or GA.
    # | beta_messages.GkehubProjectsLocationsRolloutSequencesListRequest
    # | ga_messages.GkehubProjectsLocationsRolloutSequencesListRequest
)

GkehubProjectsLocationsRolloutSequencesDeleteRequest = (
    alpha_messages.GkehubProjectsLocationsRolloutSequencesDeleteRequest
    # RolloutSequences are not yet available in beta or GA.
    # | beta_messages.GkehubProjectsLocationsRolloutSequencesDeleteRequest
    # | ga_messages.GkehubProjectsLocationsRolloutSequencesDeleteRequest
)

GkehubProjectsLocationsRolloutSequencesPatchRequest = (
    alpha_messages.GkehubProjectsLocationsRolloutSequencesPatchRequest
    # RolloutSequences are not yet available in beta or GA.
    # | beta_messages.GkehubProjectsLocationsRolloutSequencesPatchRequest
    # | ga_messages.GkehubProjectsLocationsRolloutSequencesPatchRequest
)

Operation = alpha_messages.Operation | beta_messages.Operation | ga_messages.Operation

PolicyBinding = (
    alpha_messages.PolicyBinding
    | beta_messages.PolicyBinding
    | ga_messages.PolicyBinding
)

Rollout = (
    alpha_messages.Rollout
    # Rollouts are not yet available in beta or GA.
    # | beta_messages.Rollout
    # | ga_messages.Rollout
)

RolloutSequence = (
    alpha_messages.RolloutSequence
    # RolloutSequences are not yet available in beta or GA.
    # | beta_messages.RolloutSequence
    # | ga_messages.RolloutSequence
)

RolloutGenerator = Generator[Rollout, None, None]

RolloutSequenceGenerator = Generator[RolloutSequence, None, None]

SecurityPostureConfig = (
    alpha_messages.SecurityPostureConfig
    | beta_messages.SecurityPostureConfig
    | ga_messages.SecurityPostureConfig
)

SecurityPostureConfigModeValueValuesEnum = (
    alpha_messages.SecurityPostureConfig.ModeValueValuesEnum
    | beta_messages.SecurityPostureConfig.ModeValueValuesEnum
    | ga_messages.SecurityPostureConfig.ModeValueValuesEnum
)

SecurityPostureConfigVulnerabilityModeValueValuesEnum = (
    alpha_messages.SecurityPostureConfig.VulnerabilityModeValueValuesEnum
    | beta_messages.SecurityPostureConfig.VulnerabilityModeValueValuesEnum
    | ga_messages.SecurityPostureConfig.VulnerabilityModeValueValuesEnum
)

TrackClient = (
    alpha_client.GkehubV1alpha | beta_client.GkehubV1beta | ga_client.GkehubV1
)

V2TrackClient = (
    v2_alpha_client.GkehubV2alpha
    | v2_beta_client.GkehubV2beta
    | v2_ga_client.GkehubV2
)

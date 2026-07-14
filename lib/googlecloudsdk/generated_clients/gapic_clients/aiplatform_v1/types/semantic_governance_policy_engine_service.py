# -*- coding: utf-8 -*-
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import annotations

from typing import MutableMapping, MutableSequence

import proto  # type: ignore

from cloudsdk.google.protobuf import field_mask_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types import operation


__protobuf__ = proto.module(
    package='google.cloud.aiplatform.v1',
    manifest={
        'SemanticGovernancePolicyEngine',
        'GetSemanticGovernancePolicyEngineRequest',
        'UpdateSemanticGovernancePolicyEngineRequest',
        'UpdateSemanticGovernancePolicyEngineOperationMetadata',
        'DeprovisionSemanticGovernancePolicyEngineRequest',
        'DeprovisionSemanticGovernancePolicyEngineOperationMetadata',
        'GatewayConfig',
    },
)


class SemanticGovernancePolicyEngine(proto.Message):
    r"""Define a singleton SemanticGovernancePolicyEngine resource
    under a project and location.

    Attributes:
        name (str):
            Identifier. The resource name of the
            SemanticGovernancePolicyEngine. Format:

            projects/{project}/locations/{location}/semanticGovernancePolicyEngine
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. Timestamp when this
            SemanticGovernancePolicyEngine was created.
        update_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. Timestamp when this
            SemanticGovernancePolicyEngine was last updated.
        psc_service_attachment (str):
            Output only. URI of the PSC attachment resource provided by
            SGP. Format:
            projects/{project}/regions/{region}/serviceAttachments/{service_attachment}
        ip_address (str):
            Output only. The private IPv4 address of the
            PSC endpoint.
        psc_forwarding_rule (str):
            Output only. The URI of the PSC endpoint resource created in
            customer project. Format:
            projects/{project}/regions/{region}/forwardingRules/{forwarding_rule}
        state (googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types.SemanticGovernancePolicyEngine.State):
            Output only. The state of the
            SemanticGovernancePolicyEngine.
        gateway_configs (MutableMapping[str, googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types.GatewayConfig]):
            Optional. Configurations for gateways. The
            keys are user-defined names for each gateway. At
            most 5 gateway configurations are allowed.
    """
    class State(proto.Enum):
        r"""State of the SemanticGovernancePolicyEngine.

        The lifecycle is: INACTIVE -> PROVISIONING -> {ACTIVE, FAILED}
        and ACTIVE -> DEPROVISIONING -> INACTIVE.  A FAILED engine may
        be either re-provisioned or deprovisioned.

        Values:
            STATE_UNSPECIFIED (0):
                Default value. This value is unused.
            PROVISIONING (1):
                A provisioning operation is in progress.  The
                engine will transition to ACTIVE on success or
                FAILED on failure.
            ACTIVE (2):
                The engine and all of its gateway
                configurations are provisioned and ready to
                serve traffic.
            DEPROVISIONING (3):
                A deprovisioning operation is in progress.
                The engine will transition to INACTIVE on
                success or FAILED on failure.
            INACTIVE (4):
                The engine has no provisioned infrastructure:
                either never provisioned, or successfully
                deprovisioned.
            FAILED (5):
                The most recent provisioning or
                deprovisioning operation failed. The engine may
                have partial infrastructure that needs explicit
                deprovision; the engine may be either
                re-provisioned or deprovisioned to recover.
        """
        STATE_UNSPECIFIED = 0
        PROVISIONING = 1
        ACTIVE = 2
        DEPROVISIONING = 3
        INACTIVE = 4
        FAILED = 5

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=5,
        message=timestamp_pb2.Timestamp,
    )
    update_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=6,
        message=timestamp_pb2.Timestamp,
    )
    psc_service_attachment: str = proto.Field(
        proto.STRING,
        number=7,
    )
    ip_address: str = proto.Field(
        proto.STRING,
        number=8,
    )
    psc_forwarding_rule: str = proto.Field(
        proto.STRING,
        number=9,
    )
    state: State = proto.Field(
        proto.ENUM,
        number=11,
        enum=State,
    )
    gateway_configs: MutableMapping[str, 'GatewayConfig'] = proto.MapField(
        proto.STRING,
        proto.MESSAGE,
        number=14,
        message='GatewayConfig',
    )


class GetSemanticGovernancePolicyEngineRequest(proto.Message):
    r"""Request message for GetSemanticGovernancePolicyEngine.

    Attributes:
        name (str):
            Required. The resource name of the
            SemanticGovernancePolicyEngine to retrieve.
            Format:

            projects/{project}/locations/{location}/semanticGovernancePolicyEngine
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class UpdateSemanticGovernancePolicyEngineRequest(proto.Message):
    r"""Request message for UpdateSemanticGovernancePolicyEngine.

    Attributes:
        semantic_governance_policy_engine (googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types.SemanticGovernancePolicyEngine):
            Required. The SemanticGovernancePolicyEngine resource to
            update. The name field of the
            semantic_governance_policy_engine must be of the form
            ``projects/{project}/locations/{location}/semanticGovernancePolicyEngine``.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Optional. Specifies the fields to be overwritten in the
            SemanticGovernancePolicyEngine resource by the update. The
            fields specified in the update_mask are relative to the
            resource itself. If no update_mask is provided, all fields
            are overwritten.
    """

    semantic_governance_policy_engine: 'SemanticGovernancePolicyEngine' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='SemanticGovernancePolicyEngine',
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=2,
        message=field_mask_pb2.FieldMask,
    )


class UpdateSemanticGovernancePolicyEngineOperationMetadata(proto.Message):
    r"""Details of
    [SemanticGovernancePolicyEngineService.UpdateSemanticGovernancePolicyEngine][google.cloud.aiplatform.v1.SemanticGovernancePolicyEngineService.UpdateSemanticGovernancePolicyEngine]
    operation.

    Attributes:
        generic_metadata (googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types.GenericOperationMetadata):
            The common part of the operation metadata.
        progress_message (str):
            Output only. Granular progress message for
            the operation.
    """

    generic_metadata: operation.GenericOperationMetadata = proto.Field(
        proto.MESSAGE,
        number=1,
        message=operation.GenericOperationMetadata,
    )
    progress_message: str = proto.Field(
        proto.STRING,
        number=2,
    )


class DeprovisionSemanticGovernancePolicyEngineRequest(proto.Message):
    r"""Request message for
    [SemanticGovernancePolicyEngineService.DeprovisionSemanticGovernancePolicyEngine][google.cloud.aiplatform.v1.SemanticGovernancePolicyEngineService.DeprovisionSemanticGovernancePolicyEngine].

    Attributes:
        name (str):
            Required. The resource name of the
            SemanticGovernancePolicyEngine to deprovision.
            Format:

            projects/{project}/locations/{location}/semanticGovernancePolicyEngine
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class DeprovisionSemanticGovernancePolicyEngineOperationMetadata(proto.Message):
    r"""Details of
    [SemanticGovernancePolicyEngineService.DeprovisionSemanticGovernancePolicyEngine][google.cloud.aiplatform.v1.SemanticGovernancePolicyEngineService.DeprovisionSemanticGovernancePolicyEngine]
    operation.

    Attributes:
        generic_metadata (googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types.GenericOperationMetadata):
            The common part of the operation metadata.
    """

    generic_metadata: operation.GenericOperationMetadata = proto.Field(
        proto.MESSAGE,
        number=1,
        message=operation.GenericOperationMetadata,
    )


class GatewayConfig(proto.Message):
    r"""Configuration for a single gateway.

    Attributes:
        network (str):
            Optional. The URI of the network resource where PSC-E will
            be provisioned. if not provided ``default`` network will be
            used. Format: projects/{project}/global/networks/{network}
        subnetwork (str):
            Optional. The URI of the subnetwork resource where PSC-E
            will be provisioned. if not provided ``default`` subnet will
            be used from the same {location} Format:
            projects/{project}/regions/{region}/subnetworks/{subnetwork}
        dns_zone_name (str):
            Optional. FQDN of the private DNS zone to
            create DNS record set for PSC endpoint.
        state (googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types.GatewayConfig.State):
            Output only. The state of the Gateway
            configuration.
        ip_address (str):
            Output only. The private IP address of the
            PSC endpoint.
        psc_endpoint (str):
            Output only. The self-link or name of the
            Private Service Connect endpoint forwarding
            rule.
        dns_record (str):
            Output only. The fully qualified record name
            of the created A-record in Cloud DNS.
    """
    class State(proto.Enum):
        r"""State of the Gateway configuration.

        Values:
            STATE_UNSPECIFIED (0):
                The default value. This value is used if the
                state is omitted.
            PROVISIONING (1):
                The Gateway is being provisioned.
            ACTIVE (2):
                The Gateway is active and ready to use.
            DEPROVISIONING (3):
                The Gateway is being de-provisioned.
            INACTIVE (4):
                The Gateway is inactive.
            FAILED (5):
                The Gateway failed to be provisioned.
        """
        STATE_UNSPECIFIED = 0
        PROVISIONING = 1
        ACTIVE = 2
        DEPROVISIONING = 3
        INACTIVE = 4
        FAILED = 5

    network: str = proto.Field(
        proto.STRING,
        number=2,
    )
    subnetwork: str = proto.Field(
        proto.STRING,
        number=3,
    )
    dns_zone_name: str = proto.Field(
        proto.STRING,
        number=4,
    )
    state: State = proto.Field(
        proto.ENUM,
        number=5,
        enum=State,
    )
    ip_address: str = proto.Field(
        proto.STRING,
        number=6,
    )
    psc_endpoint: str = proto.Field(
        proto.STRING,
        number=7,
    )
    dns_record: str = proto.Field(
        proto.STRING,
        number=8,
    )


__all__ = tuple(sorted(__protobuf__.manifest))

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
from googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types import operation


__protobuf__ = proto.module(
    package='google.cloud.aiplatform.v1beta1',
    manifest={
        'SemanticGovernancePolicy',
        'CreateSemanticGovernancePolicyRequest',
        'GetSemanticGovernancePolicyRequest',
        'ListSemanticGovernancePoliciesRequest',
        'ListSemanticGovernancePoliciesResponse',
        'UpdateSemanticGovernancePolicyRequest',
        'DeleteSemanticGovernancePolicyRequest',
        'CreateSemanticGovernancePolicyOperationMetadata',
        'UpdateSemanticGovernancePolicyOperationMetadata',
        'DeleteSemanticGovernancePolicyOperationMetadata',
    },
)


class SemanticGovernancePolicy(proto.Message):
    r"""Represents a governance policy applied to a specific Agent
    and optionally a specific Tool within that Agent.

    Attributes:
        name (str):
            Identifier. Resource name of the
            SemanticGovernancePolicy.
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. Timestamp when this
            SemanticGovernancePolicy was created.
        update_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. Timestamp when this
            SemanticGovernancePolicy was last updated.
        etag (str):
            Optional. Used to perform consistent
            read-modify-write transactions. If provided, the
            request will only succeed if the etag matches
            the current value. Otherwise, an ABORTED error
            will be returned.
        display_name (str):
            Optional. The user-defined name of the
            SemanticGovernancePolicy.
        description (str):
            Optional. The description of the
            SemanticGovernancePolicy.
        natural_language_constraint (str):
            Required. The natural language constraint of
            the SemanticGovernancePolicy.
        agent (str):
            Required. The name of the agent in Agent
            Registry that is affected by this policy.
        mcp_tools (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.SemanticGovernancePolicy.McpTool]):
            Optional. The McpTools that are affected by
            this policy.
        agent_identity (str):
            Output only. Represents the principal of the agent, used by
            the Policy Decision Point (PDP) for governance checks. For
            more information, see
            https://docs.cloud.google.com/agent-builder/agent-engine/agent-identity

            Format: ``principal://TRUST_DOMAIN/NAMESPACE/AGENT_NAME``

            Example:
            ``principal://agents.global.org-ORGANIZATION_ID.system.id.goog/resources/aiplatform/projects/PROJECT_NUMBER/locations/LOCATION/reasoningEngines/AGENT_ENGINE_ID``
    """

    class McpTool(proto.Message):
        r"""Represents a governance policy applied to MCP tools used by
        an Agent.

        Attributes:
            mcp_server (str):
                Required. The resource name of the McpServer in Agent
                Registry that is affected by this policy. Format:
                ``projects/{project}/locations/{location}/mcpServers/{mcp_server}``
            tools (MutableSequence[str]):
                Optional. The resource names of the McpTools
                used by the Agent that is affected by this
                policy. If not specified, the policy applies to
                all McpTools in the McpServer.
        """

        mcp_server: str = proto.Field(
            proto.STRING,
            number=1,
        )
        tools: MutableSequence[str] = proto.RepeatedField(
            proto.STRING,
            number=2,
        )

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=2,
        message=timestamp_pb2.Timestamp,
    )
    update_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=3,
        message=timestamp_pb2.Timestamp,
    )
    etag: str = proto.Field(
        proto.STRING,
        number=4,
    )
    display_name: str = proto.Field(
        proto.STRING,
        number=5,
    )
    description: str = proto.Field(
        proto.STRING,
        number=6,
    )
    natural_language_constraint: str = proto.Field(
        proto.STRING,
        number=7,
    )
    agent: str = proto.Field(
        proto.STRING,
        number=8,
    )
    mcp_tools: MutableSequence[McpTool] = proto.RepeatedField(
        proto.MESSAGE,
        number=9,
        message=McpTool,
    )
    agent_identity: str = proto.Field(
        proto.STRING,
        number=10,
    )


class CreateSemanticGovernancePolicyRequest(proto.Message):
    r"""Request message for
    SemanticGovernancePolicyService.CreateSemanticGovernancePolicy.

    Attributes:
        parent (str):
            Required. The resource name of the Location into which to
            create the SemanticGovernancePolicy. Format:
            ``projects/{project}/locations/{location}``
        semantic_governance_policy (googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.SemanticGovernancePolicy):
            Required. The SemanticGovernancePolicy to
            create.
        semantic_governance_policy_id (str):
            Required. The ID to use for the SemanticGovernancePolicy,
            which will become the final component of the
            SemanticGovernancePolicy's resource name.

            This value may be up to 63 characters, and valid characters
            are ``[a-z0-9-]``. The first character cannot be a number or
            hyphen. The last character must be a letter or a number.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    semantic_governance_policy: 'SemanticGovernancePolicy' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='SemanticGovernancePolicy',
    )
    semantic_governance_policy_id: str = proto.Field(
        proto.STRING,
        number=3,
    )


class GetSemanticGovernancePolicyRequest(proto.Message):
    r"""Request message for
    SemanticGovernancePolicyService.GetSemanticGovernancePolicy.

    Attributes:
        name (str):
            Required. The name of the SemanticGovernancePolicy resource.
            Format:
            ``projects/{project}/locations/{location}/semanticGovernancePolicies/{semantic_governance_policy}``
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ListSemanticGovernancePoliciesRequest(proto.Message):
    r"""Request message for
    SemanticGovernancePolicyService.ListSemanticGovernancePolicies.

    Attributes:
        parent (str):
            Required. The resource name of the Location from which to
            list the SemanticGovernancePolicies. Format:
            ``projects/{project}/locations/{location}``
        page_size (int):
            Optional. The list page size. If zero, a
            default page size of 10 is used.
        page_token (str):
            Optional. The standard list page token.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=2,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=3,
    )


class ListSemanticGovernancePoliciesResponse(proto.Message):
    r"""Response message for
    SemanticGovernancePolicyService.ListSemanticGovernancePolicies.

    Attributes:
        semantic_governance_policies (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.SemanticGovernancePolicy]):
            The list of SemanticGovernancePolicies.
        next_page_token (str):
            A token to retrieve the next page of results. Pass to
            [ListSemanticGovernancePoliciesRequest.page_token][google.cloud.aiplatform.v1beta1.ListSemanticGovernancePoliciesRequest.page_token]
            to obtain that page.
        etag (str):
            The etag of the semantic governance policies
            representing the current state of all semantic
            governance policies under the given parent. This
            is updated on every create, update, or delete
            operation.
    """

    @property
    def raw_page(self):
        return self

    semantic_governance_policies: MutableSequence['SemanticGovernancePolicy'] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message='SemanticGovernancePolicy',
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )
    etag: str = proto.Field(
        proto.STRING,
        number=3,
    )


class UpdateSemanticGovernancePolicyRequest(proto.Message):
    r"""Request message for
    SemanticGovernancePolicyService.UpdateSemanticGovernancePolicy.

    Attributes:
        semantic_governance_policy (googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.SemanticGovernancePolicy):
            Required. The SemanticGovernancePolicy to update.

            The SemanticGovernancePolicy's ``name`` field is used to
            identify the SemanticGovernancePolicy to update. Format:
            ``projects/{project}/locations/{location}/semanticGovernancePolicies/{semantic_governance_policy}``
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Optional. ``update_mask`` is used to specify the fields to
            be overwritten in the SemanticGovernancePolicy resource by
            the update. The fields specified in the ``update_mask`` are
            relative to the resource, not the full request. A field will
            be overwritten if it is in the mask. If the mask is not
            present, then all fields that are populated in the request
            message will be overwritten. Set the ``update_mask`` to
            ``*`` to override all fields.
    """

    semantic_governance_policy: 'SemanticGovernancePolicy' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='SemanticGovernancePolicy',
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=2,
        message=field_mask_pb2.FieldMask,
    )


class DeleteSemanticGovernancePolicyRequest(proto.Message):
    r"""Request message for
    SemanticGovernancePolicyService.DeleteSemanticGovernancePolicy.

    Attributes:
        name (str):
            Required. The name of the SemanticGovernancePolicy resource
            to be deleted. Format:
            ``projects/{project}/locations/{location}/semanticGovernancePolicies/{semantic_governance_policy}``
        etag (str):
            Optional. The etag of the
            SemanticGovernancePolicy. If an etag is provided
            and does not match the current etag of the
            SemanticGovernancePolicy, deletion will be
            blocked and an ABORTED error will be returned.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    etag: str = proto.Field(
        proto.STRING,
        number=2,
    )


class CreateSemanticGovernancePolicyOperationMetadata(proto.Message):
    r"""Runtime operation metadata for
    [SemanticGovernancePolicyService.CreateSemanticGovernancePolicy][google.cloud.aiplatform.v1beta1.SemanticGovernancePolicyService.CreateSemanticGovernancePolicy].

    Attributes:
        generic_metadata (googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.GenericOperationMetadata):
            The common part of the operation metadata.
    """

    generic_metadata: operation.GenericOperationMetadata = proto.Field(
        proto.MESSAGE,
        number=1,
        message=operation.GenericOperationMetadata,
    )


class UpdateSemanticGovernancePolicyOperationMetadata(proto.Message):
    r"""Runtime operation metadata for
    [SemanticGovernancePolicyService.UpdateSemanticGovernancePolicy][google.cloud.aiplatform.v1beta1.SemanticGovernancePolicyService.UpdateSemanticGovernancePolicy].

    Attributes:
        generic_metadata (googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.GenericOperationMetadata):
            The common part of the operation metadata.
    """

    generic_metadata: operation.GenericOperationMetadata = proto.Field(
        proto.MESSAGE,
        number=1,
        message=operation.GenericOperationMetadata,
    )


class DeleteSemanticGovernancePolicyOperationMetadata(proto.Message):
    r"""Runtime operation metadata for
    [SemanticGovernancePolicyService.DeleteSemanticGovernancePolicy][google.cloud.aiplatform.v1beta1.SemanticGovernancePolicyService.DeleteSemanticGovernancePolicy].

    Attributes:
        generic_metadata (googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.GenericOperationMetadata):
            The common part of the operation metadata.
    """

    generic_metadata: operation.GenericOperationMetadata = proto.Field(
        proto.MESSAGE,
        number=1,
        message=operation.GenericOperationMetadata,
    )


__all__ = tuple(sorted(__protobuf__.manifest))

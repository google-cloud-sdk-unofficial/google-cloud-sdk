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

from google.api import launch_stage_pb2  # type: ignore
from cloudsdk.google.protobuf import field_mask_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.run_v2.types import common_domain_mapping
from googlecloudsdk.generated_clients.gapic_clients.run_v2.types import condition


__protobuf__ = proto.module(
    package='google.cloud.run.v2',
    manifest={
        'CreateDomainMappingRequest',
        'UpdateDomainMappingRequest',
        'ListDomainMappingsRequest',
        'ListDomainMappingsResponse',
        'GetDomainMappingRequest',
        'DeleteDomainMappingRequest',
        'DomainMapping',
    },
)


class CreateDomainMappingRequest(proto.Message):
    r"""Request message for creating a DomainMapping.

    Attributes:
        parent (str):
            Required. The location and project in which this
            DomainMapping should be created. Format:
            ``projects/{project}/locations/{location}``, where
            ``{project}`` can be project id or number. Only lowercase
            characters, digits, and hyphens.
        domain_mapping (googlecloudsdk.generated_clients.gapic_clients.run_v2.types.DomainMapping):
            Required. The DomainMapping instance to
            create.
        domain_mapping_id (str):
            Required. The unique identifier for the DomainMapping. It
            must be a valid domain name that the caller is authorized to
            map, and must contain fewer than 254 characters. The name of
            the domain mapping becomes
            ``{parent}/domainMappings/{domain_mapping_id}``.
        validate_only (bool):
            Optional. Indicates that the request should
            be validated and default values populated,
            without persisting the request or creating any
            resources.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    domain_mapping: 'DomainMapping' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='DomainMapping',
    )
    domain_mapping_id: str = proto.Field(
        proto.STRING,
        number=3,
    )
    validate_only: bool = proto.Field(
        proto.BOOL,
        number=4,
    )


class UpdateDomainMappingRequest(proto.Message):
    r"""Request message for updating a DomainMapping.

    Attributes:
        domain_mapping (googlecloudsdk.generated_clients.gapic_clients.run_v2.types.DomainMapping):
            Required. The DomainMapping to be updated.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Optional. The list of fields to be updated.
        validate_only (bool):
            Optional. Indicates that the request should
            be validated and default values populated,
            without persisting the request or updating any
            resources.
        allow_missing (bool):
            Optional. If set to true, and if the DomainMapping does not
            exist, it will create a new one. The caller must have
            ``run.domainmappings.create`` permissions if this is set to
            true and the DomainMapping does not exist.
    """

    domain_mapping: 'DomainMapping' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='DomainMapping',
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=2,
        message=field_mask_pb2.FieldMask,
    )
    validate_only: bool = proto.Field(
        proto.BOOL,
        number=3,
    )
    allow_missing: bool = proto.Field(
        proto.BOOL,
        number=4,
    )


class ListDomainMappingsRequest(proto.Message):
    r"""Request message for retrieving a list of DomainMappings.

    Attributes:
        parent (str):
            Required. The location and project to list resources on.
            Location must be a valid Google Cloud region, and cannot be
            the "-" wildcard. Format:
            ``projects/{project}/locations/{location}``, where
            ``{project}`` can be project id or number.
        page_size (int):
            Optional. Maximum number of DomainMappings to
            return in this call.
        page_token (str):
            Optional. A page token received from a
            previous call to ListDomainMappings. All other
            parameters must match.
        show_deleted (bool):
            Optional. If true, returns deleted (but
            unexpired) resources along with active ones.
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
    show_deleted: bool = proto.Field(
        proto.BOOL,
        number=4,
    )


class ListDomainMappingsResponse(proto.Message):
    r"""Response message containing a list of DomainMappings.

    Attributes:
        domain_mappings (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.run_v2.types.DomainMapping]):
            The resulting list of DomainMappings.
        next_page_token (str):
            A token indicating there are more items than page_size. Use
            it in the next ListDomainMappings request to continue.
    """

    @property
    def raw_page(self):
        return self

    domain_mappings: MutableSequence['DomainMapping'] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message='DomainMapping',
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class GetDomainMappingRequest(proto.Message):
    r"""Request message for obtaining a DomainMapping by its full
    name.

    Attributes:
        name (str):
            Required. The full name of the DomainMapping. Format:
            ``projects/{project}/locations/{location}/domainMappings/{domain_mapping}``,
            where ``{project}`` can be project id or number.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class DeleteDomainMappingRequest(proto.Message):
    r"""Request message to delete a DomainMapping by its full name.

    Attributes:
        name (str):
            Required. The full name of the DomainMapping. Format:
            ``projects/{project}/locations/{location}/domainMappings/{domain_mapping}``,
            where ``{project}`` can be project id or number.
        validate_only (bool):
            Optional. Indicates that the request should
            be validated without actually deleting any
            resources.
        etag (str):
            Optional. A system-generated fingerprint for
            this version of the resource. May be used to
            detect modification conflict during updates.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    validate_only: bool = proto.Field(
        proto.BOOL,
        number=2,
    )
    etag: str = proto.Field(
        proto.STRING,
        number=3,
    )


class DomainMapping(proto.Message):
    r"""Resource to hold the state and status of a user's domain
    mapping.

    Attributes:
        name (str):
            Identifier. The fully qualified name of this DomainMapping.
            In CreateDomainMappingRequest, this field is ignored, and
            instead composed from CreateDomainMappingRequest.parent and
            CreateDomainMappingRequest.domain_mapping_id.

            Format:
            projects/{project}/locations/{location}/domainMappings/{domain_mapping}
        uid (str):
            Output only. Server assigned unique
            identifier for the trigger. The value is a UUID4
            string and guaranteed to remain unchanged until
            the resource is deleted.
        generation (int):
            Output only. A number that monotonically increases every
            time the user modifies the desired state. Please note that
            unlike v1, this is an int64 value. As with most Google APIs,
            its JSON representation will be a ``string`` instead of an
            ``integer``.
        labels (MutableMapping[str, str]):
            Optional. Unstructured key value map that can be used to
            organize and categorize objects. User-provided labels are
            shared with Google's billing system, so they can be used to
            filter, or break down billing charges by team, component,
            environment, state, etc. For more information, visit
            https://cloud.google.com/resource-manager/docs/creating-managing-labels
            or https://cloud.google.com/run/docs/configuring/labels.

            .. raw:: html

                <p>Cloud Run API v2 does not support labels with `run.googleapis.com`,
                `cloud.googleapis.com`, `serving.knative.dev`, or `autoscaling.knative.dev`
                namespaces, and they will be rejected. All system labels in v1 now have a
                corresponding field in v2 DomainMapping.
        annotations (MutableMapping[str, str]):
            Optional. Unstructured key value map that may be set by
            external tools to store and arbitrary metadata. They are not
            queryable and should be preserved when modifying objects.

            .. raw:: html

                <p>Cloud Run API v2 does not support annotations with `run.googleapis.com`,
                `cloud.googleapis.com`, `serving.knative.dev`, or `autoscaling.knative.dev`
                namespaces, and they will be rejected in new resources. All system
                annotations in v1 now have a corresponding field in v2 DomainMapping.

            .. raw:: html

                <p>This field follows Kubernetes
                annotations' namespacing, limits, and rules.
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The creation time.
        update_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The last-modified time.
        delete_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The deletion time. It is only
            populated as a response to a Delete request.
        expire_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. For a deleted resource, the time
            after which it will be permanently deleted.
        creator (str):
            Output only. Email address of the
            authenticated creator.
        last_modifier (str):
            Output only. Email address of the last
            authenticated modifier.
        client (str):
            Arbitrary identifier for the API client.
        client_version (str):
            Arbitrary version identifier for the API
            client.
        launch_stage (google.api.launch_stage_pb2.LaunchStage):
            Optional. The launch stage as defined by `Google Cloud
            Platform Launch
            Stages <https://cloud.google.com/terms/launch-stages>`__.
            Cloud Run supports ``ALPHA``, ``BETA``, and ``GA``. If no
            value is specified, GA is assumed. Set the launch stage to a
            preview stage on input to allow use of preview features in
            that stage. On read (or output), describes whether the
            resource uses preview features.

            For example, if ALPHA is provided as input, but only BETA
            and GA-level features are used, this field will be BETA on
            output.
        service (str):
            Required. The name of the Service that this
            DomainMapping applies to. The service must
            exist.
        observed_generation (int):
            Output only. The generation of this DomainMapping currently
            serving traffic. See comments in ``reconciling`` for
            additional information on reconciliation process in Cloud
            Run. Please note that unlike v1, this is an int64 value. As
            with most Google APIs, its JSON representation will be a
            ``string`` instead of an ``integer``.
        terminal_condition (googlecloudsdk.generated_clients.gapic_clients.run_v2.types.Condition):
            Output only. The Condition of this DomainMapping, containing
            its readiness status, and detailed error information in case
            it did not reach a serving state. See comments in
            ``reconciling`` for additional information on reconciliation
            process in Cloud Run.
        conditions (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.run_v2.types.Condition]):
            Output only. The Conditions of all other associated
            sub-resources. They contain additional diagnostics
            information in case the DomainMapping does not reach its
            Serving state. See comments in ``reconciling`` for
            additional information on reconciliation process in Cloud
            Run.
        resource_records (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.run_v2.types.ResourceRecord]):
            Output only. The resource records required to
            configure this domain mapping. These records
            must be added to the domain's DNS configuration
            in order to serve the application via this
            domain mapping.
        mapped_service (str):
            Output only. The name of the service that the
            mapping currently points to.
        reconciling (bool):
            Output only. Returns true if the DomainMapping is currently
            being acted upon by the system to bring it into the desired
            state.

            When a new DomainMapping is created, or an existing one is
            updated, Cloud Run will asynchronously perform all necessary
            steps to bring the DomainMapping to the desired serving
            state. This process is called reconciliation. While
            reconciliation is in process, ``observed_generation`` and
            ``mapped_service`` will have transient values that might
            mismatch the intended state: Once reconciliation is over
            (and this field is false), there are two possible outcomes:
            reconciliation succeeded and the serving state matches the
            DomainMapping, or there was an error, and reconciliation
            failed. This state can be found in
            ``terminal_condition.state``.

            If reconciliation succeeded, the following fields will
            match: ``service`` and ``mapped_service``,
            ``observed_generation`` and ``generation``.

            If reconciliation failed, ``observed_generation`` and
            ``mapped_service`` will have the state of the last serving
            revision, or empty for newly created DomainMappings.
            Additional information on the failure can be found in
            ``terminal_condition`` and ``conditions``.
        etag (str):
            A system-generated fingerprint for this
            version of the resource. May be used to detect
            modification conflict during updates.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    uid: str = proto.Field(
        proto.STRING,
        number=2,
    )
    generation: int = proto.Field(
        proto.INT64,
        number=3,
    )
    labels: MutableMapping[str, str] = proto.MapField(
        proto.STRING,
        proto.STRING,
        number=4,
    )
    annotations: MutableMapping[str, str] = proto.MapField(
        proto.STRING,
        proto.STRING,
        number=5,
    )
    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=6,
        message=timestamp_pb2.Timestamp,
    )
    update_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=7,
        message=timestamp_pb2.Timestamp,
    )
    delete_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=8,
        message=timestamp_pb2.Timestamp,
    )
    expire_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=9,
        message=timestamp_pb2.Timestamp,
    )
    creator: str = proto.Field(
        proto.STRING,
        number=10,
    )
    last_modifier: str = proto.Field(
        proto.STRING,
        number=11,
    )
    client: str = proto.Field(
        proto.STRING,
        number=12,
    )
    client_version: str = proto.Field(
        proto.STRING,
        number=13,
    )
    launch_stage: launch_stage_pb2.LaunchStage = proto.Field(
        proto.ENUM,
        number=14,
        enum=launch_stage_pb2.LaunchStage,
    )
    service: str = proto.Field(
        proto.STRING,
        number=15,
    )
    observed_generation: int = proto.Field(
        proto.INT64,
        number=17,
    )
    terminal_condition: condition.Condition = proto.Field(
        proto.MESSAGE,
        number=18,
        message=condition.Condition,
    )
    conditions: MutableSequence[condition.Condition] = proto.RepeatedField(
        proto.MESSAGE,
        number=19,
        message=condition.Condition,
    )
    resource_records: MutableSequence[common_domain_mapping.ResourceRecord] = proto.RepeatedField(
        proto.MESSAGE,
        number=20,
        message=common_domain_mapping.ResourceRecord,
    )
    mapped_service: str = proto.Field(
        proto.STRING,
        number=21,
    )
    reconciling: bool = proto.Field(
        proto.BOOL,
        number=98,
    )
    etag: str = proto.Field(
        proto.STRING,
        number=99,
    )


__all__ = tuple(sorted(__protobuf__.manifest))

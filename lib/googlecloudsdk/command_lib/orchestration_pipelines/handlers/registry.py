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
"""Registry of supported GCP resource handlers."""

from googlecloudsdk.command_lib.orchestration_pipelines.handlers import artifactregistry
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import bq
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import bq_dts
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import cloudkms
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import composer
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import compute
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import dataform
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import dataproc
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import iam
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import pubsub
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import secretmanager
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import sqladmin
from googlecloudsdk.command_lib.orchestration_pipelines.handlers import storage

RESOURCE_HANDLERS = {
    # go/keep-sorted start
    "artifactregistry.repository": (
        artifactregistry.ArtifactRegistryRepositoryHandler
    ),
    "bigquery.dataset": bq.BqDatasetHandler,
    "bigquery.routine": bq.BqRoutineHandler,
    "bigquery.table": bq.BqTableHandler,
    "bigquerydatatransfer.transferConfig": bq_dts.BqDataTransferConfigHandler,
    "cloudkms.keyRing": cloudkms.CloudKmsKeyRingHandler,
    "cloudkms.keyRing.cryptoKey": cloudkms.CloudKmsCryptoKeyHandler,
    "composer.environment": composer.ComposerEnvironmentHandler,
    "compute.address": compute.ComputeAddressHandler,
    "compute.firewall": compute.ComputeFirewallHandler,
    "compute.forwardingRule": compute.ComputeForwardingRuleHandler,
    "compute.instance": compute.ComputeInstanceHandler,
    "compute.instanceGroupManager": compute.ComputeInstanceGroupManagerHandler,
    "compute.instanceTemplate": compute.ComputeInstanceTemplateHandler,
    "compute.network": compute.ComputeNetworkHandler,
    "compute.network.networkPeering": compute.ComputeNetworkPeeringHandler,
    "compute.route": compute.ComputeRouteHandler,
    "compute.router": compute.ComputeRouterHandler,
    "compute.subnetwork": compute.ComputeSubnetworkHandler,
    "compute.targetInstance": compute.ComputeTargetInstanceHandler,
    "dataform.repository": dataform.DataformRepositoryHandler,
    "dataform.repository.releaseConfig": dataform.DataformReleaseConfigHandler,
    "dataform.repository.workflowConfig": (
        dataform.DataformWorkflowConfigHandler
    ),
    "dataform.repository.workspace": dataform.DataformWorkspaceHandler,
    "dataproc.autoscalingPolicy": dataproc.DataprocAutoscalingPolicyHandler,
    "dataproc.cluster": dataproc.DataprocClusterHandler,
    "dataproc.workflowTemplate": dataproc.DataprocWorkflowTemplateHandler,
    "iam.serviceAccount": iam.IamServiceAccountHandler,
    "iam.serviceAccountIamPolicy": iam.IamServiceAccountIamPolicyHandler,
    "iam.workloadIdentityPool": iam.IamWorkloadIdentityPoolHandler,
    "iam.workloadIdentityPoolProvider": (
        iam.IamWorkloadIdentityPoolProviderHandler
    ),
    "pubsub.schema": pubsub.PubsubSchemaHandler,
    "pubsub.subscription": pubsub.PubsubSubscriptionHandler,
    "pubsub.topic": pubsub.PubsubTopicHandler,
    "secretmanager.secret": secretmanager.SecretManagerSecretHandler,
    "sqladmin.instance": sqladmin.SqladminInstanceHandler,
    "sqladmin.instance.database": sqladmin.SqladminDatabaseHandler,
    "sqladmin.instance.user": sqladmin.SqladminUserHandler,
    "storage.bucket": storage.StorageBucketHandler,
    "storage.bucket.iamPolicy": storage.StorageBucketIamPolicyHandler,
    "storage.bucket.notification": storage.StorageNotificationHandler,
    # go/keep-sorted end
}

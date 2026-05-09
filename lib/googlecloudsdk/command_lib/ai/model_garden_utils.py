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
"""Utilities for the model garden command group."""

import datetime

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.monitoring import metric
from googlecloudsdk.api_lib.quotas import quota_info
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io

_MAX_LABEL_VALUE_LENGTH = 63


_ACCELERATOR_TYPE_TO_QUOTA_ID_MAP = {
    'NVIDIA_TESLA_P4': 'CustomModelServingP4GPUsPerProjectPerRegion',
    'NVIDIA_TESLA_T4': 'CustomModelServingT4GPUsPerProjectPerRegion',
    'NVIDIA_L4': 'CustomModelServingL4GPUsPerProjectPerRegion',
    'NVIDIA_TESLA_K80': 'CustomModelServingK80GPUsPerProjectPerRegion',
    'NVIDIA_TESLA_V100': 'CustomModelServingV100GPUsPerProjectPerRegion',
    'NVIDIA_TESLA_P100': 'CustomModelServingP100GPUsPerProjectPerRegion',
    'NVIDIA_TESLA_A100': 'CustomModelServingA100GPUsPerProjectPerRegion',
    'NVIDIA_A100_80GB': 'CustomModelServingA10080GBGPUsPerProjectPerRegion',
    'NVIDIA_H100_80GB': 'CustomModelServingH100GPUsPerProjectPerRegion',
    'NVIDIA_RTX_PRO_6000': (
        'CustomModelServingRTXPRO6000GPUsPerProjectPerRegion'
    ),
    'TPU_V5_LITEPOD': 'CustomModelServingV5ETPUPerProjectPerRegion',
}


_ACCELERATOR_TYPE_TP_QUOTA_METRIC_MAP = {
    'NVIDIA_TESLA_P4': 'custom_model_serving_nvidia_p4_gpus',
    'NVIDIA_TESLA_T4': 'custom_model_serving_nvidia_t4_gpus',
    'NVIDIA_L4': 'custom_model_serving_nvidia_l4_gpus',
    'NVIDIA_TESLA_K80': 'custom_model_serving_nvidia_k80_gpus',
    'NVIDIA_TESLA_V100': 'custom_model_serving_nvidia_v100_gpus',
    'NVIDIA_TESLA_P100': 'custom_model_serving_nvidia_p100_gpus',
    'NVIDIA_TESLA_A100': 'custom_model_serving_nvidia_a100_gpus',
    'NVIDIA_A100_80GB': 'custom_model_serving_nvidia_a100_80gb_gpus',
    'NVIDIA_H100_80GB': 'custom_model_serving_nvidia_h100_gpus',
    'NVIDIA_RTX_PRO_6000': 'custom_model_serving_nvidia_rtx_pro_6000_gpus',
    'TPU_V5_LITEPOD': 'custom_model_serving_tpu_v5e',
}
_TIME_SERIES_FILTER = (
    # gcloud-disable-gdu-domain
    'metric.type="serviceruntime.googleapis.com/quota/allocation/usage" AND'
    ' resource.type="consumer_quota" AND'
    # gcloud-disable-gdu-domain
    ' metric.label.quota_metric="aiplatform.googleapis.com/{}"'
    ' AND resource.label.project_id="{}" AND resource.label.location="{}" AND'
    # gcloud-disable-gdu-domain
    ' resource.label.service="aiplatform.googleapis.com"'
)


def _ParseOperation(operation_name):
  """Parse operation resource to the operation reference object.

  Args:
    operation_name: The operation resource to wait on

  Returns:
    The operation reference object
  """
  return resources.REGISTRY.ParseRelativeName(
      operation_name,
      collection='aiplatform.projects.locations.operations',
  )


def _GetQuotaLimit(region, project, accelerator_type):
  """Gets the quota limit for the accelerator type in the region."""
  accelerator_quota = quota_info.GetQuotaInfo(
      project,
      None,
      None,
      # gcloud-disable-gdu-domain
      'aiplatform.googleapis.com',
      _ACCELERATOR_TYPE_TO_QUOTA_ID_MAP[accelerator_type],
  )
  for region_info in accelerator_quota.dimensionsInfos:
    if region_info.applicableLocations[0] == region:
      return region_info.details.value or 0
  return 0


def _GetQuotaUsage(region, project, accelerator_type):
  """Gets the quota usage for the accelerator type in the region using the monitoring AP."""
  # Format the time in RFC3339 UTC Zulu format
  current_time_utc = datetime.datetime.now(datetime.timezone.utc)
  # Need to go back at least 24 hours to reliably get a data point
  twenty_five_hours_ago_time_utc = current_time_utc - datetime.timedelta(
      hours=25
  )

  rfc3339_time = current_time_utc.isoformat(timespec='seconds').replace(
      '+00:00', 'Z'
  )
  rfc3339_time_twenty_five_hours_ago = twenty_five_hours_ago_time_utc.isoformat(
      timespec='seconds'
  ).replace('+00:00', 'Z')

  quota_usage_time_series = metric.MetricClient().ListTimeSeriesByProject(
      project=project,
      aggregation_alignment_period='60s',
      aggregation_per_series_aligner=metric.GetMessagesModule().MonitoringProjectsTimeSeriesListRequest.AggregationPerSeriesAlignerValueValuesEnum.ALIGN_NEXT_OLDER,
      interval_start_time=rfc3339_time_twenty_five_hours_ago,
      interval_end_time=rfc3339_time,
      filter_str=_TIME_SERIES_FILTER.format(
          _ACCELERATOR_TYPE_TP_QUOTA_METRIC_MAP[accelerator_type],
          project,
          region,
      ),
  )
  try:
    current_usage = (
        quota_usage_time_series.timeSeries[0].points[0].value.int64Value
    )
  except IndexError:
    # If no data point is found, the usage is 0.
    current_usage = 0
  return current_usage


def IsDefaultUniverse():
  return (
      properties.VALUES.core.universe_domain.Get()
      == properties.VALUES.core.universe_domain.default
  )


def GetCLIEndpointLabelValue(
    is_hf_model, publisher_name, model_name='', model_version_name=''
):
  if is_hf_model:
    return f'hf-{publisher_name}-{model_name}'.replace('.', '_')[
        :_MAX_LABEL_VALUE_LENGTH
    ]
  else:
    return f'mg-{publisher_name}-{model_version_name}'.replace('.', '_')[
        :_MAX_LABEL_VALUE_LENGTH
    ]


def GetOneClickEndpointLabelValue(
    is_hf_model, publisher_name, model_name='', model_version_name=''
):
  if is_hf_model:
    return f'hf-{publisher_name}-{model_name}'.replace('.', '_')[
        :_MAX_LABEL_VALUE_LENGTH
    ]
  else:
    return (
        f'publishers-{publisher_name}-models-{model_name}-{model_version_name}'
        .replace(
            '.', '_'
        )[
            :_MAX_LABEL_VALUE_LENGTH
        ]
    )


def GetDeployConfig(args, publisher_model):
  """Returns a best suited deployment configuration for the publisher model."""
  try:
    multi_deploy = (
        publisher_model.supportedActions.multiDeployVertex.multiDeployVertex
    )
  except AttributeError:
    raise core_exceptions.Error(
        'Model does not support deployment, please use a deploy-able model'
        ' instead. You can use the `gcloud ai model-garden models list`'
        ' command to find out which ones are currently supported by the'
        ' `deploy` command.'
    )

  deploy_config = None
  if args.machine_type or args.accelerator_type or args.container_image_uri:
    for deploy in multi_deploy:
      if (
          (
              args.machine_type
              and deploy.dedicatedResources.machineSpec.machineType
              != args.machine_type
          )
          or (
              args.accelerator_type
              and str(deploy.dedicatedResources.machineSpec.acceleratorType)
              != args.accelerator_type.upper()
          )
          or (
              args.container_image_uri
              and deploy.containerSpec.imageUri != args.container_image_uri
          )
      ):
        continue
      deploy_config = deploy
      break

    if not deploy_config:
      raise core_exceptions.Error(
          'The machine type, accelerator type and/or container image URI is not'
          ' supported by the model. You can use `gcloud alpha/beta ai'
          ' model-garden models list-deployment-config` command to find the'
          ' supported configurations'
      )
    log.status.Print('Using the selected deployment configuration:')
  else:
    # Default to use the first config.
    deploy_config = multi_deploy[0]
    log.status.Print('Using the default deployment configuration:')

  machine_spec = deploy_config.dedicatedResources.machineSpec
  container_image_uri = deploy_config.containerSpec.imageUri
  if machine_spec.machineType:
    log.status.Print(f' Machine type: {machine_spec.machineType}')
  if machine_spec.acceleratorType:
    log.status.Print(f' Accelerator type: {machine_spec.acceleratorType}')
  if machine_spec.acceleratorCount:
    log.status.Print(f' Accelerator count: {machine_spec.acceleratorCount}')
  if container_image_uri:
    log.status.Print(f' Container image URI: {container_image_uri}')
  return deploy_config


def CheckAcceleratorQuota(
    args, machine_type, accelerator_type, accelerator_count
):
  """Checks the accelerator quota for the project and region."""
  # In the machine spec, TPUs don't have accelerator type and count, but they
  # have machine type.
  if machine_type == 'ct5lp-hightpu-1t':
    accelerator_type = 'TPU_V5_LITEPOD'
    accelerator_count = 1
  elif machine_type == 'ct5lp-hightpu-4t':
    accelerator_type = 'TPU_V5_LITEPOD'
    accelerator_count = 4

  if not IsDefaultUniverse():
    # Handle CPU-only deployments in non-default universes.
    # deploy.py stringifies the acceleratorType, so we check for 'None' to
    # prevent KeyError in the quota map lookup.
    if str(accelerator_type) == 'None':
      log.debug(
          'No accelerator type specified, skipping accelerator quota check.'
      )
      return
  project = properties.VALUES.core.project.GetOrFail()
  quota_limit = _GetQuotaLimit(args.region, project, accelerator_type)
  if quota_limit < accelerator_count:
    raise core_exceptions.Error(
        'The project does not have enough quota for'
        f' {_ACCELERATOR_TYPE_TP_QUOTA_METRIC_MAP[accelerator_type]} in'
        f' {args.region} to'
        f' deploy the model. The quota limit is {quota_limit} and you are'
        f' requesting for {accelerator_count}. Please'
        ' use a different region or request more quota by following'
        ' https://cloud.google.com/vertex-ai/docs/quotas#requesting_additional_quota.'
    )

  current_usage = _GetQuotaUsage(args.region, project, accelerator_type)
  if current_usage + accelerator_count > quota_limit:
    raise core_exceptions.Error(
        'The project does not have enough quota for'
        f' {_ACCELERATOR_TYPE_TP_QUOTA_METRIC_MAP[accelerator_type]} in'
        f' {args.region} to'
        f' deploy the model. The current usage is {current_usage} out of'
        f' {quota_limit} and you are'
        f' requesting for {accelerator_count}. Please'
        ' use a different region or request more quota by following'
        ' https://cloud.google.com/vertex-ai/docs/quotas#requesting_additional_quota.'
    )
  log.info(
      'The project has enough quota. The current usage of quota for'
      f' accelerator type {accelerator_type} in region {args.region} is'
      f' {current_usage} out of {quota_limit}.'
  )


def Deploy(
    args, machine_spec, endpoint_name, model, operation_client, mg_client
):
  """Deploys the publisher model to a Vertex endpoint."""
  try:
    if machine_spec is not None:
      machine_type = machine_spec.machineType
      accelerator_type = machine_spec.acceleratorType
      accelerator_count = machine_spec.acceleratorCount
    else:
      machine_type = None
      accelerator_type = None
      accelerator_count = None
    deploy_op = mg_client.Deploy(
        project=properties.VALUES.core.project.GetOrFail(),
        location=args.region,
        model=model,
        accept_eula=args.accept_eula,
        accelerator_type=accelerator_type,
        accelerator_count=accelerator_count,
        machine_type=machine_type,
        endpoint_display_name=endpoint_name,
        hugging_face_access_token=args.hugging_face_access_token,
        spot=args.spot,
        reservation_affinity=args.reservation_affinity,
        use_dedicated_endpoint=args.use_dedicated_endpoint,
        disable_dedicated_endpoint=args.disable_dedicated_endpoint,
        enable_fast_tryout=args.enable_fast_tryout,
        system_labels=args.system_labels,
        container_image_uri=args.container_image_uri,
        container_command=args.container_command,
        container_args=args.container_args,
        container_env_vars=args.container_env_vars,
        container_ports=args.container_ports,
        container_grpc_ports=args.container_grpc_ports,
        container_predict_route=args.container_predict_route,
        container_health_route=args.container_health_route,
        container_deployment_timeout_seconds=args.container_deployment_timeout_seconds,
        container_shared_memory_size_mb=args.container_shared_memory_size_mb,
        container_startup_probe_exec=args.container_startup_probe_exec,
        container_startup_probe_period_seconds=args.container_startup_probe_period_seconds,
        container_startup_probe_timeout_seconds=args.container_startup_probe_timeout_seconds,
        container_health_probe_exec=args.container_health_probe_exec,
        container_health_probe_period_seconds=args.container_health_probe_period_seconds,
        container_health_probe_timeout_seconds=args.container_health_probe_timeout_seconds,
    )
  except apitools_exceptions.HttpError as e:
    # Keep prompting for HF token if the error is due to missing HF token.
    if (
        e.status_code == 400
        and 'provide a valid Hugging Face access token' in e.content
        and args.hugging_face_access_token is None
    ):
      while not args.hugging_face_access_token:
        args.hugging_face_access_token = console_io.PromptPassword(
            'Please enter your Hugging Face read access token: '
        )
      Deploy(
          args,
          machine_spec,
          endpoint_name,
          model,
          operation_client,
          mg_client,
      )
      return
    elif e.status_code == 403 and 'EULA' in e.content:
      log.status.Print(
          'The End User License Agreement'
          ' (EULA) of the model has not been accepted.'
      )
      publisher, model_id = args.model.split('@')[0].split('/')
      try:
        args.accept_eula = console_io.PromptContinue(
            message=(
                'The model can be deployed only if the EULA of the model has'
                ' been'
                ' accepted. You can view it at'
                f' https://console.cloud.google.com/vertex-ai/publishers/{publisher}/model-garden/{model_id}):'
            ),
            prompt_string='Do you want to accept the EULA?',
            default=False,
            cancel_on_no=True,
            cancel_string='EULA is not accepted.',
            throw_if_unattended=True,
        )
      except console_io.Error:
        raise core_exceptions.Error(
            'Please accept the EULA using the `--accept-eula` flag.'
        )
      Deploy(
          args,
          machine_spec,
          endpoint_name,
          model,
          operation_client,
          mg_client,
      )
      return
    else:
      raise e

  deploy_op_id = deploy_op.name.split('/')[-1]
  log.status.Print(
      'Deploying the model to the endpoint. To check the deployment'
      ' status, you can try one of the following methods:\n1) Look for'
      f' endpoint `{endpoint_name}` at the [Vertex AI] -> [Online'
      ' prediction] tab in Cloud Console\n2) Use `gcloud ai operations'
      f' describe {deploy_op_id} --region={args.region}` to find the status'
      ' of the deployment long-running operation\n'
  )
  operations_util.WaitForOpMaybe(
      operation_client,
      deploy_op,
      _ParseOperation(deploy_op.name),
      asynchronous=args.asynchronous,
      max_wait_ms=3600000,  # 60 minutes
  )

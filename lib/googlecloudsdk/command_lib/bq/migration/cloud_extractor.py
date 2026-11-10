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
"""Cloud execution mode orchestration for BigQuery migration extract commands."""

import time

from googlecloudsdk.api_lib.bq.migration import cloud_extractor as cloud_extractor_api
from googlecloudsdk.api_lib.compute import utils as compute_utils
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.bq.migration import cloud_utils
from googlecloudsdk.command_lib.bq.migration import extractor_flags
from googlecloudsdk.command_lib.bq.migration import extractor_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

DEFAULT_ZONE = 'us-central1-a'
DEFAULT_SERVICE_ACCOUNT_NAME = 'bqms-cloud-extractor'
DEFAULT_SERVICE_ACCOUNT_DISPLAY_NAME = 'BQMS Cloud Extractor Service Account'
POLL_INTERVAL_SECONDS = 30
FINAL_ARTIFACT_RETRY_COUNT = 30
FINAL_ARTIFACT_RETRY_SLEEP_SECONDS = 10

_SERVICE_ACCOUNT_ROLES = (
    'roles/logging.logWriter',
    'roles/logging.viewer',
    'roles/errorreporting.writer',
    'roles/monitoring.metricWriter',
    'roles/storage.objectAdmin',
    'roles/cloudkms.cryptoKeyDecrypter',
    'roles/compute.admin',
    'roles/editor',
    'roles/secretmanager.secretAccessor',
)

_TERMINAL_INSTANCE_STATES = frozenset({'TERMINATED', 'STOPPED', 'SUSPENDED'})


def ResolveZoneAndRegion(zone_arg):
  """Resolves the target Compute Engine zone and its corresponding region.

  Args:
    zone_arg: str or None, The `--zone` flag value.

  Returns:
    tuple[str, str], A `(zone, region)` pair.

  Raises:
    calliope_exceptions.InvalidArgumentException: If the resolved zone is not a
      valid `<region>-<zone>` identifier.
  """
  zone = zone_arg or properties.VALUES.compute.zone.Get() or DEFAULT_ZONE
  zone_short = zone.split('/')[-1]
  if zone_short.count('-') < 2 or not all(zone_short.split('-')):
    raise calliope_exceptions.InvalidArgumentException(
        '--zone',
        "Invalid Compute Engine zone '{}'.".format(zone),
    )
  return zone_short, compute_utils.ZoneNameToRegionName(zone_short)


def CheckForErrors(project, instance_id):
  """Inspects Cloud Logging for ERROR/SEVERE entries from the GCE instance.

  Args:
    project: str, The GCP project ID.
    instance_id: str, The numeric GCE instance ID.
  """
  messages = cloud_extractor_api.FetchInstanceErrorMessages(
      project, instance_id
  )
  if messages:
    log.warning(
        'Potential errors detected during extraction:\n  %s\n'
        'To see the full logs, run:\n'
        '  gcloud logging read \'resource.type="gce_instance" AND'
        ' resource.labels.instance_id="%s"\' --project=%s --limit=200',
        '\n  '.join(messages),
        instance_id,
        project,
    )


def WaitForCompletion(
    project,
    zone,
    instance_name,
    instance_id,
    output_ref,
    sleep_fn=time.sleep,
):
  """Polls GCS and the Compute Engine instance until extraction completes.

  Args:
    project: str, The GCP project ID.
    zone: str, Compute Engine zone.
    instance_name: str, Compute Engine instance name.
    instance_id: str, Numeric Compute Engine instance ID.
    output_ref: storage_util.ObjectReference, Parsed `--output` reference.
    sleep_fn: callable, Sleep function (`time.sleep`).

  Returns:
    str, The GCS URI of the produced `.zip` artifact.

  Raises:
    cloud_extractor_api.CloudExtractionError: If the instance terminates without
      producing a non-empty `.zip` artifact in GCS.
  """
  log.status.Print(
      'Instance Link:'
      ' https://console.cloud.google.com/compute/instancesDetail/zones/{zone}/instances/{instance}?project={project}'
      .format(zone=zone, instance=instance_name, project=project)
  )
  log.status.Print('Polling for completion (this may take 10-20 minutes)...')

  while True:
    artifact = cloud_extractor_api.FindOutputZipArtifact(output_ref)
    if artifact:
      artifact_uri, size_bytes = artifact
      log.status.Print('Extraction complete.')
      log.status.Print(
          'Artifact Path: {} ({} bytes)'.format(artifact_uri, size_bytes)
      )
      CheckForErrors(project, instance_id)
      return artifact_uri

    status = cloud_extractor_api.GetInstanceStatus(project, zone, instance_name)
    if status is None:
      log.status.Print('Instance has been deleted.')
      break

    if status in _TERMINAL_INSTANCE_STATES:
      log.status.Print('Instance is in state {}.'.format(status))
      break

    sleep_fn(POLL_INTERVAL_SECONDS)

  log.status.Print('Waiting for artifact to appear in GCS (up to 5 minutes)...')
  for _ in range(FINAL_ARTIFACT_RETRY_COUNT):
    artifact = cloud_extractor_api.FindOutputZipArtifact(output_ref)
    if artifact:
      artifact_uri, size_bytes = artifact
      log.status.Print('Extraction complete.')
      log.status.Print(
          'Artifact Path: {} ({} bytes)'.format(artifact_uri, size_bytes)
      )
      CheckForErrors(project, instance_id)
      return artifact_uri
    sleep_fn(FINAL_ARTIFACT_RETRY_SLEEP_SECONDS)

  CheckForErrors(project, instance_id)
  raise cloud_extractor_api.CloudExtractionError(
      'Extraction finished, but no non-empty artifact was found in {}.'
      ' The artifact may still appear in Cloud Storage after a few minutes'
      ' due to eventual consistency.'.format(output_ref.ToUrl())
  )


def Run(args, extract_type=extractor_flags.ExtractType.METADATA):
  """Executes the migration extractor in Cloud mode on Compute Engine.

  Args:
    args: argparse.Namespace, Parsed CLI arguments.
    extract_type: extractor_flags.ExtractType, The extraction subcommand type.

  Returns:
    str, The GCS URI of the produced `.zip` artifact.

  Raises:
    calliope_exceptions.InvalidArgumentException: If `--connector`, `--zone`, or
      `--output` is invalid.
    extractor_utils.BucketVerificationError: If the output GCS bucket fails
      ownership or public-access checks.
    cloud_utils.ServiceAccountSetupError: If the dedicated service account
      cannot be found or created.
    cloud_extractor_api.CloudExtractionError: If VM creation or extraction
      fails.
  """
  extractor_utils.ValidateConnector(args.connector, extract_type=extract_type)
  project = properties.VALUES.core.project.Get(required=True)
  zone, region = ResolveZoneAndRegion(args.zone)
  secret_concept = getattr(getattr(args, 'CONCEPTS', None), 'secret', None)
  secret_ref = secret_concept.Parse() if secret_concept else None
  output_ref = extractor_utils.VerifyOutputBucket(
      args.output, expected_owner=args.expected_owner
  )

  sa_email = cloud_utils.SetupServiceAccount(
      project=project,
      default_sa_name=DEFAULT_SERVICE_ACCOUNT_NAME,
      default_sa_display_name=DEFAULT_SERVICE_ACCOUNT_DISPLAY_NAME,
      roles=_SERVICE_ACCOUNT_ROLES,
      service_account=args.gce_service_account,
      service_account_user=args.service_account_user,
  )

  now_ts = int(time.time())
  run_id = 'run-{}'.format(now_ts)

  cleaned_args = extractor_utils.CleanDumperArgs(args.dumper_args)
  secret_name = cloud_utils.SetupSecretManager(
      project=project,
      region=region,
      payload='\n'.join(cleaned_args),
      secret_ref=secret_ref,
      default_secret_id='bqms-extractor-creds-{}'.format(run_id),
      labels={cloud_extractor_api.LABEL_KEY: run_id},
  )

  instance_name = args.gce_instance or 'cloud-extractor-{}'.format(now_ts)
  instance_id = cloud_extractor_api.CreateExtractorInstance(
      project=project,
      zone=zone,
      region=region,
      instance_name=instance_name,
      connector=args.connector,
      output_uri=args.output,
      secret_name=secret_name,
      sa_email=sa_email,
      run_id=run_id,
      startup_script_url=args.gce_startup_script_url,
      network=args.network,
      subnet=args.subnet,
      no_address=bool(args.no_address),
  )

  return WaitForCompletion(
      project=project,
      zone=zone,
      instance_name=instance_name,
      instance_id=instance_id,
      output_ref=output_ref,
  )

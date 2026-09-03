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
"""Command to submit a Device Run iOS XCTest session."""

import uuid

from apitools.base.py import encoding
from googlecloudsdk.api_lib import device_run
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.device_run import resource_args
from googlecloudsdk.command_lib.device_run import session_submit_ops
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _ValidateTestPath(path):
  """Validates that the path ends with .zip extension."""
  if not path.lower().endswith('.zip'):
    raise arg_parsers.ArgumentTypeError(
        f'Test file [{path}] must have .zip extension.'
    )
  return path


def _ValidateAppPath(path):
  """Validates that the path ends with .ipa extension."""
  if not path.lower().endswith('.ipa'):
    raise arg_parsers.ArgumentTypeError(
        f'App file [{path}] must have .ipa extension.'
    )
  return path


def _ValidateXctestrunPath(path):
  """Validates that the path ends with .xctestrun extension."""
  if not path.lower().endswith('.xctestrun'):
    raise arg_parsers.ArgumentTypeError(
        f'Xctestrun file [{path}] must have .xctestrun extension.'
    )
  return path


class SessionNameNotFoundError(exceptions.Error):
  """Raised when the session name cannot be found."""


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class XcTest(base.Command):
  """Submit a Device Run session with an iOS XCTest job."""

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser, 'submit session')
    parser.display_info.AddFormat(
        'table(job_name:label="JOB NAME", '
        'execution_name:label="EXECUTION NAME", '
        'result:label="EXECUTION RESULT")'
    )
    parser.add_argument(
        '--device',
        required=True,
        type=arg_parsers.ArgList(),
        action=arg_parsers.FlattenAction(dedup=False),
        metavar='DEVICE',
        help=(
            'Id of the device type to run the test on. Can be repeated to'
            ' specify multiple device types. A job will be created for each'
            ' specified device type.'
        ),
    )
    parser.add_argument(
        '--test',
        required=True,
        type=_ValidateTestPath,
        metavar='TEST_PATH',
        help=(
            'The path to the .zip file containing the iOS app and XCTest'
            ' files. Supports both Google Cloud Storage (`gs://...`) paths and'
            ' local filesystem paths. Any local file will be uploaded to'
            ' Google Cloud Storage prior to test execution.'
        ),
    )
    parser.add_argument(
        '--apps',
        metavar='APP_PATH',
        type=arg_parsers.ArgList(element_type=_ValidateAppPath),
        default=[],
        help=(
            'A list of additional application binary files (.ipa) to install'
            ' before running the test. The order of the applications in the'
            ' list determines their installation order on the device. Supports'
            ' both Google Cloud Storage (`gs://...`) paths and local filesystem'
            ' paths. Any local file will be uploaded to Google Cloud Storage'
            ' prior to test execution.'
        ),
    )
    parser.add_argument(
        '--xctestrun-file',
        type=_ValidateXctestrunPath,
        metavar='XCTESTRUN_FILE',
        help=(
            'The path to the custom .xctestrun file. Supports both Google'
            ' Cloud Storage (`gs://...`) paths and local filesystem paths.'
            ' Any local file will be uploaded to Google Cloud Storage prior'
            ' to test execution.'
        ),
    )

    parser.add_argument(
        '--xctest-timeout',
        type=arg_parsers.Duration(lower_bound='1m', upper_bound='1h'),
        help=(
            'Specify the maximum duration allowed for the XCTest run'
            ' (e.g., `10m`, `15m`, `1h`). The valid range is `1m` to `1h`.'
            ' If not specified, defaults to `5m`. It does not include any'
            ' time necessary to prepare and clean up the target device.'
        ),
    )
    parser.add_argument(
        '--other-files-to-push',
        metavar='SOURCE=BUNDLE_ID:DEST',
        type=arg_parsers.ArgDict(operators={'=': None, ' ': None}),
        action=arg_parsers.UpdateAction,
        default={},
        help=(
            'A dictionary of additional files to be pushed to the device before'
            ' running the test. The key is the source path of the file'
            ' (supports both Google Cloud Storage and local paths; local files'
            ' will be uploaded to Google Cloud Storage prior to test'
            ' execution), and the value is the destination path in the format'
            ' BUNDLE_ID:DEVICE_PATH.'
        ),
    )
    parser.add_argument(
        '--paths-to-pull',
        metavar='BUNDLE_ID:DEVICE_PATH',
        type=arg_parsers.ArgList(),
        default=[],
        help=(
            'A list of file or directory paths to pull from the device'
            ' following test completion, in the format BUNDLE_ID:DEVICE_PATH.'
        ),
    )
    parser.add_argument(
        '--video',
        type=str,
        choices=['always', 'on-failure'],
        help=(
            'Specify when to record video of the device screen during the'
            ' test run. Accepted values are `always` or `on-failure`.'
        ),
    )
    parser.add_argument(
        '--bucket-name',
        type=str,
        help=(
            'The name of a Google Cloud Storage bucket to store test'
            ' artifacts, including local input files and test output files.'
            ' If not specified, a default bucket named'
            ' ```gs://[PROJECT_ID]-devicerun``` will be used or created.'
        ),
    )
    parser.add_argument(
        '--flaky-test-attempts',
        type=int,
        help=(
            'Specify the maximum number of execution attempts per job'
            ' to handle flakiness. If not specified, defaults to 1.'
        ),
    )
    parser.add_argument(
        '--labels',
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(operators={'=': None, ' ': None}),
        action=arg_parsers.UpdateAction,
        default={},
        help=(
            'A dictionary of user-defined key-value labels to attach to the'
            ' session.'
        ),
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    if args.other_files_to_push:
      for src, dest in args.other_files_to_push.items():
        if ':' not in dest:
          raise calliope_exceptions.InvalidArgumentException(
              '--other-files-to-push',
              f'Destination [{dest}] must follow the format'
              ' BUNDLE_ID:DEVICE_PATH.',
          )

    if args.paths_to_pull:
      for path in args.paths_to_pull:
        if ':' not in path:
          raise calliope_exceptions.InvalidArgumentException(
              '--paths-to-pull',
              f'Path [{path}] must follow the format BUNDLE_ID:DEVICE_PATH.',
          )

    location_ref = args.CONCEPTS.location.Parse()
    client = device_run.SessionsClient(api_version='v1alpha')
    messages = client.messages

    storage_client = storage_api.StorageClient()
    bucket_name = args.bucket_name
    if not bucket_name:
      project = properties.VALUES.core.project.Get(required=True)
      bucket_name = session_submit_ops.GetDefaultBucketName(project)
      log.status.Print(
          f'Using the default GCS bucket [gs://{bucket_name}] for input and'
          ' result files. Will create the bucket if it does not exist.'
      )
      if location_ref.locationsId == 'global':
        location = None
      else:
        location = location_ref.locationsId
      storage_client.CreateBucketIfNotExists(
          bucket_name,
          project=project,
          location=location,
          check_ownership=True,
      )

    run_id = session_submit_ops.GetRunId()
    test_gcs = session_submit_ops.UploadFileIfNeeded(
        args.test, bucket_name, storage_client, run_id
    )

    xctestrun_gcs = None
    if args.xctestrun_file:
      xctestrun_gcs = session_submit_ops.UploadFileIfNeeded(
          args.xctestrun_file, bucket_name, storage_client, run_id
      )

    installables = []
    if args.apps:
      for app_ipa in args.apps:
        app_ipa_gcs = session_submit_ops.UploadFileIfNeeded(
            app_ipa, bucket_name, storage_client, run_id
        )
        installables.append(
            messages.InputFile(gcsInputFile=messages.GcsPath(path=app_ipa_gcs))
        )

    device_actions = []
    if installables:
      device_action = messages.DeviceAction(
          iosInstallPackages=messages.IosInstallPackagesDeviceAction(
              ipas=installables
          )
      )
      device_actions.append(device_action)

    if args.paths_to_pull:
      path_configs = []
      for path in args.paths_to_pull:
        bundle_id, device_path = path.split(':', 1)
        path_configs.append(
            messages.IosPullFilesDeviceActionPathConfig(
                bundleId=bundle_id, devicePath=device_path
            )
        )
      pull_action = messages.DeviceAction(
          iosPullFiles=messages.IosPullFilesDeviceAction(paths=path_configs)
      )
      device_actions.append(pull_action)

    if args.other_files_to_push:
      file_configs = []
      for src, dest in sorted(args.other_files_to_push.items()):
        bundle_id, dest_path = dest.split(':', 1)
        src_gcs = session_submit_ops.UploadFileIfNeeded(
            src, bucket_name, storage_client, run_id
        )
        file_configs.append(
            messages.IosPushFilesDeviceActionFileConfig(
                bundleId=bundle_id,
                destinationPath=dest_path,
                sourceFile=messages.InputFile(
                    gcsInputFile=messages.GcsPath(path=src_gcs)
                ),
            )
        )
      push_action = messages.DeviceAction(
          iosPushFiles=messages.IosPushFilesDeviceAction(
              fileConfigs=file_configs
          )
      )
      device_actions.append(push_action)

    if args.video:
      video_action = messages.DeviceAction(
          iosRecordVideo=messages.IosRecordVideoDeviceAction(
              discardOnPass=(args.video == 'on-failure')
          )
      )
      device_actions.append(video_action)

    xctest_timeout = (
        f'{args.xctest_timeout}s' if args.xctest_timeout is not None else None
    )

    test_zip_file = messages.InputFile(
        gcsInputFile=messages.GcsPath(path=test_gcs)
    )
    xctestrun_file = None
    if xctestrun_gcs:
      xctestrun_file = messages.InputFile(
          gcsInputFile=messages.GcsPath(path=xctestrun_gcs)
      )

    ios_xc_test = messages.IosXcTest(
        testsZip=test_zip_file,
        xctestrun=xctestrun_file,
        xcTestTimeout=xctest_timeout,
    )

    job_action = messages.JobAction(iosXcTest=ios_xc_test)

    labels = None
    if args.labels:
      labels = messages.JobConfig.LabelsValue(
          additionalProperties=[
              messages.JobConfig.LabelsValue.AdditionalProperty(key=k, value=v)
              for k, v in sorted(args.labels.items())
          ]
      )

    settings = None
    if args.flaky_test_attempts is not None:
      settings = messages.JobSettings(
          retrySettings=messages.RetrySettings(
              flakyTestRetryStrategy=messages.RetrySettingsFlakyTestRetryStrategy(
                  flakyTestAttempts=args.flaky_test_attempts
              )
          )
      )

    job_configs = []
    for device in args.device:
      device_requirement = messages.DeviceRequirement(deviceId=device)
      device_config = messages.DeviceConfig(
          requirement=device_requirement,
          actions=device_actions,
      )
      allocation_config = messages.AllocationConfig(
          deviceConfigs=[device_config]
      )
      job_config = messages.JobConfig(
          allocationConfig=allocation_config,
          action=job_action,
          labels=labels,
          settings=settings,
      )
      job_configs.append(job_config)

    gcs_path = f'gs://{bucket_name}/automation/sessions'
    output_directory_config = (
        messages.SessionConfigSessionOutputFileDirectoryConfig(
            gcsOutputDirectory=messages.GcsPath(path=gcs_path)
        )
    )
    session_config = messages.SessionConfig(
        displayName='xctest-session',
        jobConfigs=job_configs,
        outputDirectoryConfig=output_directory_config,
    )

    session = messages.Session(sessionConfig=session_config)
    request_id = str(uuid.uuid4())
    operation = client.Create(
        location_ref, session=session, request_id=request_id
    )
    operation_id = operation.name.split('/')[-1]

    log.status.Print()
    log.status.Print(
        f'Initiated long-running operation [{operation_id}] to create session.'
    )

    session_name = None
    if getattr(operation, 'metadata'):
      session_name = encoding.MessageToPyValue(operation.metadata).get('target')
    if not session_name:
      raise SessionNameNotFoundError(
          'Could not obtain session name from operation.'
      )

    session_id = session_name.split('/')[-1]

    log.status.Print(
        f'Creating session [{session_id}] in location'
        f' [{location_ref.locationsId}].'
    )

    log.status.Print(
        'Result files will be stored at'
        f' [https://console.cloud.google.com/storage/browser/{bucket_name}/automation/sessions/{session_id}/].'
    )

    if args.async_:
      return

    return session_submit_ops.WaitForSession(client, operation, session_name)


XcTest.detailed_help = {
    'DESCRIPTION': 'Submit a Device Run session with an iOS XCTest job.',
    'EXAMPLES': (
        """\
To submit an XCTest session on an iPhone 15 Pro, run:

  $ {command} --device=iphone15pro-17.2 --test=gs://my-bucket/SmokeTests.zip --bucket-name=my-bucket

To submit an XCTest session asynchronously without waiting for it to
complete, run:

  $ {command} --device=iphone15pro-17.2 --test=gs://my-bucket/SmokeTests.zip --bucket-name=my-bucket --async
"""
    ),
}

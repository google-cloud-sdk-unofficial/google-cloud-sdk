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
"""Command to submit a Device Run Android executable session."""

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


def _ParseLatLng(val):
  """Parses a latitude,longitude string into a tuple of floats."""
  try:
    lat_str, lng_str = val.split(',')
  except ValueError as exc:
    raise arg_parsers.ArgumentTypeError(
        f'Invalid coordinates [{val}]. '
        'Format must be latitude,longitude (e.g. 37.4220,-122.0841).'
    ) from exc
  try:
    lat = float(lat_str)
  except ValueError as exc:
    raise arg_parsers.ArgumentTypeError(
        f'Invalid latitude [{lat_str}] in coordinates. Must be a float.'
    ) from exc
  try:
    lng = float(lng_str)
  except ValueError as exc:
    raise arg_parsers.ArgumentTypeError(
        f'Invalid longitude [{lng_str}] in coordinates. Must be a float.'
    ) from exc

  if not -90.0 <= lat <= 90.0:
    raise arg_parsers.ArgumentTypeError(
        f'Latitude [{lat}] must be between -90.0 and 90.0.'
    )
  if not -180.0 <= lng <= 180.0:
    raise arg_parsers.ArgumentTypeError(
        f'Longitude [{lng}] must be between -180.0 and 180.0.'
    )
  return lat, lng


def _ValidateArgs(args):
  """Validates command arguments before execution."""
  if args.flaky_test_attempts is not None and args.flaky_test_attempts < 1:
    raise calliope_exceptions.InvalidArgumentException(
        '--flaky-test-attempts',
        'Must be at least 1.',
    )
  if args.bucket_name and '/' in args.bucket_name:
    raise calliope_exceptions.InvalidArgumentException(
        '--bucket-name',
        'Must be a bucket name only, without a `gs://` scheme or a path'
        ' (for example `my-bucket`, not `gs://my-bucket/results`). Artifacts'
        ' are always written under the `automation/` prefix of the bucket.',
    )


def _BuildDeviceActions(messages, args, bucket_name, storage_client, run_id):
  """Builds device actions list to configure on the test device."""
  device_actions = []

  # Always enable logcat and make it the first action.
  logcat_action = messages.DeviceAction(
      androidLogcat=messages.AndroidLogcatDeviceAction()
  )
  device_actions.append(logcat_action)

  if args.other_files_to_push:
    push_action = messages.DeviceAction(
        androidPushFiles=messages.AndroidPushFilesDeviceAction(
            fileConfigs=[
                messages.AndroidPushFilesDeviceActionFileConfig(
                    destinationPath=dest,
                    sourceFile=messages.InputFile(
                        gcsInputFile=messages.GcsPath(
                            path=session_submit_ops.UploadFileIfNeeded(
                                src, bucket_name, storage_client, run_id
                            )
                        )
                    ),
                )
                for src, dest in sorted(args.other_files_to_push.items())
            ]
        )
    )
    device_actions.append(push_action)

  if args.locale:
    locale_action = messages.DeviceAction(
        androidSwitchLocale=messages.AndroidSwitchLocaleDeviceAction(
            localeCode=args.locale
        )
    )
    device_actions.append(locale_action)

  if args.orientation:
    orientation_action = messages.DeviceAction(
        androidOrientation=messages.AndroidOrientationDeviceAction(
            orientation=args.orientation
        )
    )
    device_actions.append(orientation_action)

  if args.paths_to_pull:
    pull_action = messages.DeviceAction(
        androidPullFiles=messages.AndroidPullFilesDeviceAction(
            paths=args.paths_to_pull
        )
    )
    device_actions.append(pull_action)

  if args.video:
    video_action = messages.DeviceAction(
        androidRecordVideo=messages.AndroidRecordVideoDeviceAction(
            discardOnPass=(args.video == 'on-failure')
        )
    )
    device_actions.append(video_action)

  if args.dumpsys:
    dumpsys_action = messages.DeviceAction(
        androidDumpsys=messages.AndroidDumpsysDeviceAction(
            collectOnPass=(args.dumpsys == 'always')
        )
    )
    device_actions.append(dumpsys_action)

  if args.bugreport:
    bugreport_action = messages.DeviceAction(
        androidBugreport=messages.AndroidBugreportDeviceAction(
            collectOnPass=(args.bugreport == 'always')
        )
    )
    device_actions.append(bugreport_action)

  if args.coordinates:
    lat, lng = args.coordinates
    mock_location_action = messages.DeviceAction(
        androidMockLocation=messages.AndroidMockLocationDeviceAction(
            location=messages.LatLng(latitude=lat, longitude=lng)
        )
    )
    device_actions.append(mock_location_action)

  return device_actions


def _BuildJobAction(messages, args, executable_gcs):
  """Constructs the JobAction containing the Android executable payload."""
  executable_timeout = (
      f'{args.executable_timeout}s'
      if args.executable_timeout is not None
      else None
  )

  env_vars = None
  if args.executable_env_vars:
    env_prop_cls = messages.AndroidNativeBinary.EnvVarsValue.AdditionalProperty
    env_vars = messages.AndroidNativeBinary.EnvVarsValue(
        additionalProperties=[
            env_prop_cls(key=k, value=v)
            for k, v in sorted(args.executable_env_vars.items())
        ]
    )

  android_native_binary = messages.AndroidNativeBinary(
      androidNativeBinary=messages.InputFile(
          gcsInputFile=messages.GcsPath(path=executable_gcs)
      ),
      args=args.executable_args if args.executable_args else [],
      envVars=env_vars,
      executionTimeout=executable_timeout,
  )
  return messages.JobAction(androidNativeBinary=android_native_binary)


def _BuildJobConfigs(messages, args, job_action, device_actions):
  """Builds the list of JobConfig objects for each target device."""
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
                flakyTestAttempts=args.flaky_test_attempts,
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
    allocation_config = messages.AllocationConfig(deviceConfigs=[device_config])
    job_config = messages.JobConfig(
        allocationConfig=allocation_config,
        action=job_action,
        labels=labels,
        settings=settings,
    )
    job_configs.append(job_config)

  return job_configs


class SessionNameNotFoundError(exceptions.Error):
  """Raised when the session name cannot be found."""


class BucketNotFoundError(exceptions.Error):
  """Raised when an explicitly specified GCS bucket does not exist."""


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AndroidExecutable(base.Command):
  """Submit a Device Run session with an Android executable job."""

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
            'Id of the device type to run the executable on. Can be repeated'
            ' to specify multiple device types. A job will be created for each'
            ' specified device type.'
        ),
    )
    parser.add_argument(
        '--executable',
        required=True,
        metavar='EXECUTABLE_PATH',
        help=(
            'The path to the Android executable to run.'
            ' Supports both Google Cloud Storage (`gs://...`) paths and local'
            ' filesystem paths. Any local file will be uploaded to Google Cloud'
            ' Storage prior to execution.'
        ),
    )
    parser.add_argument(
        '--executable-args',
        metavar='ARG',
        type=arg_parsers.ArgList(),
        action=arg_parsers.FlattenAction(dedup=False),
        default=[],
        help=(
            'Arguments to pass to the executable when executing on the'
            ' device. Can be specified as a comma-separated list or by'
            ' repeating the flag. Each element becomes one argument, so a'
            ' space-separated command line must be rewritten in'
            ' comma-separated form, for example'
            ' `--executable-args="--input=a.tflite,--threads=4"`. To pass an'
            ' argument that itself contains a comma, prefix the value with'
            ' `^SEP^` to'
            ' choose a different separator, for example'
            ' `--executable-args="^;^--shape=1,224,224,3;--threads=4"`.'
        ),
    )
    parser.add_argument(
        '--executable-env-vars',
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(operators={'=': None, ' ': None}),
        action=arg_parsers.UpdateAction,
        default={},
        help=(
            'A dictionary of environment variables to set for the executable'
            ' process on the device.'
        ),
    )
    parser.add_argument(
        '--executable-timeout',
        type=arg_parsers.Duration(lower_bound='1m', upper_bound='3h'),
        help=(
            'Specify the maximum duration allowed for the executable to run'
            ' (e.g., `10m`, `15m`, `1h`). The valid range is `1m` to `3h`.'
            ' If not specified, defaults to `5m`. It does not include any'
            ' time necessary to prepare and clean up the target device.'
        ),
    )
    parser.add_argument(
        '--other-files-to-push',
        metavar='SOURCE=DEST',
        type=arg_parsers.ArgDict(operators={'=': None, ' ': None}),
        action=arg_parsers.UpdateAction,
        default={},
        help=(
            'A dictionary of additional files to be pushed to the device before'
            ' running the executable. The key is the source path of the file'
            ' (supports both Google Cloud Storage and local paths; local files'
            ' will be uploaded to Google Cloud Storage prior to execution), and'
            ' the value is the destination path on the device.'
        ),
    )
    parser.add_argument(
        '--paths-to-pull',
        metavar='DEVICE_PATH',
        type=arg_parsers.ArgList(),
        default=[],
        help=(
            'A list of file or directory paths to pull from the device'
            ' following execution completion.'
        ),
    )
    parser.add_argument(
        '--video',
        type=str,
        choices=['always', 'on-failure'],
        help=(
            'Specify when to record video of the device screen during the'
            ' run. Accepted values are `always` or `on-failure`.'
        ),
    )
    parser.add_argument(
        '--bucket-name',
        type=str,
        help="""\
The name of a Google Cloud Storage bucket to store artifacts, including
local input files and output files. If not specified, a default bucket named
```gs://[PROJECT_ID]-devicerun``` will be used or created.

A bucket named explicitly with this flag must already exist; only the default
bucket is created automatically. This flag accepts a bucket name only, without
a ```gs://``` scheme or a path.

The Google Cloud Storage bucket layout will be structured as follows:

  * gs://{bucket-name}/automation/
    * inputs/
      * 2026-05-29_10:13.026220_JZTM/
        * my_executable
        * ...
    * sessions/
      * my-session-id1/
        * job-000/
          * execution-000/
            * output.log
            * ...
""",
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
    parser.add_argument(
        '--orientation',
        type=str,
        choices=['portrait', 'landscape'],
        help='Orientation of the device for the execution.',
    )
    parser.add_argument(
        '--locale',
        type=str,
        help='Locale code to set on the device for the execution.',
    )
    parser.add_argument(
        '--coordinates',
        type=_ParseLatLng,
        metavar='LATITUDE,LONGITUDE',
        help=(
            'Specify the mock location coordinates (latitude and longitude)'
            ' to set on the device before running the test. The format is'
            ' latitude,longitude (e.g., 37.4220,-122.0841). Latitude must be'
            ' in the range [-90.0, 90.0] and longitude must be in the range'
            ' [-180.0, 180.0].'
        ),
    )
    parser.add_argument(
        '--dumpsys',
        type=str,
        choices=['always', 'on-failure'],
        help='Specify when to collect dumpsys logs from the device.',
    )
    parser.add_argument(
        '--bugreport',
        type=str,
        choices=['always', 'on-failure'],
        help='Specify when to collect bugreport from the device.',
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    _ValidateArgs(args)

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
    else:
      # An explicitly named bucket is never created on the user's behalf, so
      # verify it up front. Otherwise the only signal is an opaque
      # INVALID_ARGUMENT from session creation, long after the input files
      # have been uploaded.
      try:
        storage_client.GetBucket(bucket_name)
      except storage_api.BucketNotFoundError as e:
        raise BucketNotFoundError(
            f'Bucket [gs://{bucket_name}] does not exist or is not accessible.'
            ' Create it with:\n\n'
            f'  $ gcloud storage buckets create gs://{bucket_name}\n\n'
            'Or omit --bucket-name to use the default bucket, which is created'
            ' automatically.'
        ) from e

    run_id = session_submit_ops.GetRunId()
    executable_gcs = session_submit_ops.UploadFileIfNeeded(
        args.executable, bucket_name, storage_client, run_id
    )

    # 1. Device actions: configure device-level setup, logs, and files.
    device_actions = _BuildDeviceActions(
        messages, args, bucket_name, storage_client, run_id
    )

    # 2. Job action: build Android executable action payload.
    job_action = _BuildJobAction(messages, args, executable_gcs)

    # 3. Job configs: combine allocations, job action, retry settings, labels.
    job_configs = _BuildJobConfigs(messages, args, job_action, device_actions)

    gcs_path = f'gs://{bucket_name}/automation/sessions'
    output_directory_config = (
        messages.SessionConfigSessionOutputFileDirectoryConfig(
            gcsOutputDirectory=messages.GcsPath(path=gcs_path)
        )
    )
    session_config = messages.SessionConfig(
        displayName='android-executable-session',
        jobConfigs=job_configs,
        outputDirectoryConfig=output_directory_config,
    )

    session = messages.Session(sessionConfig=session_config)
    # The session ID is generated client-side so that the request stays
    # idempotent if it is retried; see GenerateSessionAndRequestIds.
    session_id, request_id = session_submit_ops.GenerateSessionAndRequestIds()
    operation = client.Create(
        location_ref,
        session=session,
        session_id=session_id,
        request_id=request_id,
    )
    operation_id = operation.name.split('/')[-1]

    # Print a blank line for spacing.
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

    session_submit_ops.PrintResultFilesLink(
        gcs_path, session_id, is_completed=False
    )

    if args.async_:
      return

    return session_submit_ops.WaitForSession(client, operation, session_name)


AndroidExecutable.detailed_help = {
    'DESCRIPTION': (
        'Submit a Device Run session with an Android executable job.'
    ),
    'EXAMPLES': (
        """\
To submit an Android executable session on a device with ID `my-device-id`, run:

  $ {command} --device=my-device-id --executable=gs://my-bucket/my_executable --executable-args="--flag1=value1,--flag2=value2" --bucket-name=my-bucket

To submit an Android executable session asynchronously without waiting for it to
complete, run:

  $ {command} --device=my-device-id --executable=gs://my-bucket/my_executable --bucket-name=my-bucket --async
"""
    ),
}

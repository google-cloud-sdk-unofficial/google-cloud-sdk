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
"""Command to submit a Device Run instrumentation session."""

import datetime
import os
import uuid

from apitools.base.py import encoding
from googlecloudsdk.api_lib import device_run
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.device_run import resource_args
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _GetRunId():
  timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M.%S%f')
  random_suffix = uuid.uuid4().hex[:4].upper()
  return f'{timestamp}_{random_suffix}'


def _UploadFileIfNeeded(path, bucket_name, storage_client, run_id):
  """Uploads a local file to GCS if it is not already a GCS path."""
  if path.startswith('gs://'):
    return path
  log.status.Print(f'Uploading [{path}].')
  target_gcs_path = (
      f'gs://{bucket_name}/automation/inputs/{run_id}/{os.path.basename(path)}'
  )
  target_obj_ref = storage_util.ObjectReference.FromUrl(target_gcs_path)
  storage_client.CopyFileToGCS(path, target_obj_ref)
  return target_gcs_path


def _GetDefaultBucketName(project_id):
  """Returns the default bucket name for the current project.

  Args:
    project_id: str, the Google Cloud project ID.

  Returns:
    GCS bucket name.
  """
  safe_project = (
      project_id.replace(':', '-').replace('.', '-').replace('google', 'elgoog')
  )

  return safe_project + '-devicerun'


def _ValidateAppPath(path):
  """Validates that the path ends with an allowed application file extension."""
  valid_extensions = ('.apk', '.aab', '.apks')
  if not path.lower().endswith(valid_extensions):
    raise arg_parsers.ArgumentTypeError(
        f'App file [{path}] must have one of the following extensions:'
        f' {", ".join(valid_extensions)}.'
    )
  return path


def _ValidateTestPath(path):
  """Validates that the path ends with .apk extension."""
  if not path.lower().endswith('.apk'):
    raise arg_parsers.ArgumentTypeError(
        f'Test file [{path}] must have .apk extension.'
    )
  return path


class SessionNameNotFoundError(exceptions.Error):
  """Raised when the session name cannot be found."""


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Instrumentation(base.Command):
  """Submit a Device Run session with an instrumentation job."""

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
            'The path to the APK file containing instrumentation tests.'
            ' Supports both Google Cloud Storage (`gs://...`) paths and local'
            ' filesystem paths. Any local file will be uploaded to Google Cloud'
            ' Storage prior to test execution.'
        ),
    )
    parser.add_argument(
        '--apps',
        metavar='APP_PATH',
        type=arg_parsers.ArgList(element_type=_ValidateAppPath),
        default=[],
        help=(
            'A list of application binary files (.apk, .aab, or .apks) to'
            ' install before running the test. The order of the applications in'
            ' the list determines their installation order on the device.'
            ' Supports both Google Cloud Storage (`gs://...`) paths and local'
            ' filesystem paths. Any local file will be uploaded to Google Cloud'
            ' Storage prior to test execution.'
        ),
    )
    parser.add_argument(
        '--bucket-name',
        type=str,
        help="""\
The name of a Google Cloud Storage bucket to store test artifacts, including
local input files, test output files, and smart sharding timing records. If
not specified, a default bucket named ```gs://[PROJECT_ID]-devicerun``` will be
used or created.

The Google Cloud Storage bucket layout will be structured as follows:

  * gs://{bucket-name}/automation/
    * inputs/
      * 2026-05-29_10:13.026220_JZTM/
        * app-debug.apk
        * app-debug-androidTest.apk
    * sessions/
      * my-session-id1/
        * job-000/
          * execution-000/
            * junit.xml
            * ...
          * execution-001/
            * junit.xml
            * ...
          * merged_junit.xml
      * my-session-id2/
        * ...
    * smart-sharding/
      * sharding-record-A.yaml
      * sharding-record-B.yaml
""",
    )
    parser.add_argument(
        '--test-runner-class',
        type=str,
        help=(
            'The instrumentation test runner class to use. If not specified, a'
            ' default runner class will be determined by examining the'
            ' application\'s manifest.'
        ),
    )
    parser.add_argument(
        '--test-targets',
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(operators={'=': None, ' ': None}),
        action=arg_parsers.UpdateActionWithAppend,
        default={},
        help="""\
A list of test targets or target filters to run. Each target must be fully
qualified with the package name or class name, in one of these formats:

  * `package package_name`
  * `notPackage com.package.to.skip`
  * `class package_name.class_name`
  * `class package_name.class_name#method_name`
  * `notClass com.foo.ClassToSkip`
  * `notClass com.foo.ClassName#testMethodToSkip`
  * `annotation com.foo.AnnotationToRun`
  * `notAnnotation com.foo.AnnotationToSkip`
  * `size [small|medium|large]`

Formats like `testfile` or `notTestfile` won't be supported. If empty, all
targets in the module will be run.
""",
    )
    parser.add_argument(
        '--additional-test-options',
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(operators={'=': None, ' ': None}),
        action=arg_parsers.UpdateAction,
        default={},
        help=(
            'A dictionary of additional options to pass to the instrumentation'
            ' test. Formats supported in test_targets are not allowed to be'
            ' used here.'
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
            ' running the test. The key is the source path of the file'
            ' (supports both Google Cloud Storage and local paths; local files'
            ' will be uploaded to Google Cloud Storage prior to test'
            ' execution), and the value is the destination path on the device.'
        ),
    )
    parser.add_argument(
        '--paths-to-pull',
        metavar='DEVICE_PATH',
        type=arg_parsers.ArgList(),
        default=[],
        help=(
            'A list of file or directory paths to pull from the device'
            ' following test completion.'
        ),
    )
    parser.add_argument(
        '--video',
        type=str,
        choices=['always', 'on-failure'],
        help=(
            'Specifies when to record video of the device screen during the'
            ' test run. Accepted values are `always` or `on-failure`.'
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
        '--sharding-option',
        type=str,
        choices=['uniform', 'smart'],
        help=(
            'Specifies the sharding strategy to partition the test execution'
            ' across multiple device allocations. Accepted values are `uniform`'
            ' or `smart`.'
        ),
    )
    parser.add_argument(
        '--uniform-shard-count',
        type=int,
        help=(
            'Specifies the total number of shards to create for uniform'
            ' sharding. Required when `--sharding-option=uniform`.'
        ),
    )
    parser.add_argument(
        '--smart-sharding-target-duration',
        type=arg_parsers.Duration(lower_bound='2m', upper_bound='1h'),
        help=(
            'Specifies the targeted execution time (e.g., `2m`, `10m`, `1h`)'
            ' per shard for smart sharding. The valid range is `2m` to `1h`.'
            ' Required when `--sharding-option=smart`.'
        ),
    )
    parser.add_argument(
        '--smart-sharding-record-name',
        type=str,
        help=(
            'Specifies the name of the smart sharding record file, excluding'
            ' the file extension. Required when `--sharding-option=smart`. This'
            ' file is located in the Google Cloud Storage bucket specified by'
            ' `--bucket-name` under the `smart-sharding/` directory with a'
            ' `.yaml` extension. If the file does not exist, it will be created'
            ' automatically; otherwise, its contents will be updated upon'
            ' session completion.'
        ),
    )
    parser.add_argument(
        '--flaky-test-attempts',
        type=int,
        help=(
            'Specifies the maximum number of execution attempts per test shard'
            ' to handle flakiness or infrastructure errors. If not specified,'
            ' defaults to 1.'
        ),
    )
    parser.add_argument(
        '--instrumentation-timeout',
        type=arg_parsers.Duration(lower_bound='1m', upper_bound='1h'),
        help=(
            'Specifies the maximum duration allowed for the instrumentation'
            ' test run (e.g., `10m`, `20s`, `1h`). The valid range is `1m` to'
            ' `1h`. If not specified, defaults to `5m`.'
        ),
    )
    parser.add_argument(
        '--orchestrator-version',
        type=str,
        help=(
            'Specifies the version of the Android Test Orchestrator to use'
            ' during test execution. If not specified, no orchestrator is'
            ' used. If set to `auto`, the system-default orchestrator version'
            ' is used.'
        ),
    )
    parser.add_argument(
        '--locale',
        type=str,
        help=(
            'Specifies the locale (language and region) to switch the device to'
            ' before running the test. The format is `language-region`, e.g.,'
            ' `en-US` or `zh-CN`. The typical language value is a two- or'
            ' three-letter language code as defined in ISO 639. The typical'
            ' region value is a two-letter ISO 3166 code or a three-digit UN'
            ' M.49 area code.'
        ),
    )
    parser.add_argument(
        '--orientation',
        type=str,
        choices=['portrait', 'landscape'],
        help=(
            'Specifies the orientation to set the device to before running the'
            ' test. Accepted values are `portrait` or `landscape`.'
        ),
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    if args.additional_test_options:
      invalid_keys = {
          'package',
          'notPackage',
          'class',
          'notClass',
          'annotation',
          'notAnnotation',
          'size',
      }.intersection(args.additional_test_options.keys())
      if invalid_keys:
        raise calliope_exceptions.InvalidArgumentException(
            '--additional-test-options',
            f'Keys {", ".join(sorted(invalid_keys))} are not allowed. '
            'Use --test-targets instead.',
        )

    if args.sharding_option == 'uniform' and args.uniform_shard_count is None:
      raise calliope_exceptions.RequiredArgumentException(
          '--uniform-shard-count',
          'Required when sharding-option is uniform.',
      )
    if (
        args.sharding_option == 'smart'
        and args.smart_sharding_target_duration is None
    ):
      raise calliope_exceptions.RequiredArgumentException(
          '--smart-sharding-target-duration',
          'Required when sharding-option is smart.',
      )
    if (
        args.sharding_option == 'smart'
        and args.smart_sharding_record_name is None
    ):
      raise calliope_exceptions.RequiredArgumentException(
          '--smart-sharding-record-name',
          'Required when sharding-option is smart.',
      )

    location_ref = args.CONCEPTS.location.Parse()
    client = device_run.SessionsClient(api_version='v1alpha')
    messages = client.messages

    storage_client = storage_api.StorageClient()
    bucket_name = args.bucket_name
    if not bucket_name:
      project = properties.VALUES.core.project.Get(required=True)
      bucket_name = _GetDefaultBucketName(project)
      log.status.Print(
          f'Using the default GCS bucket [gs://{bucket_name}] for input and'
          ' result files. Will create the bucket if it does not exist.'
      )
      if location_ref.locationsId == 'global':
        # Creating STANDARD buckets with locationConstraint GLOBAL is not
        # allowed. Fallback to GCS default location.
        location = None
      else:
        location = location_ref.locationsId
      storage_client.CreateBucketIfNotExists(
          bucket_name,
          project=project,
          location=location,
          check_ownership=True,
      )

    run_id = _GetRunId()
    test_gcs = _UploadFileIfNeeded(
        args.test, bucket_name, storage_client, run_id
    )

    installables = []
    if args.apps:
      for app_apk in args.apps:
        app_apk_gcs = _UploadFileIfNeeded(
            app_apk, bucket_name, storage_client, run_id
        )
        installables.append(
            messages.AndroidInstallable(
                files=[
                    messages.InputFile(
                        gcsInputFile=messages.GcsPath(path=app_apk_gcs)
                    )
                ],
            )
        )

    device_actions = []
    if installables:
      device_action = messages.DeviceAction(
          androidInstallPackages=messages.AndroidInstallPackagesDeviceAction(
              installables=installables
          )
      )
      device_actions.append(device_action)

    if args.other_files_to_push:
      push_action = messages.DeviceAction(
          androidPushFiles=messages.AndroidPushFilesDeviceAction(
              fileConfigs=[
                  messages.FileConfig(
                      destinationPath=dest,
                      sourceFile=messages.InputFile(
                          gcsInputFile=messages.GcsPath(
                              path=_UploadFileIfNeeded(
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

    logcat_action = messages.DeviceAction(
        androidLogcat=messages.AndroidLogcatDeviceAction()
    )
    device_actions.append(logcat_action)

    test_installable = messages.AndroidInstallable(
        files=[
            messages.InputFile(gcsInputFile=messages.GcsPath(path=test_gcs))
        ],
    )

    test_targets = []
    if args.test_targets:
      for k, v_or_list in sorted(args.test_targets.items()):
        if isinstance(v_or_list, list):
          for v in v_or_list:
            test_targets.append(f'{k} {v}')
        else:
          test_targets.append(f'{k} {v_or_list}')

    additional_test_options = None
    if args.additional_test_options:
      add_prop_cls = (
          messages.AndroidInstrumentationTest.AdditionalTestOptionsValue.AdditionalProperty
      )
      additional_test_options = (
          messages.AndroidInstrumentationTest.AdditionalTestOptionsValue(
              additionalProperties=[
                  add_prop_cls(key=k, value=v)
                  for k, v in sorted(args.additional_test_options.items())
              ]
          )
      )

    test_runner_class = (
        args.test_runner_class if args.test_runner_class else None
    )
    orchestrator_version = (
        args.orchestrator_version if args.orchestrator_version else None
    )
    instrumentation_timeout = (
        f'{args.instrumentation_timeout}s'
        if args.instrumentation_timeout is not None
        else None
    )

    uniform_sharding = None
    smart_sharding = None
    if args.sharding_option == 'uniform':
      uniform_sharding = messages.UniformSharding(
          shardCount=args.uniform_shard_count
      )
    elif args.sharding_option == 'smart':
      record_path = (
          f'gs://{bucket_name}/automation/smart-sharding/'
          f'{args.smart_sharding_record_name}.yaml'
      )
      smart_sharding = messages.SmartSharding(
          targetedShardDuration=f'{args.smart_sharding_target_duration}s',
          timingRecord=messages.InputFile(
              gcsInputFile=messages.GcsPath(path=record_path)
          ),
      )

    android_instrumentation_test = messages.AndroidInstrumentationTest(
        testInstallable=test_installable,
        testRunnerClass=test_runner_class,
        testTargets=test_targets,
        additionalTestOptions=additional_test_options,
        uniformSharding=uniform_sharding,
        smartSharding=smart_sharding,
        instrumentationTimeout=instrumentation_timeout,
        orchestratorVersion=orchestrator_version,
    )
    job_action = messages.JobAction(
        androidInstrumentationTest=android_instrumentation_test
    )

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
              flakyTestRetryStrategy=messages.FlakyTestRetryStrategy(
                  flakyTestAttempts=args.flaky_test_attempts
              )
          )
      )

    job_configs = []
    for device in args.device:
      device_requirement = messages.DeviceRequirement(deviceId=device)
      device_config = messages.DeviceConfig(
          actions=device_actions,
          requirement=device_requirement,
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
    output_directory_config = messages.SessionOutputFileDirectoryConfig(
        gcsOutputDirectory=messages.GcsPath(path=gcs_path)
    )
    session_config = messages.SessionConfig(
        displayName='instrumentation-session',
        jobConfigs=job_configs,
        outputDirectoryConfig=output_directory_config,
    )

    session = messages.Session(sessionConfig=session_config)
    operation = client.Create(location_ref, session=session)
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

    log.status.Print(
        f'Result files will be stored at'
        f' [gs://{bucket_name}/automation/sessions/{session_id}/].'
    )

    if args.async_:
      return

    operation_ref = resources.REGISTRY.ParseRelativeName(
        operation.name,
        collection='devicerun.projects.locations.operations',
    )
    operations_client = device_run.OperationsClient(api_version='v1alpha')
    poller = device_run.DeviceRunOperationPoller(
        resource_service=client.service,
        operations_service=operations_client.service,
        resource_ref=None,
    )
    waiter.WaitFor(
        poller,
        operation_ref,
        f'Waiting for session [{session_id}] to complete.',
    )
    session_ref = resources.REGISTRY.ParseRelativeName(
        session_name,
        collection='devicerun.projects.locations.sessions',
    )
    session = client.Get(session_ref)
    result_type = (
        session.sessionReport.result.resultType
        if session.sessionReport and session.sessionReport.result
        else None
    )

    rows = []
    if session.sessionReport and session.sessionReport.jobReports:
      for job_report in session.sessionReport.jobReports:
        job_name = job_report.displayName
        if job_report.executionReports:
          for exec_report in job_report.executionReports:
            exec_name = exec_report.displayName
            result = str(exec_report.result.resultType)
            rows.append({
                'job_name': job_name,
                'execution_name': exec_name,
                'result': result,
            })
        else:
          result = (
              str(job_report.result.resultType)
              if job_report.result and job_report.result.resultType
              else ''
          )
          rows.append({
              'job_name': job_name,
              'execution_name': '',
              'result': result,
          })

    # Print a blank line for spacing.
    log.status.Print()
    log.status.Print(
        f'Session [{session_id}] finished with result [{result_type}].'
    )

    return rows


Instrumentation.detailed_help = {
    'DESCRIPTION':
        'Submit a Device Run session with an instrumentation job.',
    'EXAMPLES':
        """\
To submit an instrumentation session in location `us-central1` on a device
with ID `my-device-id`, run:

  $ {command} --location=us-central1 --device=my-device-id --apps=gs://my-bucket/app.apk --test=gs://my-bucket/test.apk --bucket-name=my-bucket

To submit an instrumentation session asynchronously without waiting for it to
complete, run:

  $ {command} --location=us-central1 --device=my-device-id --apps=gs://my-bucket/app.apk --test=gs://my-bucket/test.apk --bucket-name=my-bucket --async
""",
}

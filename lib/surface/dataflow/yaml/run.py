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
"""Implementation of gcloud dataflow yaml run command."""

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import dataflow_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Run(base.Command):
  """Runs a job from the specified path."""

  detailed_help = {
      'DESCRIPTION': (
          'Runs a job from the specified YAML description or '
          'Cloud Storage path.'
      ),
      'EXAMPLES': """\
          To run a job from YAML, run:

            $ {command} my-job --yaml-pipeline-file=gs://yaml-path --region=europe-west1
          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    parser.add_argument(
        'job_name', metavar='JOB_NAME', help='Unique name to assign to the job.'
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--yaml-pipeline-file',
        help=(
            'Path of a file defining the YAML pipeline to run. '
            "(Must be a local file or a URL beginning with 'gs://'.)"
        ),
    )

    group.add_argument(
        '--yaml-pipeline', help='Inline definition of the YAML pipeline to run.'
    )

    parser.add_argument(
        '--region',
        metavar='REGION_ID',
        help=(
            "Region ID of the job's regional endpoint. "
            + dataflow_util.DEFAULT_REGION_MESSAGE
        ),
    )

    parser.add_argument(
        '--pipeline-options',
        metavar='OPTIONS=VALUE;OPTION=VALUE',
        type=arg_parsers.ArgDict(),
        action=actions.DeprecationAction(
            '--pipeline-options',
            warn=(
                'The `--pipeline-options` flag is deprecated. Pipeline options '
                'should be passed using --additional-pipeline-options flag.'
            ),
            action=arg_parsers.UpdateAction),
        help='Pipeline options to pass to the job.',
    )

    parser.add_argument(
        '--jinja-variables',
        metavar='JSON_OBJECT',
        help='Jinja2 variables to be used in reifying the yaml.',
    )

    parser.add_argument(
        '--template-file-gcs-location',
        help=('Google Cloud Storage location of the YAML template to run. '
              "(Must be a URL beginning with 'gs://'.)"),
        type=arg_parsers.RegexpValidator(r'^gs://.*',
                                         'Must begin with \'gs://\''),
    )

    parser.add_argument(
        '--network',
        help=(
            'Compute Engine network for launching worker instances to run '
            'the pipeline.  If not set, the default network is used.'
        ),
    )

    parser.add_argument(
        '--subnetwork',
        help=(
            'Compute Engine subnetwork for launching worker instances to '
            'run the pipeline.  If not set, the default subnetwork is used.'
        ),
    )

    parser.add_argument(
        '--service-account-email',
        type=arg_parsers.RegexpValidator(r'.*@.*\..*',
                                         'must provide a valid email address'),
        help=(
            'Service account to run the workers as.'
        ),
    )

    parser.add_argument(
        '--additional-experiments',
        metavar='ADDITIONAL_EXPERIMENTS',
        type=arg_parsers.ArgList(),
        action=arg_parsers.UpdateAction,
        help=(
            'Additional experiments to pass to the job. Example: '
            '--additional-experiments=experiment1,experiment2=value2'
        )
    )

    parser.add_argument(
        '--additional-pipeline-options',
        metavar='ADDITIONAL_PIPELINE_OPTIONS',
        type=arg_parsers.ArgList(),
        action=arg_parsers.UpdateAction,
        help=(
            'Additional pipeline options to pass to the job. Example: '
            '--additional-pipeline-options=option1=value1,option2=value2 '
            'For a list of available options, see the Dataflow reference: '
            'https://cloud.google.com/dataflow/docs/reference/pipeline-options'
        ),
    )

    parser.add_argument(
        '--additional-user-labels',
        metavar='ADDITIONAL_USER_LABELS',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.UpdateAction,
        help=(
            'Additional user labels to pass to the job. Example: '
            "--additional-user-labels='key1=value1,key2=value2'"
        ),
    )

    parser.add_argument(
        '--disable-public-ips',
        action=actions.StoreBooleanProperty(
            properties.VALUES.dataflow.disable_public_ips
        ),
        help=(
            'If specified, Cloud Dataflow workers will not use public IP'
            ' addresses.'
        ),
    )

    parser.add_argument(
        '--staging-location',
        help=(
            'Google Cloud Storage location to stage local files. '
            'If not set, defaults to the value for --temp-location.'
            "(Must be a URL beginning with 'gs://'.)"
        ),
        type=arg_parsers.RegexpValidator(
            r'^gs://.*', "Must begin with 'gs://'"
        ),
    )

    parser.add_argument(
        '--temp-location',
        help=(
            'Google Cloud Storage location to stage temporary files. '
            'If not set, defaults to the value for --staging-location.'
            "(Must be a URL beginning with 'gs://'.)"
        ),
        type=arg_parsers.RegexpValidator(
            r'^gs://.*', "Must begin with 'gs://'"
        ),
    )

    parser.add_argument(
        '--max-workers', type=int, help='Maximum number of workers to run.'
    )

    parser.add_argument(
        '--num-workers', type=int, help='Initial number of workers to use.'
    )

    parser.add_argument(
        '--worker-machine-type',
        help=(
            'Type of machine to use for workers. Defaults to server-specified.'
        ),
    )

    parser.add_argument(
        '--launcher-machine-type',
        help=(
            'The machine type to use for launching the job. The default is '
            'n1-standard-1.'
        ),
    )

    parser.add_argument(
        '--dataflow-kms-key', help='Cloud KMS key to protect the job resources.'
    )

    parser.add_argument(
        '--enable-streaming-engine',
        action=actions.StoreBooleanProperty(
            properties.VALUES.dataflow.enable_streaming_engine
        ),
        help='Enable Streaming Engine for the streaming job.',
    )

    streaming_update_args = parser.add_argument_group()
    streaming_update_args.add_argument(
        '--transform-name-mappings',
        metavar='TRANSFORM_NAME_MAPPINGS',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.UpdateAction,
        help=
        ('Transform name mappings for the streaming update job.'))

    streaming_update_args.add_argument(
        '--update',
        help=('Specify this flag to update a streaming job.'),
        action=arg_parsers.StoreTrueFalseAction,
        required=True)

  def Run(self, args):
    """Runs the command.

    Args:
      args: The arguments that were provided to this command invocation.

    Returns:
      A Job message.
    """
    parameters = dict(args.pipeline_options or {})

    # These are required and mutually exclusive due to the grouping above.
    if args.yaml_pipeline_file:
      yaml_contents = _try_get_yaml_contents(args.yaml_pipeline_file)
      if yaml_contents is None:
        parameters['yaml_pipeline_file'] = args.yaml_pipeline_file
      else:
        parameters['yaml_pipeline'] = yaml_contents

    else:
      parameters['yaml_pipeline'] = args.yaml_pipeline

    if args.jinja_variables:
      parameters['jinja_variables'] = args.jinja_variables

    if 'yaml_pipeline' in parameters and 'jinja-variables' not in parameters:
      _validate_yaml(parameters['yaml_pipeline'])

    region_id = _get_region_from_yaml_or_default(
        parameters.get('yaml_pipeline'), args
    )

    gcs_location = (
        args.template_file_gcs_location
        or apis.Templates.YAML_TEMPLATE_GCS_LOCATION.format(region_id)
    )

    arguments = apis.TemplateArguments(
        project_id=properties.VALUES.core.project.Get(required=True),
        region_id=region_id,
        job_name=args.job_name,
        gcs_location=gcs_location,
        parameters=parameters,
        network=args.network,
        subnetwork=args.subnetwork,
        service_account_email=args.service_account_email,
        additional_experiments=args.additional_experiments,
        additional_pipeline_options=args.additional_pipeline_options,
        additional_user_labels=args.additional_user_labels,
        disable_public_ips=properties.VALUES.dataflow.disable_public_ips.GetBool(),
        staging_location=args.staging_location,
        temp_location=args.temp_location,
        max_workers=args.max_workers,
        num_workers=args.num_workers,
        worker_machine_type=args.worker_machine_type,
        launcher_machine_type=args.launcher_machine_type,
        kms_key_name=args.dataflow_kms_key,
        enable_streaming_engine=properties.VALUES.dataflow.enable_streaming_engine.GetBool(),
        transform_name_mappings=args.transform_name_mappings,
        streaming_update=args.update,
    )
    return apis.Templates.CreateJobFromFlexTemplate(arguments)


def _validate_yaml(yaml_pipeline):
  # TODO(b/320740846): Do more complete validation without requiring importing
  # the entire beam library.
  try:
    _ = yaml.load(yaml_pipeline)
  except Exception as exn:
    raise ValueError('yaml_pipeline must be a valid yaml.') from exn


def _get_region_from_yaml_or_default(yaml_pipeline, args):
  """Gets the region from yaml pipeline or args, or falls back to default."""
  region = args.region
  options_region = None
  try:
    pipeline_data = yaml.load(yaml_pipeline)
    if not pipeline_data:
      return dataflow_util.GetRegion(args)
    if 'options' in pipeline_data and 'region' in pipeline_data['options']:
      options_region = pipeline_data['options']['region']
      if '{' in options_region or '}' in options_region:
        raise yaml.YAMLParseError(
            'yaml pipeline contains unparsable region: {0}. Found curly braces '
            'in region. Falling back to default region.'.format(options_region)
        )
  except yaml.YAMLParseError as exn:
    if not region:
      print(
          'Failed to get region from yaml pipeline: {0}. If using jinja '
          'variables, parsing may fail. Falling back to default '
          'region.'.format(exn)
      )

  if options_region:
    if region and region != options_region:
      raise ValueError(
          'Region specified in yaml pipeline options ({0}) does not match'
          ' region specified in command line ({1})'.format(
              options_region, region
          )
      )
    return options_region

  return dataflow_util.GetRegion(args)


def _try_get_yaml_contents(yaml_pipeline_file):
  """Reads yaml contents from the specified file if it is accessable."""
  if not yaml_pipeline_file.startswith('gs://'):
    return files.ReadFileContents(yaml_pipeline_file)

  storage_client = storage_api.StorageClient()
  obj_ref = storage_util.ObjectReference.FromUrl(yaml_pipeline_file)
  try:
    return storage_client.ReadObject(obj_ref).read().decode('utf-8')
  except Exception as e:  # pylint: disable=broad-exception-caught
    print(
        'Unable to read file {0} due to incorrect file path or insufficient'
        ' read permissions. Will not be able to validate the yaml pipeline or'
        ' determine the region from the yaml pipeline'
        ' options. Error: {1}'.format(yaml_pipeline_file, e)
    )

  return None

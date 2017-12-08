# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Implementation of gcloud genomics pipelines run.
"""
from googlecloudsdk.api_lib import genomics as lib
from googlecloudsdk.api_lib.genomics import exceptions
from googlecloudsdk.api_lib.genomics import genomics_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


def _ValidateAndMergeArgInputs(args):
  """Turn args.inputs and args.inputs_from_file dicts into a single dict.

  Args:
    args: The parsed command-line arguments

  Returns:
    A dict that is the merge of args.inputs and args.inputs_from_file
  Raises:
    files.Error
  """

  # If no inputs from file, then no validation or merge needed
  if not args.inputs_from_file:
    return args.inputs

  # Initialize the merged dictionary
  arg_inputs = {}

  if args.inputs:
    # Validate args.inputs and args.inputs-from-file do not overlap
    overlap = set(args.inputs.keys()).intersection(
        set(args.inputs_from_file.keys()))
    if overlap:
      raise exceptions.GenomicsError(
          '--{0} and --{1} may not specify overlapping values: {2}'
          .format('inputs', 'inputs-from-file', ', '.join(overlap)))

    # Add the args.inputs
    arg_inputs.update(args.inputs)

  # Read up the inputs-from-file and add the values from the file
  for key, value in args.inputs_from_file.iteritems():
    arg_inputs[key] = files.GetFileContents(value)

  return arg_inputs


class Run(base.Command):
  """Defines and runs a pipeline.

  A pipeline is a transformation of a set of inputs to a set of outputs.
  Supports docker-based commands.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        '--pipeline-file',
        required=True,
        help='''A YAML or JSON file containing a Pipeline object. See
          [](https://cloud.google.com/genomics/reference/rest/v1alpha2/pipelines#Pipeline)

          YAML Example:
            name: hello world

            inputParameters:
            - name: greeting
              defaultValue: Hello
            - name: object
              defaultValue: World

            outputParameters:
            - name: outputFile
              localCopy:
                path: /data/output/greeting.txt
                disk: boot

            resources:
              minimumCpuCores: 1
              minimumRamGb: 1
              preemptible: true

            docker:
              imageName: ubuntu
              cmd: >
                echo "${greeting} ${object}" > /data/output/greeting.txt
        ''')

    parser.add_argument(
        '--inputs',
        category=base.COMMONLY_USED_FLAGS,
        type=arg_parsers.ArgDict(),
        action=arg_parsers.FloatingListValuesCatcher(
            arg_parsers.UpdateAction,
            switch_value={}),
        help='''Map of input PipelineParameter names to values.
            Used to pass literal parameters to the pipeline, and to specify
            input files in Google Cloud Storage that will have a localCopy
            made. Specified as a comma-separated list: --inputs
            file=gs://my-bucket/in.txt,name=hello''')

    parser.add_argument(
        '--inputs-from-file',
        category=base.COMMONLY_USED_FLAGS,
        type=arg_parsers.ArgDict(),
        action=arg_parsers.FloatingListValuesCatcher(
            arg_parsers.UpdateAction,
            switch_value={}),
        help='''Map of input PipelineParameter names to values.
            Used to pass literal parameters to the pipeline where values come
            from local files; this can be used to send large pipeline input
            parameters, such as code, data, or configuration values.
            Specified as a comma-separated list:
            --inputs-from-file script=myshellscript.sh,pyfile=mypython.py''')

    parser.add_argument(
        '--outputs',
        category=base.COMMONLY_USED_FLAGS,
        type=arg_parsers.ArgDict(),
        action=arg_parsers.FloatingListValuesCatcher(
            arg_parsers.UpdateAction,
            switch_value={}),
        help='''Map of output PipelineParameter names to values.
            Used to specify output files in Google Cloud Storage that will be
            made from a localCopy. Specified as a comma-separated list:
            --outputs ref=gs://my-bucket/foo,ref2=gs://my-bucket/bar''')

    parser.add_argument(
        '--logging',
        category=base.COMMONLY_USED_FLAGS,
        help='''The location in Google Cloud Storage to which the pipeline logs
            will be copied. Can be specified as a fully qualified directory
            path, in which case logs will be output with a unique identifier
            as the filename in that directory, or as a fully specified path,
            which must end in `.log`, in which case that path will be
            used. Stdout and stderr logs from the run are also generated and
            output as `-stdout.log` and `-stderr.log`.''')

    parser.add_argument(
        '--memory',
        category=base.COMMONLY_USED_FLAGS,
        type=float,
        help='''The number of GB of RAM needed to run the pipeline. Overrides
             any value specified in the pipeline-file.''')

    parser.add_argument(
        '--disk-size',
        category=base.COMMONLY_USED_FLAGS,
        default=None,
        help='''The disk size(s) in GB, specified as a comma-separated list of
            pairs of disk name and size. For example:
            --disk-size "name:size,name2:size2".
            Overrides any values specified in the pipeline-file.''')

    parser.add_argument(
        '--preemptible',
        category=base.COMMONLY_USED_FLAGS,
        action='store_true',
        help='''Whether to use a preemptible VM for this pipeline. The
            "resource" section of the pipeline-file must also set preemptible
            to "true" for this flag to take effect.''')

    parser.add_argument(
        '--run-id',
        help='''Optional caller-specified identifier for this run of the
             pipeline.''')

    parser.add_argument(
        '--service-account-email',
        default='default',
        help='''The service account used to run the pipeline. If unspecified,
            defaults to the Compute Engine service account for your project.''')

    parser.add_argument(
        '--service-account-scopes',
        type=arg_parsers.ArgList(),
        default=[],
        help='''List of additional scopes to be made available for this service
             account. The following scopes are always requested:
             https://www.googleapis.com/auth/genomics,
             https://www.googleapis.com/auth/compute, and
             https://www.googleapis.com/auth/devstorage.full_control''')

    parser.add_argument(
        '--zones',
        type=arg_parsers.ArgList(),
        completion_resource='compute.zones',
        help='''List of Compute Engine zones the pipeline can run in''')

  @genomics_util.ReraiseHttpException
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: argparse.Namespace, All the arguments that were provided to this
        command invocation.

    Raises:
      files.Error: A file argument could not be read.
      GenomicsError: User input was invalid.
      HttpException: An http error response was received while executing api
          request.
    Returns:
      Operation representing the running pipeline.
    """
    apitools_client = genomics_util.GetGenomicsClient('v1alpha2')
    genomics_messages = genomics_util.GetGenomicsMessages('v1alpha2')

    pipeline = genomics_util.GetFileAsMessage(
        args.pipeline_file,
        genomics_messages.Pipeline,
        self.context[lib.STORAGE_V1_CLIENT_KEY])
    pipeline.projectId = genomics_util.GetProjectId()

    arg_inputs = _ValidateAndMergeArgInputs(args)

    inputs = genomics_util.ArgDictToAdditionalPropertiesList(
        arg_inputs,
        genomics_messages.RunPipelineArgs.InputsValue.AdditionalProperty)
    outputs = genomics_util.ArgDictToAdditionalPropertiesList(
        args.outputs,
        genomics_messages.RunPipelineArgs.OutputsValue.AdditionalProperty)

    # Set "overrides" on the resources. If the user did not pass anything on
    # the command line, do not set anything in the resource: preserve the
    # user-intent "did not set" vs. "set an empty value/list"

    resources = genomics_messages.PipelineResources(
        preemptible=args.preemptible)
    if args.memory:
      resources.minimumRamGb = args.memory
    if args.disk_size:
      resources.disks = []
      for disk_encoding in args.disk_size.split(','):
        disk_args = disk_encoding.split(':', 1)
        resources.disks.append(genomics_messages.Disk(
            name=disk_args[0],
            sizeGb=int(disk_args[1])
        ))
    if args.zones:
      resources.zones = args.zones

    request = genomics_messages.RunPipelineRequest(
        ephemeralPipeline=pipeline,
        pipelineArgs=genomics_messages.RunPipelineArgs(
            inputs=genomics_messages.RunPipelineArgs.InputsValue(
                additionalProperties=inputs),
            outputs=genomics_messages.RunPipelineArgs.OutputsValue(
                additionalProperties=outputs),
            clientId=args.run_id,
            logging=genomics_messages.LoggingOptions(gcsPath=args.logging),
            projectId=genomics_util.GetProjectId(),
            serviceAccount=genomics_messages.ServiceAccount(
                email=args.service_account_email,
                scopes=args.service_account_scopes),
            resources=resources))
    return apitools_client.pipelines.Run(request)

  def Display(self, args_unused, operation):
    """This method is called to print the result of the Run() method.

    Args:
      args_unused: The arguments that command was run with.
      operation: The value returned from the Run() method.
    """
    log.Print('Running: [{0}]'.format(operation.name))

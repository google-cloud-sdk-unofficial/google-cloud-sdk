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
from googlecloudsdk.api_lib.genomics import genomics_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


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
        https://cloud.google.com/genomics/reference/rest/v1alpha2/pipelines#Pipeline

        Example:
        {
          "name": "hello",
          "inputParameters": [
            {"name":"greeting"}
          ],
          "resources": {
            "minimumCpuCores":1,
            "minimumRamGb":1
          },
          "docker": {
          "imageName": "ubuntu",
          "cmd": "echo $greeting"
          }
        }
        ''')

    parser.add_argument(
        '--inputs',
        nargs='+',
        default=[],
        category=base.COMMONLY_USED_FLAGS,
        type=arg_parsers.ArgDict(),
        help='''Map of input PipelineParameter names to values.
        Used to pass literal parameters to the pipeline, and to specify
        input files in Google Cloud Storage that will have a localCopy
        made.  Specified as a comma-separated list: --inputs
        file=gs://my-bucket/in.txt,name=hello''')

    parser.add_argument(
        '--outputs',
        nargs='+',
        default=[],
        category=base.COMMONLY_USED_FLAGS,
        type=arg_parsers.ArgDict(),
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
        used. Stdout and stderr logs from the run are also generated and output
        as `-stdout.log` and `-stderr.log`.''')

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
        type=bool,
        help='''Whether to use a preemptible VM for this pipeline, if the
        pipeline-file allows preemptible VMs.''')

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
        nargs='+',
        default=['https://www.googleapis.com/auth/genomics',
                 'https://www.googleapis.com/auth/compute',
                 'https://www.googleapis.com/auth/devstorage.full_control'],
        help='''List of scopes to be made available for this service
             account. If unspecified, defaults to:
             https://www.googleapis.com/auth/genomics,
             https://www.googleapis.com/auth/compute, and
             https://www.googleapis.com/auth/devstorage.full_control''')

  @genomics_util.ReraiseHttpException
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: argparse.Namespace, All the arguments that were provided to this
        command invocation.

    Raises:
      GenomicsError: User input was invalid.
      HttpException: An http error response was received while executing api
          request.
    Returns:
      Operation representing the running pipeline.
    """
    apitools_client = self.context[lib.GENOMICS_APITOOLS_V1A2_CLIENT_KEY]
    genomics_messages = self.context[lib.GENOMICS_MESSAGES_V1A2_MODULE_KEY]

    pipeline = genomics_util.GetFileAsMessage(
        args.pipeline_file,
        genomics_messages.Pipeline,
        self.context[lib.STORAGE_V1_CLIENT_KEY])
    pipeline.projectId = genomics_util.GetProjectId()

    inputs = genomics_util.ArgDictToAdditionalPropertiesList(
        args.inputs,
        genomics_messages.RunPipelineArgs.InputsValue.AdditionalProperty)
    outputs = genomics_util.ArgDictToAdditionalPropertiesList(
        args.outputs,
        genomics_messages.RunPipelineArgs.OutputsValue.AdditionalProperty)

    resources = genomics_messages.PipelineResources(
        preemptible=args.preemptible)
    if args.memory:
      resources.minimumRamGb = args.memory
    if args.disk_size:
      resources.disks = []
      for disk_encoding in args.disk_size.split(','):
        disk_args = disk_encoding.split(':')
        resources.disks.append(genomics_messages.Disk(
            name=disk_args[0],
            sizeGb=int(disk_args[1])
        ))

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

# Copyright 2015 Google Inc. All Rights Reserved.
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

"""'functions deploy' command."""
import httplib
import os
import random
import string
from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.functions import cloud_storage as storage
from googlecloudsdk.api_lib.functions import exceptions
from googlecloudsdk.api_lib.functions import operations
from googlecloudsdk.api_lib.functions import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import archive
from googlecloudsdk.core.util import files as file_utils


class Deploy(base.Command):
  """Creates a new function or updates an existing one."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'name', help='Intended name of the new function.',
        type=util.ValidateFunctionNameOrRaise)
    parser.add_argument(
        '--source',
        help=('Path to directory with source code, either local or in Cloud '
              'Source Repositories. If the code is being deployed from Cloud '
              'Source Repositories, this parameter is required and also you '
              'have to specify the parameter --source-url. If the code is in '
              'a local directory, this parameter is optional and defaults to '
              'the current directory. In this case you have to specify the '
              '--bucket parameter.'))
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        '--bucket',
        help=('Name of Google Cloud Storage bucket in which source code will '
              'be stored. Required if a function is deployed from a local '
              'directory.'),
        type=util.ValidateAndStandarizeBucketUriOrRaise)
    source_group.add_argument(
        '--source-url',
        help=('The Url of a remote repository that holds the function being '
              'deployed. It is of the form: '
              'https://source.developers.google.com/p/{project_id}/'
              'r/{repo_name}/, where you should substitute your data for '
              'values inside the curly brackets. You can omit "r/{repo_name}/" '
              'in which case the "default" repository is taken. '
              'One of the parameters --source-revision, --source-branch, '
              'or --source-tag can be given to specify the version in the '
              'repository. If none of them are provided, the last revision '
              'from the master branch is used. If this parameter is given, '
              'the parameter --source is required and describes the path '
              'inside the repository.'))
    source_version_group = parser.add_mutually_exclusive_group()
    source_version_group.add_argument(
        '--source-revision',
        help=('The revision ID (for instance, git tag) that will be used to '
              'get the source code of the function. Can be specified only '
              'together with --source-url parameter.'))
    source_version_group.add_argument(
        '--source-branch',
        help=('The branch that will be used to get the source code of the '
              'function.  The most recent revision on this branch will be '
              'used. Can be specified only together with --source-url '
              'parameter.'))
    source_version_group.add_argument(
        '--source-tag',
        help=('The revision tag for the source that will be used as the source '
              'code of the function. Can be specified only together with '
              '--source-url parameter.'))
    parser.add_argument(
        '--entry-point',
        help=('The name of the function (as defined in source code) that will '
              'be executed.'),
        type=util.ValidateEntryPointNameOrRaise)
    parser.add_argument(
        '--timeout',
        help=('The function execution timeout, e.g. 30s for 30 seconds. '
              'Defaults to 60 seconds.'),
        type=arg_parsers.Duration(lower_bound='1s'))
    trigger_group = parser.add_mutually_exclusive_group(required=True)
    trigger_group.add_argument(
        '--trigger-topic',
        help=('Name of Pub/Sub topic. Every message published in this topic '
              'will trigger function execution with message contents passed as '
              'input data.'),
        type=util.ValidatePubsubTopicNameOrRaise)
    trigger_group.add_argument(
        '--trigger-gs-uri',
        help=('Google Cloud Storage bucket name. Every change in files in this '
              'bucket will trigger function execution.'),
        type=util.ValidateAndStandarizeBucketUriOrRaise)
    trigger_http = trigger_group.add_argument(
        '--trigger-http', action='store_true',
        help='Associates an HTTP endpoint with this function.')
    trigger_http.detailed_help = (
        'Every HTTP POST request to the function\'s endpoint '
        '(web_trigger.url parameter of the deploy output) will trigger '
        'function execution. Result of the function execution will be returned '
        'in response body.')

  @util.CatchHTTPErrorRaiseHTTPException
  def _GetExistingFunction(self, name):
    client = self.context['functions_client']
    messages = self.context['functions_messages']
    try:
      # TODO(user): Use resources.py here after b/21908671 is fixed.
      # We got response for a get request so a function exists.
      return client.projects_regions_functions.Get(
          messages.CloudfunctionsProjectsRegionsFunctionsGetRequest(name=name))
    except apitools_exceptions.HttpError as error:
      if error.status_code == httplib.NOT_FOUND:
        # The function has not been found.
        return None
      raise

  def _GenerateRemoteZipFileName(self, args):
    sufix = ''.join(random.choice(string.ascii_lowercase) for _ in range(12))
    return '{0}-{1}-{2}.zip'.format(args.region, args.name, sufix)

  def _UploadFile(self, source, target):
    return storage.Upload(source, target)

  def _CreateZipFile(self, tmp_dir, args):
    zip_file_name = os.path.join(tmp_dir, 'fun.zip')
    try:
      archive.MakeZipFromDir(zip_file_name, args.source)
    except ValueError as e:
      raise exceptions.FunctionsError(
          'Error creating a ZIP archive with the source code '
          'for directory {0}: {1}'.format(args.source, str(e)))
    return zip_file_name

  def _PrepareFunctionWithoutSources(self, name, args):
    """Creates a function object without filling in the sources properties.

    Args:
      name: funciton name
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified function with its description and configured filter.
    """
    messages = self.context['functions_messages']
    trigger = messages.FunctionTrigger()
    if args.trigger_topic:
      project = properties.VALUES.core.project.Get(required=True)
      trigger.pubsubTopic = 'projects/{0}/topics/{1}'.format(
          project, args.trigger_topic)
    if args.trigger_gs_uri:
      trigger.gsUri = args.trigger_gs_uri
    if args.trigger_http:
      web_trigger = messages.WebTrigger()
      web_trigger.protocol = messages.WebTrigger.ProtocolValueValuesEnum.HTTP
      trigger.webTrigger = web_trigger
    function = messages.HostedFunction()
    function.name = name
    if args.entry_point:
      function.entryPoint = args.entry_point
    if args.timeout:
      function.timeout = str(args.timeout) + 's'
    function.triggers = [trigger]
    return function

  def _DeployFunction(self, name, location, args, deploy_method):
    function = self._PrepareFunctionWithoutSources(name, args)
    if args.source_url:
      messages = self.context['functions_messages']
      if len(filter(None, [args.source_tag, args.source_branch,
                           args.source_revision])) > 1:  # double check
        raise exceptions.FunctionsError('Invalid source parameters.')
      function.sourceRepository = messages.SourceRepository(
          tag=args.source_tag, branch=args.source_branch,
          revision=args.source_revision, repositoryUrl=args.source_url,
          sourcePath=args.source)
    else:
      function.gcsUrl = self._PrepareSourcesOnGcs(args)
    return deploy_method(location, function)

  def _PrepareSourcesOnGcs(self, args):
    remote_zip_file = self._GenerateRemoteZipFileName(args)
    if args.bucket is None:  # double check
      raise exceptions.FunctionsError('Missing bucket parameter'
                                      ' for function sources.')
    gcs_url = storage.BuildRemoteDestination(args.bucket, remote_zip_file)
    with file_utils.TemporaryDirectory() as tmp_dir:
      zip_file = self._CreateZipFile(tmp_dir, args)
      if self._UploadFile(zip_file, gcs_url) != 0:
        raise exceptions.FunctionsError(
            'Failed to upload the function source code to the bucket {0}'
            .format(args.bucket))
    return gcs_url

  @util.CatchHTTPErrorRaiseHTTPException
  def _CreateFunction(self, location, function):
    client = self.context['functions_client']
    messages = self.context['functions_messages']
    # TODO(user): Use resources.py here after b/21908671 is fixed.
    op = client.projects_regions_functions.Create(
        messages.CloudfunctionsProjectsRegionsFunctionsCreateRequest(
            location=location, hostedFunction=function))
    operations.Wait(op, messages, client)
    return self._GetExistingFunction(function.name)

  @util.CatchHTTPErrorRaiseHTTPException
  def _UpdateFunction(self, unused_location, function):
    client = self.context['functions_client']
    messages = self.context['functions_messages']
    # TODO(user): Use resources.py here after b/21908671 is fixed.
    op = client.projects_regions_functions.Update(function)
    operations.Wait(op, messages, client)
    return self._GetExistingFunction(function.name)

  def _CheckArgs(self, args):
    # This function should raise ArgumentParsingError, but:
    # 1. ArgumentParsingError requires the  argument returned from add_argument)
    #    and Args() method is static. So there is no elegant way to save it
    #    to be reused here.
    # 2. _CheckArgs() is invoked from Run() and ArgumentParsingError thrown
    #    from Run are not caught.
    if args.source_url is None:
      if args.source_revision is not None:
        raise exceptions.FunctionsError(
            'argument --source-revision: can be given only if argument '
            '--source-url is provided')
      if args.source_branch is not None:
        raise exceptions.FunctionsError(
            'argument --source-branch: can be given only if argument '
            '--source-url is provided')
      if args.source_tag is not None:
        raise exceptions.FunctionsError(
            'argument --source-tag: can be given only if argument '
            '--source-url is provided')
      if args.source is None:
        args.source = '.'
      if args.bucket is None:
        raise exceptions.FunctionsError(
            'argument --bucket: required when the function is deployed from'
            ' a local directory (when argument --source-url is not provided)')
      util.ValidateDirectoryExistsOrRaiseFunctionError(args.source)
    else:
      if args.source is None:
        raise exceptions.FunctionsError(
            'argument --source: required when argument --source-url is '
            'provided')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified function with its description and configured filter.

    Raises:
      FunctionsError if command line parameters are not valid.
    """
    # TODO(b/24723761): This should be invoked as a hook method after arguments
    # are parsed, but unfortunately gcloud framework doesn't support such a
    # hook.
    self._CheckArgs(args)

    project = properties.VALUES.core.project.Get(required=True)
    location = 'projects/{0}/regions/{1}'.format(project, args.region)
    name = 'projects/{0}/regions/{1}/functions/{2}'.format(
        project, args.region, args.name)

    function = self._GetExistingFunction(name)
    if function is None:
      return self._DeployFunction(name, location, args, self._CreateFunction)
    else:
      return self._DeployFunction(name, location, args, self._UpdateFunction)

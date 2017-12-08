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

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.functions import exceptions
from googlecloudsdk.api_lib.functions import operations
from googlecloudsdk.api_lib.functions import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.deploy import util as deploy_util
from googlecloudsdk.command_lib.util import labels_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

_DEPLOY_WAIT_NOTICE = 'Deploying function (may take a while - up to 2 minutes)'
_NO_LABELS_STARTING_WITH_DEPLOY_MESSAGE = (
    'Label keys starting with `deployment` are reserved for use by deployment '
    'tools and cannot be specified manually.')


def _FunctionArgs(parser):
  """Add arguments specyfying functions behavior to the parser."""
  parser.add_argument(
      'name', help='Intended name of the new function.',
      type=util.ValidateFunctionNameOrRaise)
  parser.add_argument(
      '--memory',
      type=arg_parsers.BinarySize(
          suggested_binary_size_scales=['KB', 'MB', 'MiB', 'GB', 'GiB'],
          default_unit='MB'),
      help="""\
      The amount of memory allocated to your function.

      Allowed values are: 128MB, 256MB, 512MB, 1024MB, and 2048MB. By default,
      256 MB is allocated to each function. When deploying an update to an
      existing function it will keep its old memory limit unless you specify
      this flag.""")
  parser.add_argument(
      '--timeout',
      help="""\
      The function execution timeout, e.g. 30s for 30 seconds. Defaults to
      original value for existing function or 60 seconds for new functions.
      Cannot be more than 540s.""",
      type=arg_parsers.Duration(lower_bound='1s', upper_bound='540s'))
  parser.add_argument(
      '--retry',
      help=('If specified, then the function will be retried in case of a '
            'failure.'),
      action='store_true',
  )
  labels_util.AddUpdateLabelsFlags(
      parser,
      extra_update_message=' ' + _NO_LABELS_STARTING_WITH_DEPLOY_MESSAGE,
      extra_remove_message=' ' + _NO_LABELS_STARTING_WITH_DEPLOY_MESSAGE)


def _SourceCodeArgs(parser):
  """Add arguments specyfying functions source code to the parser."""
  parser.add_argument(
      '--source',
      help="""\
      Location of source code to deploy.

      Location of the source can be one of the following:

      * Source code in Google Cloud Storage,
      * Reference to source repository or,
      * Local filesystem path.

      Value of the flag will be interpreted as Google Cloud Storage location if
      it starts with `gs://`.

      The value will be interpreted as reference to source repository if it
      starts with `https://`..

      Otherwise, it will be interpreted as the local filesystem path. When
      deploying source from the local filesystem, this command skips files
      specified in the `.gcloudignore` file (see `gcloud topic gcloudignore` for
      more information). If the `.gcloudignore` file doesn't exist, the command
      will try to create it.

      If you provide reference to source repository it should be in one of the
      following formats:

      * https://source.developers.google.com/projects/([^/]+)/repos/([^/]+)/revisions/([^/]+)/paths/(.+)
        * Unlike other patterns this can include slashes in last group.
      * https://source.developers.google.com/projects/([^/]+)/repos/([^/]+)/moveable-aliases/([^/]+)
      * https://source.developers.google.com/projects/([^/]+)/repos/([^/]+)/fixed-aliases/([^/]+)
      * https://source.developers.google.com/projects/([^/]+)/repos/([^/]+)

      If source location is not explicitly set new functions deploy current
      directory. Existing functions keep their old source.
      """)

  parser.add_argument(
      '--stage-bucket',
      help=('Name of Google Cloud Storage bucket in which source code will '
            'be stored. Required if a function is deployed from a local '
            'directory.'),
      type=util.ValidateAndStandarizeBucketUriOrRaise)
  parser.add_argument(
      '--entry-point',
      type=util.ValidateEntryPointNameOrRaise,
      help="""\
      By default when a Google Cloud Function is triggered, it executes a
      JavaScript function with the same name. Or, if it cannot find a
      function with the same name, it executes a function named `function`.
      You can use this flag to override the default behavior, by specifying
      the name of a JavaScript function that will be executed when the
      Google Cloud Function is triggered."""
  )


def _TriggerArgs(parser):
  """Add arguments specyfying functions trigger to the parser."""
  # You can also use --trigger-provider but it is hidden argument so not
  # mentioning it for now.
  one_trigger_mandatory_for_new_deployment = (
      ' If you don\'t specify a trigger when deploying an update to an '
      'existing function it will keep its current trigger. You must specify '
      '`--trigger-topic`, `--trigger-bucket`, or `--trigger-http` when '
      'deploying a new function.'
  )
  trigger_group = parser.add_mutually_exclusive_group()
  trigger_group.add_argument(
      '--trigger-topic',
      help=('Name of Pub/Sub topic. Every message published in this topic '
            'will trigger function execution with message contents passed as '
            'input data.' + one_trigger_mandatory_for_new_deployment),
      type=util.ValidatePubsubTopicNameOrRaise)
  trigger_group.add_argument(
      '--trigger-bucket',
      help=('Google Cloud Storage bucket name. Every change in files in this '
            'bucket will trigger function execution.' +
            one_trigger_mandatory_for_new_deployment),
      type=util.ValidateAndStandarizeBucketUriOrRaise)
  trigger_group.add_argument(
      '--trigger-http', action='store_true',
      help="""\
      Function will be assigned an endpoint, which you can view by using
      the `describe` command. Any HTTP request (of a supported type) to the
      endpoint will trigger function execution. Supported HTTP request
      types are: POST, PUT, GET, DELETE, and OPTIONS."""
      + one_trigger_mandatory_for_new_deployment)
  trigger_group.add_argument(
      '--trigger-provider',
      metavar='PROVIDER',
      choices=sorted(util.input_trigger_provider_registry.ProvidersLabels()),
      help=('Trigger this function in response to an event in another '
            'service. For a list of acceptable values, call `gcloud '
            'functions event-types list`.' +
            one_trigger_mandatory_for_new_deployment),
      hidden=True,
      )
  trigger_provider_spec_group = parser.add_argument_group()
  # The validation performed by argparse is incomplete, as the set of valid
  # provider/event combinations is limited. This should be more thoroughly
  # validated at runtime.
  trigger_provider_spec_group.add_argument(
      '--trigger-event',
      metavar='EVENT_TYPE',
      choices=['topic.publish', 'object.change', 'user.create', 'user.delete',
               'data.write'],
      help=('Specifies which action should trigger the function. If omitted, '
            'a default EVENT_TYPE for --trigger-provider will be used. For a '
            'list of acceptable values, call functions event_types list.'),
      hidden=True,
  )
  # check later as type of applicable input depends on options above
  trigger_provider_spec_group.add_argument(
      '--trigger-resource',
      metavar='RESOURCE',
      help=('Specifies which resource from --trigger-provider is being '
            'observed. E.g. if --trigger-provider is cloud.storage, '
            '--trigger-resource must be a bucket name. For a list of '
            'expected resources, call functions event_types list.'),
      hidden=True,
  )


class Deploy(base.Command):
  """Creates a new function or updates an existing one."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    _FunctionArgs(parser)
    _SourceCodeArgs(parser)
    _TriggerArgs(parser)
    flags.AddRegionFlag(parser)

  @util.CatchHTTPErrorRaiseHTTPException
  def _GetExistingFunction(self, name):
    client = util.GetApiClientInstance()
    messages = client.MESSAGES_MODULE
    try:
      # We got response for a get request so a function exists.
      return client.projects_locations_functions.Get(
          messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
              name=name))
    except apitools_exceptions.HttpError as error:
      if error.status_code == httplib.NOT_FOUND:
        # The function has not been found.
        return None
      raise

  def _EventTrigger(self, trigger_provider, trigger_event,
                    trigger_resource):
    messages = util.GetApiMessagesModule()
    event_trigger = messages.EventTrigger()
    event_type_ref = resources.REGISTRY.Parse(
        None,
        params={
            'triggerProvider': trigger_provider,
            'triggerEvent': trigger_event
        },
        collection='cloudfunctions.providers.event_types'
    )
    event_trigger.eventType = event_type_ref.RelativeName()
    event_trigger.resource = (
        deploy_util.ConvertTriggerArgsToRelativeName(
            trigger_provider,
            trigger_event,
            trigger_resource))
    return event_trigger

  def _ApplyNonSourceArgsToFunction(
      self, function, update_mask, messages, args, name, trigger_params):
    """Modifies a function object without touching in the sources properties.

    Args:
      function: message, function resource to be modified.
      update_mask: update mask to which modified fields will be added.
      messages: messages module.
      args: parsed commandline arguments.
      name: str, name of the function.
      trigger_params: None or dict from str to str, the dict is assumed to
                      contain exactly the following keys: trigger_provider,
                      trigger_event, trigger_resource.
    """
    function.name = name
    if args.entry_point:
      function.entryPoint = args.entry_point
      update_mask.append('entryPoint')
    if args.timeout:
      function.timeout = '{}s'.format(args.timeout)
      update_mask.append('timeout')
    if args.trigger_http:
      deploy_util.CleanOldTriggerInfo(function, update_mask)
      function.httpsTrigger = messages.HttpsTrigger()
    if trigger_params:
      deploy_util.CleanOldTriggerInfo(function, update_mask)
      function.eventTrigger = self._EventTrigger(**trigger_params)
    if args.IsSpecified('retry'):
      update_mask.append('eventTrigger.failurePolicy')
      if args.retry:
        function.eventTrigger.failurePolicy = messages.FailurePolicy()
        function.eventTrigger.failurePolicy.retry = messages.Retry()
      else:
        function.eventTrigger.failurePolicy = None
    elif function.eventTrigger:
      function.eventTrigger.failurePolicy = None
    if args.memory:
      function.availableMemoryMb = utils.BytesToMb(args.memory)
      update_mask.append('memory')

  def _ApplyArgsToFunction(
      self, function, is_new_function, trigger_params, name, args,
      project):
    """Apply values from args to base_function.

    Args:
        function: function message to modify
        is_new_function: bool, indicates if this is a new function (and source
                         code for it must be deployed) or an existing function
                         (so it may keep its old source code).
        trigger_params: parameters for creating functions trigger.
        name: relative name of the function.
        args: commandline args specyfying how to modify the function.
        project: project of the function.
    Returns:
      Pair of function and update mask.
    """
    update_mask = []

    messages = util.GetApiMessagesModule()
    self._ApplyNonSourceArgsToFunction(
        function, update_mask, messages, args, name, trigger_params)
    if args.source or args.stage_bucket:
      deploy_util.AddSourceToFunction(
          function, update_mask, args.source, args.name, args.stage_bucket,
          messages)
    elif is_new_function:
      raise exceptions.FunctionsError(
          'argument --stage-bucket: required when the function is deployed '
          'from a local directory.')
    # Set information about deployment tool.
    labels_to_update = args.update_labels or {}
    labels_to_update['deployment-tool'] = 'cli-gcloud'
    labels_diff = labels_util.Diff(additions=labels_to_update,
                                   subtractions=args.remove_labels,
                                   clear=args.clear_labels)
    labels_update = labels_diff.Apply(messages.CloudFunction.LabelsValue,
                                      function.labels)
    if labels_update.needs_update:
      function.labels = labels_update.labels
      update_mask.append('labels')
    return function, ','.join(sorted(update_mask))

  def _ValidateAfterCheckingFunctionsExistence(self, function, args):
    if function is None:
      if (not args.IsSpecified('trigger_topic') and
          not args.IsSpecified('trigger_bucket') and
          not args.IsSpecified('trigger_http') and
          not args.IsSpecified('trigger_provider')):
        # --trigger-provider is hidden for now so not mentioning it.
        raise calliope_exceptions.OneOfArgumentsRequiredException(
            ['--trigger-topic', '--trigger-bucket', '--trigger-http'],
            'You must specify a trigger when deploying a new function.'
        )

  @util.CatchHTTPErrorRaiseHTTPException
  def _CreateFunction(self, location, function):
    client = util.GetApiClientInstance()
    messages = client.MESSAGES_MODULE
    op = client.projects_locations_functions.Create(
        messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=location, cloudFunction=function))
    operations.Wait(op, messages, client, _DEPLOY_WAIT_NOTICE)
    return self._GetExistingFunction(function.name)

  @util.CatchHTTPErrorRaiseHTTPException
  def _UpdateFunction(self, function, update_mask):
    client = util.GetApiClientInstance()
    messages = client.MESSAGES_MODULE
    op = client.projects_locations_functions.Patch(
        messages.CloudfunctionsProjectsLocationsFunctionsPatchRequest(
            cloudFunction=function,
            name=function.name,
            updateMask=update_mask,
        )
    )
    operations.Wait(op, messages, client, _DEPLOY_WAIT_NOTICE)
    return self._GetExistingFunction(function.name)

  def _ValidateLabelsFlagKeys(self, flag_name, keys):
    for key in keys:
      if key.startswith('deployment'):
        raise calliope_exceptions.InvalidArgumentException(
            flag_name, _NO_LABELS_STARTING_WITH_DEPLOY_MESSAGE)

  def _ValidateLabelsFlags(self, args):
    if args.remove_labels:
      self._ValidateLabelsFlagKeys('--remove-labels', args.remove_labels)
    if args.update_labels:
      self._ValidateLabelsFlagKeys('--update-labels', args.update_labels.keys())

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
    self._ValidateLabelsFlags(args)
    trigger_params = deploy_util.DeduceAndCheckArgs(args)
    project = properties.VALUES.core.project.Get(required=True)
    location_ref = resources.REGISTRY.Parse(
        properties.VALUES.functions.region.Get(),
        params={'projectsId': project},
        collection='cloudfunctions.projects.locations')
    location = location_ref.RelativeName()
    function_ref = resources.REGISTRY.Parse(
        args.name, params={
            'projectsId': project,
            'locationsId': properties.VALUES.functions.region.Get()},
        collection='cloudfunctions.projects.locations.functions')
    function_url = function_ref.RelativeName()

    function = self._GetExistingFunction(function_url)
    self._ValidateAfterCheckingFunctionsExistence(function, args)
    is_new_function = function is None
    if is_new_function:
      messages = util.GetApiMessagesModule()
      function = messages.CloudFunction()
    function, update_mask = self._ApplyArgsToFunction(
        function, is_new_function, trigger_params, function_url, args,
        project)
    if is_new_function:
      return self._CreateFunction(location, function)
    else:
      return self._UpdateFunction(function, update_mask)

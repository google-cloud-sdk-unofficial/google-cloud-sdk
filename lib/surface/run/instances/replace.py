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
"""Command for creating or replacing instances from YAML."""

import argparse

from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.api_lib.run import instance
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import messages_util as run_messages_util
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaReplace(base.Command):
  """Create or replace an instance from a YAML instance specification."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Creates or replaces an instance from a YAML instance specification.
          """
      ),
      'EXAMPLES': (
          """\
          To replace the specification for an instance defined in myinstance.yaml

              $ {command} myinstance.yaml

         """
      ),
  }

  @staticmethod
  def Args(parser: argparse.ArgumentParser) -> None:
    flags.AddAsyncFlag(parser)
    flags.AddClientNameAndVersionFlags(parser)
    parser.add_argument(
        'FILE',
        action='store',
        type=arg_parsers.YAMLFileContents(),
        help=(
            'The absolute path to the YAML file with a Cloud Run '
            'instance definition for the instance to update or create.'
        ),
    )
    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')

  def Run(self, args: argparse.Namespace) -> instance.Instance:
    """Create or Update instance from YAML."""
    run_messages = apis.GetMessagesModule(
        global_methods.SERVERLESS_API_NAME,
        global_methods.SERVERLESS_API_VERSION,
    )
    instance_dict = dict(args.FILE)
    # Clear the status field since it is ignored by Cloud Run APIs and can cause
    # issues trying to convert to a message.
    if 'status' in instance_dict:
      del instance_dict['status']

    # For cases where YAML contains the project number as metadata.namespace,
    # preemptively convert them to a string to avoid validation failures.
    namespace = instance_dict.get('metadata', {}).get('namespace', None)
    if namespace is not None and not isinstance(namespace, str):
      instance_dict['metadata']['namespace'] = str(namespace)

    try:
      raw_instance = messages_util.DictToMessageWithErrorCheck(
          instance_dict, run_messages.Instance
      )
      new_instance = instance.Instance(raw_instance, run_messages)
    except messages_util.ScalarTypeMismatchError as e:
      exceptions.MaybeRaiseCustomFieldMismatch(
          e,
          help_text=(
              'Please make sure that the YAML file matches the Cloud Run '
              'instance definition spec.'
          ),
      )

    # Namespace must match project (or will default to project if
    # not specified).
    namespace = properties.VALUES.core.project.Get()
    if new_instance.metadata.namespace is not None:
      project = namespace
      project_number = projects_util.GetProjectNumber(namespace)
      namespace = new_instance.metadata.namespace
      if namespace != project and namespace != str(project_number):
        raise exceptions.ConfigurationError(
            'Namespace must be project ID [{}] or quoted number [{}] for '
            .format(project, project_number)
        )
    new_instance.metadata.namespace = namespace

    is_either_specified = args.IsSpecified('client_name') or args.IsSpecified(
        'client_version'
    )
    changes = [
        config_changes.ReplaceInstanceChange(new_instance),
        config_changes.SetLaunchStageAnnotationChange(self.ReleaseTrack()),
        config_changes.SetClientNameAndVersionAnnotationChange(
            args.client_name if is_either_specified else 'gcloud',
            args.client_version
            if is_either_specified
            else config.CLOUD_SDK_VERSION,
        ),
    ]

    instance_ref = resources.REGISTRY.Parse(
        new_instance.metadata.name,
        params={'namespacesId': new_instance.metadata.namespace},
        collection='run.namespaces.instances',
    )
    try:
      region = new_instance.region
    except KeyError:
      region = None
    conn_context = connection_context.GetConnectionContext(
        args,
        flags.Product.RUN,
        self.ReleaseTrack(),
        region_label=region,
    )

    with serverless_operations.Connect(conn_context) as client:
      instance_obj = client.GetInstance(instance_ref)

      is_create = not instance_obj
      operation = 'Creating' if is_create else 'Replacing'
      pretty_print.Info(
          run_messages_util.GetStartDeployMessage(
              conn_context, instance_ref, operation, 'instance'
          )
      )

      header = operation + ' instance...'
      with progress_tracker.StagedProgressTracker(
          header,
          stages.InstanceStages(),
          failure_message='Instance failed to deploy',
          suppress_output=args.async_,
      ) as tracker:

        if instance_obj:
          instance_obj = client.ReplaceInstance(
              instance_ref, changes, tracker, asyn=args.async_
          )
        else:
          parent_ref = instance_ref.Parent()
          instance_obj = client.CreateInstance(
              parent_ref,
              instance_ref.Name(),
              changes,
              tracker,
              asyn=args.async_,
          )

      operation = 'created' if is_create else 'replaced'
      if args.async_:
        pretty_print.Success(
            'Instance [{{bold}}{instance}{{reset}}] is being {operation} '
            'asynchronously.'.format(
                instance=instance_obj.name, operation=operation
            )
        )
      else:
        pretty_print.Success(
            'Instance [{{bold}}{instance}{{reset}}] has been '
            '{operation}.'.format(
                instance=instance_obj.name, operation=operation
            )
        )
      return instance_obj

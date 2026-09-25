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
"""Command to create and provision a Firebase project."""

from __future__ import annotations

from googlecloudsdk.api_lib.firebase import projects as firebase_api
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

_DEFAULT_APP_NAMESPACE = 'com.example.my_app'
_DEFAULT_DISPLAY_NAME = 'My Firebase App'
_DEFAULT_WAIT_TIMEOUT_MS = 60 * 60 * 1000


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create and provision a new Firebase project and associated resources."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          Creates (provisions) a Firebase project and initializes a Firebase
          Web App in region us-west1.

          If a Google Cloud project ID is specified, Firebase is provisioned into
          that existing project. Otherwise, a new project ID is automatically
          generated and provisioned.
          """,
      'EXAMPLES': """\
          To provision a new Firebase project:

              $ {command} --app-namespace=com.example.my_app --display-name="My Firebase App"

          To provision Firebase for an existing Google Cloud project:

              $ {command} my-project-id --display-name="My Firebase App"

          To provision asynchronously:

              $ {command} --display-name="My Firebase App" --async
          """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'project',
        nargs='?',
        help=(
            'ID for the Google Cloud project in which to provision Firebase. '
            'If omitted, a new project ID will be automatically generated and '
            'provisioned.'
        ),
    )
    parser.add_argument(
        '--app-namespace',
        help=(
            'Developer-assigned identifier for the web app to create. '
            'Defaults to a generated namespace based on project ID or '
            'display name.'
        ),
    )
    parser.add_argument(
        '--display-name',
        help=(
            'The display name for the new Project and/or Web App. '
            'Defaults to project ID or "My Firebase App".'
        ),
    )
    parser.add_argument(
        '--async',
        action='store_true',
        dest='async_',
        help=(
            'Return immediately, without waiting for the operation in '
            'progress to complete.'
        ),
    )

  def Run(self, args):
    project_id = args.project if args.IsSpecified('project') else None
    parent = (
        resources.REGISTRY.Parse(
            project_id, collection='firebase.projects', api_version='v1alpha'
        ).RelativeName()
        if project_id
        else None
    )

    app_namespace = args.app_namespace
    if not app_namespace:
      if project_id:
        app_namespace = 'com.example.{}'.format(project_id.replace('-', '_'))
      elif args.display_name:
        sanitized = ''.join(
            c if c.isalnum() else '_' for c in args.display_name.lower()
        )
        app_namespace = 'com.example.{}'.format(sanitized.strip('_'))
      else:
        app_namespace = _DEFAULT_APP_NAMESPACE

    display_name = args.display_name or (
        project_id if project_id else _DEFAULT_DISPLAY_NAME
    )

    operation = firebase_api.ProvisionFirebaseApp(
        app_namespace=app_namespace,
        display_name=display_name,
        parent=parent,
    )

    if args.async_:
      log.status.Print(
          'Provisioning operation started: [{}]'.format(operation.name)
      )
      return operation

    log.status.Print(
        'Waiting for operation [{}] to finish...'.format(operation.name)
    )
    operation_ref = resources.REGISTRY.Parse(
        operation.name, collection='firebase.operations', api_version='v1alpha'
    )
    poller = waiter.CloudOperationPollerNoResources(
        firebase_api.GetClientInstance().operations
    )
    result = waiter.WaitFor(
        poller,
        operation_ref,
        'Provisioning Firebase project',
        max_wait_ms=_DEFAULT_WAIT_TIMEOUT_MS,
    )
    log.CreatedResource(operation.name, kind='firebase project')
    return result

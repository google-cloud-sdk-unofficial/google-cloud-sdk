# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for creating a local development environment."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import os.path

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.local import local
from googlecloudsdk.command_lib.local import yaml_helper
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files

_SKAFFOLD_TEMPLATE = """
apiVersion: skaffold/v1beta12
kind: Config
build:
  artifacts:
  - image: {image_name}
    context: {context_path}
deploy:
  kubectl:
    manifests: []
"""

_DEFAULT_SECRET_PATH = os.path.join(config.Paths().global_config_dir,
                                    'local_developer_credential_secret.yaml')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Setup(base.Command):
  """Command for creating a skaffold local development environment."""

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--dockerfile',
        default='Dockerfile',
        help='The Dockerfile for the service image.')

    parser.add_argument(
        '--service-name', required=False, help='Name of the service.')

    parser.add_argument(
        '--image-name', required=False, help='Name for the built docker image.')

    parser.add_argument(
        '--skaffold-file',
        default='skaffold.yaml',
        required=False,
        help='Location of the generated skaffold.yaml file.')

    parser.add_argument(
        '--kubernetes-file',
        default='pods_and_services.yaml',
        help='File containing yaml specifications for kubernetes resources.')

    parser.add_argument(
        '--build-context-directory',
        help='If set, use this as the context directory when building the '
        'container image. Otherwise, the directory of the Dockerfile will be '
        'used.')

    parser.add_argument(
        '--service-account',
        help='When connecting to Google Cloud Platform services, use a service '
        'account key.')

  def Run(self, args):
    project_name = properties.VALUES.core.project.Get(required=True)

    if not args.IsSpecified('service_name'):
      dir_name = os.path.basename(
          os.path.dirname(os.path.join(files.GetCWD(), args.dockerfile)))
      service_name = console_io.PromptWithDefault(
          message='Service name', default=dir_name)
    else:
      service_name = args.service_name

    if not args.IsSpecified('image_name'):
      default_image_name = 'gcr.io/{project}/{service}'.format(
          project=project_name, service=service_name)
      image_name = console_io.PromptWithDefault(
          message='Docker image tag', default=default_image_name)
    else:
      image_name = args.image_name

    kubernetes_yaml_paths = []
    kubernetes_configs = local.CreatePodAndService(service_name, image_name)
    if args.service_account:
      service_account = local.CreateDevelopmentServiceAccount(
          args.service_account)
      private_key_json = local.CreateServiceAccountKey(service_account)
      secret_yaml = local.LocalDevelopmentSecretSpec(private_key_json)
      kubernetes_configs.append(secret_yaml)
      local.AddServiceAccountSecret(kubernetes_configs)

    with files.FileWriter(args.kubernetes_file) as output:
      yaml.dump_all(kubernetes_configs, output)
    kubernetes_yaml_paths.append(args.kubernetes_file)

    skaffold_yaml_text = _SKAFFOLD_TEMPLATE.format(
        image_name=image_name,
        context_path=args.build_context_directory or
        os.path.dirname(args.dockerfile) or '.')
    skaffold_yaml = yaml.load(skaffold_yaml_text)
    manifests = yaml_helper.GetOrCreate(
        skaffold_yaml, ('deploy', 'kubectl', 'manifests'), constructor=list)
    manifests.extend(kubernetes_yaml_paths)

    with files.FileWriter(args.skaffold_file) as output:
      yaml.dump(skaffold_yaml, output)

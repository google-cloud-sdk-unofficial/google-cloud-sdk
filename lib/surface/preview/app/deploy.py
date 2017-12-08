
# Copyright 2013 Google Inc. All Rights Reserved.
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

"""The gcloud app deploy command."""

import argparse
import json
import os

from gae_ext_runtime import ext_runtime

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import appengine_client
from googlecloudsdk.api_lib.app import cloud_endpoints
from googlecloudsdk.api_lib.app import cloud_storage
from googlecloudsdk.api_lib.app import deploy_app_command_util
from googlecloudsdk.api_lib.app import deploy_command_util
from googlecloudsdk.api_lib.app import metric_names
from googlecloudsdk.api_lib.app import util
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.app.runtimes import fingerprinter
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import exceptions
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.command_lib.app import output_helpers
from googlecloudsdk.core import apis
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.docker import constants
from googlecloudsdk.third_party.appengine.tools import context_util


class _AppEngineClients(object):
  """Value class for App Engine client objects."""

  def __init__(self, gae_client, api_client):
    self.gae = gae_client
    self.api = api_client


DEFAULT_DEPLOYABLE = 'app.yaml'


class Deploy(base.SilentCommand):
  """Deploy the local code and/or configuration of your app to App Engine.

  This command is used to deploy both code and configuration to the App Engine
  server.  As an input it takes one or more ``DEPLOYABLES'' that should be
  uploaded.  A ``DEPLOYABLE'' can be a service's .yaml file or a configuration's
  .yaml file.
  """

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To deploy a single service, run:

            $ {command} ~/my_app/app.yaml

          To deploy multiple services, run:

            $ {command} ~/my_app/app.yaml ~/my_app/another_service.yaml
          """,
  }

  @staticmethod
  def Args(parser):
    """Get arguments for this command.

    Args:
      parser: argparse.ArgumentParser, the parser for this command.
    """
    flags.SERVER_FLAG.AddToParser(parser)
    flags.IGNORE_CERTS_FLAG.AddToParser(parser)
    parser.add_argument(
        '--version',
        help='The version of the app that will be created or replaced by this '
        'deployment.  If you do not specify a version, one will be generated '
        'for you.')
    parser.add_argument(
        '--force',
        action='store_true',
        help=('Force deploying, overriding any previous in-progress '
              'deployments to this version.'))
    parser.add_argument(
        '--bucket',
        type=cloud_storage.GcsBucketArgument,
        help=("The Google Cloud Storage bucket used to stage files associated "
              "with the deployment. If this argument is not specified, the "
              "application's default code bucket is used."))
    parser.add_argument(
        '--docker-build',
        choices=['remote', 'local'],
        action=actions.StoreProperty(properties.VALUES.app.docker_build),
        help=argparse.SUPPRESS)
    deployables = parser.add_argument(
        'deployables', nargs='*',
        help='The yaml files for the services or configurations you want to '
        'deploy.')
    deployables.detailed_help = (
        'The yaml files for the services or configurations you want to deploy. '
        'If not given, defaults to `app.yaml` in the current directory. '
        'If that is not found, attempts to automatically generate necessary '
        'configuration files (such as app.yaml) in the current directory.')
    parser.add_argument(
        '--repo-info-file', metavar='filename',
        help=argparse.SUPPRESS)
    parser.add_argument(
        '--stop-previous-version',
        action=actions.StoreBooleanProperty(
            properties.VALUES.app.stop_previous_version),
        help='Stop the previously running version when deploying a new version '
             'that receives all traffic (off by default).')
    parser.add_argument(
        '--image-url',
        help='Deploy with a specific Docker image.  Docker url must be '
        'from one of the valid gcr hostnames.')
    promote = parser.add_argument(
        '--promote',
        action=actions.StoreBooleanProperty(
            properties.VALUES.app.promote_by_default),
        help='Promote the deployed version to receive all traffic.')
    promote.detailed_help = (
        'Promote the deployed version to receive all traffic.\n\n'
        'True by default. To change the default behavior for your current '
        'environment, run:\n\n'
        '    $ gcloud config set app/promote_by_default false')

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    version = args.version or util.GenerateVersionId()
    promote = properties.VALUES.app.promote_by_default.GetBool()
    stop_previous_version = (
        properties.VALUES.app.stop_previous_version.GetBool())
    use_cloud_build = properties.VALUES.app.use_cloud_build.GetBool()
    if not use_cloud_build:
      log.warning(
          'Docker builds use Container Builder by default. The ability to '
          'perform builds on Compute Engine directly (via the '
          'app/use_cloud_build property) will be removed in a future release.')
    remote_build = True
    docker_build_property = properties.VALUES.app.docker_build.Get()
    if docker_build_property:
      log.warning("""\
The --docker-build flag and the app/docker_build property are
deprecated and will be removed in a future release. To run a Docker build on
your own host, you can run:
    docker build -t gcr.io/<project>/<service.version> .
    gcloud docker push gcr.io/<project>/<service.version>
    gcloud preview app deploy --image-url=gcr.io/<project>/<service.version>
    """)
      remote_build = docker_build_property == 'remote'

    config_cleanup = None
    if args.deployables:
      app_config = yaml_parsing.AppConfigSet(args.deployables)
    else:
      if not os.path.exists(DEFAULT_DEPLOYABLE):
        console_io.PromptContinue(
            'Deployment to Google App Engine requires an app.yaml file. '
            'This command will run `gcloud preview app gen-config` to generate '
            'an app.yaml file for you in the current directory (if the current '
            'directory does not contain an App Engine service, please answer '
            '"no").', cancel_on_no=True)
        # This generates the app.yaml AND the Dockerfile (and related files).
        params = ext_runtime.Params(deploy=True)
        configurator = fingerprinter.IdentifyDirectory(os.getcwd(),
                                                       params=params)
        if configurator is None:
          raise exceptions.NoAppIdentifiedError(
              'Could not identify an app in the current directory.\n\n'
              'Please prepare an app.yaml file for your application manually '
              'and deploy again.')
        config_cleanup = configurator.GenerateConfigs()
        log.status.Print('\nCreated [{0}] in the current directory.\n'.format(
            DEFAULT_DEPLOYABLE))
      app_config = yaml_parsing.AppConfigSet([DEFAULT_DEPLOYABLE])

    # If the app has enabled Endpoints API Management features, pass
    # control to the cloud_endpoints handler.

    cloud_endpoints.ProcessEndpointsServices(
        [item[1] for item in app_config.Services().items()], project)

    clients = _AppEngineClients(
        appengine_client.AppengineClient(args.server,
                                         args.ignore_bad_certs),
        appengine_api_client.GetApiClient())
    # pylint: disable=protected-access
    log.debug('API endpoint: [{endpoint}], API version: [{version}]'.format(
        endpoint=clients.api.client.url,
        version=clients.api.client._VERSION))
    cloudbuild_client = apis.GetClientInstance('cloudbuild', 'v1')
    storage_client = apis.GetClientInstance('storage', 'v1')

    deployed_urls = output_helpers.DisplayProposedDeployment(
        project, app_config, version, promote)
    console_io.PromptContinue(default=True, throw_if_unattended=False,
                              cancel_on_no=True)

    log.status.Print('Beginning deployment...')

    source_contexts = []
    if args.repo_info_file:
      if args.image_url:
        raise exceptions.NoRepoInfoWithImageUrlError()

      try:
        with open(args.repo_info_file, 'r') as f:
          source_contexts = json.load(f)
      except (ValueError, IOError) as ex:
        raise exceptions.RepoInfoLoadError(args.repo_info_file, ex)
      if isinstance(source_contexts, dict):
        # This is an old-style source-context.json file. Convert to a new-
        # style array of extended contexts.
        source_contexts = [context_util.ExtendContextDict(source_contexts)]

    services = app_config.Services()

    code_bucket_ref = None
    if services and (use_cloud_build or app_config.NonHermeticServices()):
      # If using Argo CloudBuild, we'll need to upload source to a GCS bucket.
      code_bucket_ref = flags.GetCodeBucket(clients.api, project, args.bucket)
      metrics.CustomTimedEvent(metric_names.GET_CODE_BUCKET)
      log.debug('Using bucket [{b}].'.format(b=code_bucket_ref))

    if any([m.RequiresImage() for m in services.values()]):
      deploy_command_util.DoPrepareManagedVms(clients.gae)
    if args.image_url:
      if len(services) != 1:
        raise exceptions.MultiDeployError()
      for registry in constants.ALL_SUPPORTED_REGISTRIES:
        if args.image_url.startswith(registry):
          break
      else:
        raise exceptions.UnsupportedRegistryError(args.image_url)
      service = services.keys()[0]
      images = {service: args.image_url}
    else:
      images = deploy_command_util.BuildAndPushDockerImages(services,
                                                            version,
                                                            cloudbuild_client,
                                                            storage_client,
                                                            code_bucket_ref,
                                                            self.cli,
                                                            remote_build,
                                                            source_contexts,
                                                            config_cleanup)

    deployment_manifests = {}
    if app_config.NonHermeticServices():
      if properties.VALUES.app.use_gsutil.GetBool():
        copy_func = deploy_app_command_util.CopyFilesToCodeBucket
        metric_name = metric_names.COPY_APP_FILES
      else:
        copy_func = deploy_app_command_util.CopyFilesToCodeBucketNoGsUtil
        metric_name = metric_names.COPY_APP_FILES_NO_GSUTIL

      deployment_manifests = copy_func(
          app_config.NonHermeticServices().items(),
          code_bucket_ref,
          source_contexts,
          storage_client)
      metrics.CustomTimedEvent(metric_name)

    new_versions = []
    if services:
      # We don't necessarily have permission to list services if we only want to
      # update config files (below).
      all_services = dict([(s.id, s) for s in clients.api.ListServices()])

      # Now do deployment.
      for (service, info) in services.iteritems():
        message = 'Updating service [{service}]'.format(service=service)
        new_version = version_util.Version(project, service, version)
        with console_io.ProgressTracker(message):
          if args.force:
            log.warning('The --force argument is deprecated and no longer '
                        'required. It will be removed in a future release.')

          clients.api.DeployService(service, version, info,
                                    deployment_manifests.get(service),
                                    images.get(service))
          metrics.CustomTimedEvent(metric_names.DEPLOY_API)

          if promote:
            version_util.PromoteVersion(all_services, new_version, clients,
                                        stop_previous_version)
          elif stop_previous_version:
            log.info('Not stopping previous version because new version was '
                     'not promoted.')
        # We don't have a deployed URL for custom-domain apps, since these are
        # not possible to predict with 100% accuracy (b/24603280).
        deployed_url = deployed_urls.get(service)
        if deployed_url:
          log.status.Print('Deployed service [{0}] to [{1}]'.format(
              service, deployed_url))
        else:
          log.status.Print('Deployed service [{0}]'.format(service))
        new_versions.append(new_version)

    # Config files.
    for (c, info) in app_config.Configs().iteritems():
      message = 'Updating config [{config}]'.format(config=c)
      with console_io.ProgressTracker(message):
        clients.gae.UpdateConfig(c, info.parsed)
    return {
        'versions': new_versions,
        'configs': app_config.Configs().keys()
    }




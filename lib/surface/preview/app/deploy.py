
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
from googlecloudsdk.api_lib.app import flags
from googlecloudsdk.api_lib.app import metric_names
from googlecloudsdk.api_lib.app import service_util
from googlecloudsdk.api_lib.app import util
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.app.runtimes import fingerprinter
from googlecloudsdk.api_lib.source import context_util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.docker import constants


DEPLOY_MESSAGE_TEMPLATE = """\
{project}/{module} (from [{file}])
     Deployed URL: [{url}]
"""
# We can't reliably calculate the URL for domain scoped projects, so don't show
# it.
DEPLOY_MESSAGE_DOMAIN_SCOPED_TEMPLATE = """\
{project}/{module} (from [{file}])
"""
PROMOTE_MESSAGE = """\
     (add --promote if you also want to make this module available from
     [{default_url}])
"""


class NoAppIdentifiedError(exceptions.Error):
  pass


class _AppEngineClients(object):
  """Value class for App Engine client objects."""

  def __init__(self, gae_client, api_client):
    self.gae = gae_client
    self.api = api_client


class DeployError(exceptions.Error):
  """Base class for app deploy failures."""


class RepoInfoLoadError(DeployError):
  """Indicates a failure to load a source context file."""

  def __init__(self, filename, inner_exception):
    self.filename = filename
    self.inner_exception = inner_exception

  def __str__(self):
    return 'Could not read repo info file {0}: {1}'.format(
        self.filename, self.inner_exception)


class MultiDeployError(DeployError):
  """Indicates a failed attempt to deploy multiple image urls."""

  def __str__(self):
    return ('No more than one module may be deployed when using the '
            'image-url flag')


class NoRepoInfoWithImageUrlError(DeployError):
  """The user tried to specify a repo info file with a docker image."""

  def __str__(self):
    return 'The --repo-info-file option is not compatible with --image_url.'


class UnsupportedRegistryError(DeployError):
  """Indicates an attempt to use an unsuported registry."""

  def __init__(self, image_url):
    self.image_url = image_url

  def __str__(self):
    return ('{0} is not in a supported registry.  Supported registries are '
            '{1}'.format(self.image_url, constants.ALL_SUPPORTED_REGISTRIES))


class DefaultBucketAccessError(DeployError):
  """Indicates a failed attempt to access a project's default bucket."""

  def __init__(self, project):
    self.project = project

  def __str__(self):
    return (
        'Could not retrieve the default Google Cloud Storage bucket for [{a}]. '
        'Please try again or use the [bucket] argument.').format(a=self.project)


DEFAULT_DEPLOYABLE = 'app.yaml'


def _DisplayProposedDeployment(project, app_config, version, promote):
  """Prints the details of the proposed deployment.

  Args:
    project: the name of the current project
    app_config: the application configuration to be deployed
    version: the version identifier of the application to be deployed
    promote: whether the newly deployed version will receive all traffic
      (this affects deployed URLs)

  Returns:
    dict (str->str), a mapping of module names to deployed module URLs

  This includes information on to-be-deployed modules (including module name,
  version number, and deployed URLs) as well as configurations.
  """
  # TODO(user): Have modules and configs be able to print themselves.  We
  # do this right now because we actually need to pass a yaml file to appcfg.
  # Until we can make a call with the correct values for project and version
  # it is weird to override those values in the yaml parsing code (because
  # it does not carry through to the actual file contents).
  deployed_urls = {}
  if app_config.Modules():
    printer = console_io.ListPrinter(
        'You are about to deploy the following modules:')
    deploy_messages = []
    for module, info in app_config.Modules().iteritems():
      use_ssl = deploy_command_util.UseSsl(info.parsed.handlers)
      version = None if promote else version
      if ':' in project:
        deploy_message = DEPLOY_MESSAGE_DOMAIN_SCOPED_TEMPLATE.format(
            project=project, module=module, file=info.file)
      else:
        url = deploy_command_util.GetAppHostname(
            project, module=info.module, version=version, use_ssl=use_ssl)
        deployed_urls[module] = url
        deploy_message = DEPLOY_MESSAGE_TEMPLATE.format(
            project=project, module=module, file=info.file, url=url)
      if not promote:
        default_url = deploy_command_util.GetAppHostname(
            project, module=info.module, use_ssl=use_ssl)
        deploy_message += PROMOTE_MESSAGE.format(default_url=default_url)
      deploy_messages.append(deploy_message)
    printer.Print(deploy_messages, output_stream=log.status)

  if app_config.Configs():
    printer = console_io.ListPrinter(
        'You are about to deploy the following configurations:')
    printer.Print(
        ['{0}/{1}  (from [{2}])'.format(project, c.config, c.file)
         for c in app_config.Configs().values()], output_stream=log.status)

  return deployed_urls


def _Promote(all_services, new_version, clients, stop_previous_version):
  """Promote the new version to receive all traffic.

  Additionally, stops the previous version if applicable.

  Args:
    all_services: list of Service objects representing all services in the app
    new_version: Version object representing the version to promote
    clients: _AppEngineClients object containing clients for Google App Engine
        APIs.
    stop_previous_version: bool, whether to stop the previous version which was
        receiving all traffic, if any.
  """
  old_default_version = None
  if stop_previous_version:
    # Grab the list of versions before we promote, since we need to
    # figure out what the previous default version was
    old_default_version = _GetPreviousVersion(all_services, new_version,
                                              clients.api)

  clients.api.SetDefaultVersion(new_version.service, new_version.id)
  metrics.CustomTimedEvent(metric_names.SET_DEFAULT_VERSION_API)

  if old_default_version:
    _StopPreviousVersionIfApplies(old_default_version, clients)


def _GetPreviousVersion(all_services, new_version, api_client):
  """Get the previous default version of which new_version is replacing.

  If there is no such version, return None.

  Args:
    all_services: list of Service objects representing all services for the app
    new_version: a Version object representing the new version deployed.
    api_client: client for the App Engine Admin API

  Returns:
    Version object representing the previous version or None

  """
  try:
    service_object = service_util.GetMatchingServices(all_services,
                                                      [new_version.service])[0]
  except service_util.ServicesNotFoundError:
    return None
  for old_version in api_client.ListVersions([service_object]):
    # Make sure not to stop the just-deployed version!
    # This can happen with a new service, or with a deployment over
    # an existing version.
    if (old_version.is_receiving_all_traffic and
        old_version.id != new_version.id):
      return old_version


def _StopPreviousVersionIfApplies(old_default_version, clients):
  """Stop the previous default version if applicable.

  Cases where a version will not be stopped:

  * If the previous default version is not serving, there is no need to stop it.
  * If the previous default version is an automatically scaled standard
    environment app, it cannot be stopped.

  Args:
    old_default_version: Version object representign the default version
    clients: _AppEngineClients object containing clients for Google App Engine
        APIs.
  """
  version_object = old_default_version.version
  status_enum = clients.api.messages.Version.ServingStatusValueValuesEnum
  if version_object.servingStatus != status_enum.SERVING:
    log.info(
        'Previous default version [{0}] not serving, so not stopping '
        'it.'.format(old_default_version))
    return
  if (not version_object.vm and not version_object.basicScaling and
      not version_object.manualScaling):
    log.info(
        'Previous default version [{0}] is an automatically scaled '
        'standard environment app, so not stopping it.'.format(
            old_default_version))
    return

  try:
    clients.gae.StopModule(module=old_default_version.service,
                           version=old_default_version.id)
  except util.RPCError as err:
    log.warn('Error stopping version [{0}]: {1}'.format(old_default_version,
                                                        str(err)))
    log.warn('Version [{0}] is still running and you must stop or delete it '
             'yourself in order to turn it off. (If you do not, you may be '
             'charged.)'.format(old_default_version))


class Deploy(base.Command):
  """Deploy the local code and/or configuration of your app to App Engine.

  This command is used to deploy both code and configuration to the App Engine
  server.  As an input it takes one or more ``DEPLOYABLES'' that should be
  uploaded.  A ``DEPLOYABLE'' can be a module's .yaml file or a configuration's
  .yaml file.
  """

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          To use a temporary VM (with the default `--docker-build=remote`
          setting), rather than the Container Builder API to perform docker
          builds, run:

              $ gcloud config set app/use_cloud_build false

          See https://cloud.google.com/container-builder/docs/ for more
          information.
          """,
      'EXAMPLES': """\
          To deploy a single module, run:

            $ {command} ~/my_app/app.yaml

          To deploy multiple modules, run:

            $ {command} ~/my_app/app.yaml ~/my_app/another_module.yaml
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
    docker_build_group = parser.add_mutually_exclusive_group()
    docker_build_group.add_argument(
        '--docker-build',
        choices=['remote', 'local'],
        default=None,
        help=("Perform a hosted ('remote') or local ('local') Docker build. To "
              "perform a local build, you must have your local docker "
              "environment configured correctly. The default is a hosted "
              "build."))
    deployables = parser.add_argument(
        'deployables', nargs='*',
        help='The yaml files for the modules or configurations you want to '
        'deploy.')
    deployables.detailed_help = (
        'The yaml files for the modules or configurations you want to deploy. '
        'If not given, defaults to `app.yaml` in the current directory. '
        'If that is not found, attempts to automatically generate necessary '
        'configuration files (such as app.yaml) in the current directory.')
    parser.add_argument(
        '--repo-info-file', metavar='filename',
        help=argparse.SUPPRESS)
    unused_repo_info_file_help = (
        'The name of a file containing source context information for the '
        'modules being deployed. If not specified, the source context '
        'information will be inferred from the directory containing the '
        'app.yaml file.')
    parser.add_argument(
        '--stop-previous-version',
        action='store_true',
        default=None,
        help='Stop the previously running version when deploying a new version '
             'that receives all traffic (off by default).')
    parser.add_argument(
        '--image-url',
        help='Deploy with a specific Docker image.  Docker url must be '
        'from one of the valid gcr hostnames.')
    promote = parser.add_argument(
        '--promote',
        nargs=0,
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
    use_cloud_build = properties.VALUES.app.use_cloud_build.GetBool()

    config_cleanup = None
    if args.deployables:
      app_config = yaml_parsing.AppConfigSet(args.deployables)
    else:
      if not os.path.exists(DEFAULT_DEPLOYABLE):
        console_io.PromptContinue(
            'Deployment to Google App Engine requires an app.yaml file. '
            'This command will run `gcloud preview app gen-config` to generate '
            'an app.yaml file for you in the current directory (if the current '
            'directory does not contain an App Engine module, please answer '
            '"no").', cancel_on_no=True)
        # This generates the app.yaml AND the Dockerfile (and related files).
        params = ext_runtime.Params(deploy=True)
        configurator = fingerprinter.IdentifyDirectory(os.getcwd(),
                                                       params=params)
        if configurator is None:
          raise NoAppIdentifiedError(
              'Could not identify an app in the current directory.\n\n'
              'Please prepare an app.yaml file for your application manually '
              'and deploy again.')
        config_cleanup = configurator.GenerateConfigs()
        log.status.Print('\nCreated [{0}] in the current directory.\n'.format(
            DEFAULT_DEPLOYABLE))
      app_config = yaml_parsing.AppConfigSet([DEFAULT_DEPLOYABLE])

    # If the app has enabled Endpoints API Management features, pass
    # control to the cloud_endpoints handler.
    for _, module in app_config.Modules().items():
      if module and module.parsed and module.parsed.beta_settings:
        bs = module.parsed.beta_settings
        use_endpoints = bs.get('use_endpoints_api_management', '').lower()
        if (use_endpoints in ('true', '1', 'yes') and
            bs.get('endpoints_swagger_spec_file')):
          cloud_endpoints.PushServiceConfig(
              bs.get('endpoints_swagger_spec_file'),
              project,
              apis.GetClientInstance('servicemanagement', 'v1'),
              apis.GetMessagesModule('servicemanagement', 'v1'))

    remote_build = True
    docker_build_property = properties.VALUES.app.docker_build.Get()
    if args.docker_build:
      remote_build = args.docker_build == 'remote'
    elif docker_build_property:
      remote_build = docker_build_property == 'remote'

    clients = _AppEngineClients(
        appengine_client.AppengineClient(args.server,
                                         args.ignore_bad_certs),
        appengine_api_client.GetApiClient())
    log.debug('API endpoint: [{endpoint}], API version: [{version}]'.format(
        endpoint=clients.api.client.url,
        version=clients.api.api_version))
    cloudbuild_client = apis.GetClientInstance('cloudbuild', 'v1')
    storage_client = apis.GetClientInstance('storage', 'v1')
    promote = properties.VALUES.app.promote_by_default.GetBool()
    deployed_urls = _DisplayProposedDeployment(project, app_config, version,
                                               promote)
    if args.version or promote:
      # Prompt if there's a chance that you're overwriting something important:
      # If the version is set manually, you could be deploying over something.
      # If you're setting the new deployment to be the default version, you're
      # changing the target of the default URL.
      # Otherwise, all existing URLs will continue to work, so need to prompt.
      console_io.PromptContinue(default=True, throw_if_unattended=False,
                                cancel_on_no=True)

    log.status.Print('Beginning deployment...')

    source_contexts = []
    if args.repo_info_file:
      if args.image_url:
        raise NoRepoInfoWithImageUrlError()

      try:
        with open(args.repo_info_file, 'r') as f:
          source_contexts = json.load(f)
      except (ValueError, IOError) as ex:
        raise RepoInfoLoadError(args.repo_info_file, ex)
      if isinstance(source_contexts, dict):
        # This is an old-style source-context.json file. Convert to a new-
        # style array of extended contexts.
        source_contexts = [context_util.ExtendContextDict(source_contexts)]

    code_bucket_ref = None
    if use_cloud_build or app_config.NonHermeticModules():
      # If using Argo CloudBuild, we'll need to upload source to a GCS bucket.
      code_bucket_ref = self._GetCodeBucket(clients.api, args)
      metrics.CustomTimedEvent(metric_names.GET_CODE_BUCKET)
      log.debug('Using bucket [{b}].'.format(b=code_bucket_ref))

    modules = app_config.Modules()
    if any([m.RequiresImage() for m in modules.values()]):
      deploy_command_util.DoPrepareManagedVms(clients.gae)
    if args.image_url:
      if len(modules) != 1:
        raise MultiDeployError()
      for registry in constants.ALL_SUPPORTED_REGISTRIES:
        if args.image_url.startswith(registry):
          break
      else:
        raise UnsupportedRegistryError(args.image_url)
      module = modules.keys()[0]
      images = {module: args.image_url}
    else:
      images = deploy_command_util.BuildAndPushDockerImages(modules,
                                                            version,
                                                            cloudbuild_client,
                                                            storage_client,
                                                            code_bucket_ref,
                                                            self.cli,
                                                            remote_build,
                                                            source_contexts,
                                                            config_cleanup)

    deployment_manifests = {}
    if app_config.NonHermeticModules():
      if properties.VALUES.app.use_gsutil.GetBool():
        copy_func = deploy_app_command_util.CopyFilesToCodeBucket
        metric_name = metric_names.COPY_APP_FILES
      else:
        copy_func = deploy_app_command_util.CopyFilesToCodeBucketNoGsUtil
        metric_name = metric_names.COPY_APP_FILES_NO_GSUTIL

      deployment_manifests = copy_func(
          app_config.NonHermeticModules().items(),
          code_bucket_ref,
          source_contexts,
          storage_client)
      metrics.CustomTimedEvent(metric_name)

    all_services = clients.api.ListServices()
    # Now do deployment.
    for (module, info) in app_config.Modules().iteritems():
      message = 'Updating module [{module}]'.format(module=module)
      with console_io.ProgressTracker(message):
        if args.force:
          log.warning('The --force argument is deprecated and no longer '
                      'required. It will be removed in a future release.')

        clients.api.DeployModule(module, version, info,
                                 deployment_manifests.get(module),
                                 images.get(module))
        metrics.CustomTimedEvent(metric_names.DEPLOY_API)

        stop_previous_version = (
            deploy_command_util.GetStopPreviousVersionFromArgs(args))
        if promote:
          new_version = version_util.Version(project, module, version)
          _Promote(all_services, new_version, clients,
                   stop_previous_version)
        elif stop_previous_version:
          log.info('Not stopping previous version because new version was not '
                   'promoted.')

    # Config files.
    for (c, info) in app_config.Configs().iteritems():
      message = 'Updating config [{config}]'.format(config=c)
      with console_io.ProgressTracker(message):
        clients.gae.UpdateConfig(c, info.parsed)
    return deployed_urls

  def Display(self, args, result):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    writer = log.out
    for module, url in result.items():
      writer.Print('Deployed module [{0}] to [{1}]'.format(module, url))

  def _GetCodeBucket(self, api_client, args):
    if args.bucket:
      bucket_with_gs = args.bucket
    else:
      # Attempt to retrieve the default appspot bucket, if one can be created.
      log.debug('No bucket specified, retrieving default bucket.')
      bucket_with_gs = api_client.GetApplicationCodeBucket()
      if not bucket_with_gs:
        project = properties.VALUES.core.project.Get(required=True)
        raise DefaultBucketAccessError(project)

    return cloud_storage.BucketReference(bucket_with_gs)

# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Utilities for loading and parsing kubeconfig."""


import os
import subprocess

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import platforms
from googlecloudsdk.core.util import times


class Error(core_exceptions.Error):
  """Class for errors raised by kubeconfig utilities."""


class MissingEnvVarError(Error):
  """An exception raised when required environment variables are missing."""


GKE_GCLOUD_AUTH_PLUGIN_CACHE_FILE_NAME = 'gke_gcloud_auth_plugin_cache'


class Kubeconfig(object):
  """Interface for interacting with a kubeconfig file."""

  def __init__(self, raw_data, filename):
    self._filename = filename
    self._data = raw_data
    self.clusters = {}
    self.users = {}
    self.contexts = {}

    self._ReadKubeconfigSectionIntoDict('clusters', self.clusters)
    self._ReadKubeconfigSectionIntoDict('users', self.users)
    self._ReadKubeconfigSectionIntoDict('contexts', self.contexts)
    # WARNING: if an Error is raised here, LoadOrCreate will catch it, save a
    # backup of ~/.kube/config to ~/.kube/config.<timestamp>.backup, and
    # re-create it with only one entry for current context.

  @classmethod
  def _GetEntryLocationDesc(cls, index, item, last_seen_name, section_name):
    """Returns a description of the location of an entry inside a section.

    Examples:
      - "entry 'my-cluster' in clusters section"
      - "entry at zero-starting-index 2 (after entry 'dev-cluster') in clusters
        section"
      - "entry 'prod-cluster' at line 42 in clusters section"
      - "clusters section" (when index is None)

    Args:
      index: int or None, 0-based index of the entry inside the section.
      item: dict or object, the section element data.
      last_seen_name: str or None, name of the preceding valid entry.
      section_name: str, formatted section name.

    Returns:
      str, descriptive location string indicating where the entry is located.
    """
    if index is None:
      return section_name

    parts = []
    item_name = None
    if isinstance(item, dict):
      item_name = item.get('name')

    if item_name:
      parts.append('entry \'{0}\''.format(item_name))
    else:
      parts.append('entry at zero-starting-index {0}'.format(index))

    if last_seen_name and item_name != last_seen_name:
      parts.append('(after entry \'{0}\')'.format(last_seen_name))

    line_num = None
    if hasattr(item, 'lc') and getattr(item.lc, 'line', None) is not None:
      line_num = item.lc.line + 1
    elif (
        isinstance(item, dict)
        and hasattr(item, 'lc')
        and getattr(item.lc, 'line', None) is not None
    ):
      line_num = item.lc.line + 1

    if line_num is not None:
      parts.append('at line {0}'.format(line_num))

    parts.append('in {0}'.format(section_name))
    return ' '.join(parts)

  def _ReadKubeconfigSectionIntoDict(self, section_key, target_dict):
    """Populates target dictionary with entries from a kubeconfig section.

    Args:
      section_key: str, section name in parsed kubeconfig data (e.g.
        'clusters').
      target_dict: dict, dictionary to populate with entries keyed by entry
        'name'.

    Raises:
      Error: if the section key or entry 'name' is missing, or if data is
        malformed.
    """
    file_desc = self._filename or 'kubeconfig'
    try:
      items = self._data[section_key]
    except (KeyError, TypeError) as error:
      if isinstance(error, KeyError):
        raise Error(
            'Expected top-level section key \'{0}\' not found in root of'
            ' \'{1}\''.format(
                error.args[0] if error.args else error, file_desc
            )
        ) from error
      raise Error(
          '{0} : Most likely the root of \'{1}\' is empty or invalid'.format(
              error, file_desc
          )
      ) from error

    section_name = '{0} section'.format(section_key)
    index = None
    item = None
    last_seen_name = None
    try:
      for index, item in enumerate(items):
        name = item['name']
        target_dict[name] = item
        last_seen_name = name
    except TypeError as error:
      location_desc = self._GetEntryLocationDesc(
          index, item, last_seen_name, section_name
      )
      raise Error(
          '{0} : Most likely there is empty data in {1} of \'{2}\''.format(
              error, location_desc, file_desc
          )
      ) from error
    except KeyError as error:
      location_desc = self._GetEntryLocationDesc(
          index, item, last_seen_name, section_name
      )
      raise Error(
          'Expected key \'{0}\' not found in {1} of \'{2}\''.format(
              error.args[0] if error.args else error, location_desc, file_desc
          )
      ) from error

  @property
  def current_context(self):
    return self._data['current-context']

  @property
  def filename(self):
    return self._filename

  def Clear(self, key):
    self.contexts.pop(key, None)
    self.clusters.pop(key, None)
    self.users.pop(key, None)
    if self._data.get('current-context') == key:
      self._data['current-context'] = ''

  def SaveToFile(self):
    """Save kubeconfig to file.

    Raises:
      Error: don't have the permission to open kubeconfig or plugin cache file.
    """
    self._data['clusters'] = list(self.clusters.values())
    self._data['users'] = list(self.users.values())
    self._data['contexts'] = list(self.contexts.values())
    with file_utils.FileWriter(self._filename, private=True) as fp:
      yaml.dump(self._data, fp)

    # GKE_GCLOUD_AUTH_PLUGIN_CACHE_FILE_NAME is used by GKE_GCLOUD_AUTH_PLUGIN
    # Erase cache file everytime kubeconfig is updated. This allows for a reset
    # of the cache. Previously, credentials were cached in the kubeconfig file
    # and updating the kubeconfig allowed for a "reset" of the cache.
    dirname = os.path.dirname(self._filename)
    gke_gcloud_auth_plugin_file_path = os.path.join(
        dirname, GKE_GCLOUD_AUTH_PLUGIN_CACHE_FILE_NAME
    )
    if os.path.exists(gke_gcloud_auth_plugin_file_path):
      file_utils.WriteFileAtomically(gke_gcloud_auth_plugin_file_path, '')

  def SetCurrentContext(self, context):
    self._data['current-context'] = context

  @classmethod
  def _Validate(cls, data, filename=None):
    """Make sure we have the main fields of a kubeconfig."""
    file_desc = filename or 'kubeconfig'
    if not data:
      raise Error('Empty file: \'{0}\''.format(file_desc))
    try:
      for key in ('clusters', 'users', 'contexts'):
        if not isinstance(data[key], list):
          raise Error(
              'Invalid type for \'{0}\' in \'{1}\': {2}'.format(
                  data[key], file_desc, type(data[key])
              )
          )
    except KeyError as error:
      raise Error(
          'Expected key \'{0}\' not found in \'{1}\''.format(
              error.args[0] if error.args else error, file_desc
          )
      ) from error

  @classmethod
  def LoadFromFile(cls, filename):
    try:
      data = yaml.load_path(filename)
    except yaml.Error as error:
      raise Error(
          'unable to load kubeconfig for {0}: {1}'.format(
              filename, error.inner_error
          )
      ) from error
    cls._Validate(data, filename=filename)
    return cls(data, filename)

  @classmethod
  def LoadOrCreate(cls, path):
    """Read in the kubeconfig, and if it doesn't exist create one there."""
    if os.path.isdir(path):
      raise IsADirectoryError(
          '{0} is a directory. File must be provided.'.format(path)
      )
    if os.path.isfile(path):
      try:
        return cls.LoadFromFile(path)
      except (Error, IOError) as error:
        # Use hyphens instead of colons in the timestamp format because ':' is
        # an illegal filename character on Windows.
        timestamp = times.FormatDateTime(
            times.Now(times.UTC), '%Y-%m-%dT%H-%M-%SZ'
        )
        pid = os.getpid()  # add unique PID to backup file name
        counter = 0
        backup_path = '{0}.{1}.{2}.00.backup'.format(path, timestamp, pid)
        while os.path.exists(backup_path) and counter < 99:
          # add unique number 01..99 to backup file name if it already exists
          counter += 1
          backup_path = '{0}.{1}.{2}.{3:02d}.backup'.format(
              path, timestamp, pid, counter
          )
        try:
          os.rename(path, backup_path)
          log.warning(
              'Unable to load default kubeconfig: {0}; saved backup to {1}'
              ' and recreating {2}'.format(error, backup_path, path)
          )
        except OSError:
          log.debug(
              'Unable to load default kubeconfig: {0}; recreating {1}'.format(
                  error, path
              )
          )
    file_utils.MakeDir(os.path.dirname(path))
    kubeconfig = cls(EmptyKubeconfig(), path)
    kubeconfig.SaveToFile()
    return kubeconfig

  @classmethod
  def Default(cls):
    return cls.LoadOrCreate(Kubeconfig.DefaultPath())

  @staticmethod
  def DefaultPath():
    """Return default path for kubeconfig file."""

    kubeconfig = encoding.GetEncodedValue(os.environ, 'KUBECONFIG')
    if kubeconfig:
      # split $KUBECONFIG env var into individual paths separated by ':'
      paths = kubeconfig.split(os.pathsep)
      for kubeconfig in paths:
        # KUBECONFIG=$KUBECONFIG:~/.kube/config might become ':~/.kube/config'
        # if KUBECONFIG is not set.
        if kubeconfig:  # only consider non-empty paths
          return os.path.abspath(kubeconfig)

    # This follows the same resolution process as kubectl for the config file.
    home_dir = encoding.GetEncodedValue(os.environ, 'HOME')
    if not home_dir and platforms.OperatingSystem.IsWindows():
      home_drive = encoding.GetEncodedValue(os.environ, 'HOMEDRIVE')
      home_path = encoding.GetEncodedValue(os.environ, 'HOMEPATH')
      if home_drive and home_path:
        home_dir = os.path.join(home_drive, home_path)
      if not home_dir:
        home_dir = encoding.GetEncodedValue(os.environ, 'USERPROFILE')

    if not home_dir:
      raise MissingEnvVarError(
          'environment variable {vars} or KUBECONFIG must be set to store '
          'credentials for kubectl'.format(
              vars='HOMEDRIVE/HOMEPATH, USERPROFILE, HOME,'
              if platforms.OperatingSystem.IsWindows()
              else 'HOME'
          )
      )
    return os.path.join(home_dir, '.kube', 'config')

  def Merge(self, kubeconfig):
    """Merge another kubeconfig into self.

    In case of overlapping keys, the value in self is kept and the value in
    the other kubeconfig is lost.

    Args:
      kubeconfig: a Kubeconfig instance
    """
    self.SetCurrentContext(self.current_context or kubeconfig.current_context)
    self.clusters = dict(
        list(kubeconfig.clusters.items()) + list(self.clusters.items())
    )
    self.users = dict(list(kubeconfig.users.items()) + list(self.users.items()))
    self.contexts = dict(
        list(kubeconfig.contexts.items()) + list(self.contexts.items())
    )


def Cluster(name, server, ca_path=None, ca_data=None, has_dns_endpoint=False):
  """Generate and return a cluster kubeconfig object."""
  cluster = {
      'server': server,
  }
  if ca_path and ca_data:
    raise Error('cannot specify both ca_path and ca_data')
  if ca_path:
    cluster['certificate-authority'] = ca_path
  elif ca_data is not None and not has_dns_endpoint:
    cluster['certificate-authority-data'] = ca_data
  elif not has_dns_endpoint:
    cluster['insecure-skip-tls-verify'] = True
  return {'name': name, 'cluster': cluster}


def User(
    name,
    auth_provider=None,
    auth_provider_cmd_path=None,
    auth_provider_cmd_args=None,
    auth_provider_expiry_key=None,
    auth_provider_token_key=None,
    cert_path=None,
    cert_data=None,
    key_path=None,
    key_data=None,
    impersonate_service_account=None,
    iam_token=None,
):
  """Generates and returns a user kubeconfig object.

  Args:
    name: str, nickname for this user entry.
    auth_provider: str, authentication provider.
    auth_provider_cmd_path: str, authentication provider command path.
    auth_provider_cmd_args: str, authentication provider command args.
    auth_provider_expiry_key: str, authentication provider expiry key.
    auth_provider_token_key: str, authentication provider token key.
    cert_path: str, path to client certificate file.
    cert_data: str, base64 encoded client certificate data.
    key_path: str, path to client key file.
    key_data: str, base64 encoded client key data.
    impersonate_service_account: str, service account to impersonate.
    iam_token: str, IAM token to use for authentication.

  Returns:
    dict, valid kubeconfig user entry.

  Raises:
    Error: if no auth info is provided (auth_provider or cert AND key)
  """
  # TODO(b/70856999) Figure out what the correct behavior for client certs is.
  if not (
      auth_provider or (cert_path and key_path) or (cert_data and key_data)
  ):
    raise Error('either auth_provider or cert & key must be provided')
  user = {}
  use_exec_auth = _UseExecAuth()

  if auth_provider:
    # Setup authprovider
    # if certain 'auth_provider_' fields are "present" OR
    # if use_exec_auth is set to False
    # pylint: disable=line-too-long
    if (
        auth_provider_cmd_path
        or auth_provider_cmd_args
        or auth_provider_expiry_key
        or auth_provider_token_key
        or not use_exec_auth
    ):
      # auth-provider is being deprecated in favor of "exec" in k8s 1.25.
      user['auth-provider'] = _AuthProvider(
          name=auth_provider,
          cmd_path=auth_provider_cmd_path,
          cmd_args=auth_provider_cmd_args,
          expiry_key=auth_provider_expiry_key,
          token_key=auth_provider_token_key,
      )
    else:
      user['exec'] = _ExecAuthPlugin(impersonate_service_account)

  if cert_path and cert_data:
    raise Error('cannot specify both cert_path and cert_data')
  if cert_path:
    user['client-certificate'] = cert_path
  elif cert_data:
    user['client-certificate-data'] = cert_data

  if key_path and key_data:
    raise Error('cannot specify both key_path and key_data')
  if key_path:
    user['client-key'] = key_path
  elif key_data:
    user['client-key-data'] = key_data

  if iam_token:
    user['token'] = iam_token
    log.status.Print(f'Added IAM token to kubeconfig entry for user {name}.')

  return {'name': name, 'user': user}


def _UseExecAuth():
  """Returns a bool noting if ExecAuth should be enabled.

  Returns:
    bool, which notes if ExecAuth should be enabled
  """
  # Enable ExecAuth for all users
  use_exec_auth = True

  use_gke_gcloud_auth_plugin = encoding.GetEncodedValue(
      os.environ, 'USE_GKE_GCLOUD_AUTH_PLUGIN'
  )
  # if use_gke_gcloud_auth_plugin is explicitly set(True/False), take action.
  # if use_gke_gcloud_auth_plugin is NOT explicitly set, do nothing
  if (
      use_gke_gcloud_auth_plugin
      and use_gke_gcloud_auth_plugin.lower() == 'true'
  ):
    use_exec_auth = True
  elif (
      use_gke_gcloud_auth_plugin
      and use_gke_gcloud_auth_plugin.lower() == 'false'
  ):
    use_exec_auth = False

  return use_exec_auth


SDK_BIN_PATH_NOT_FOUND = """\
Path to sdk installation not found. Please switch to application default
credentials using one of

$ gcloud config set container/use_application_default_credentials true
$ export CLOUDSDK_CONTAINER_USE_APPLICATION_DEFAULT_CREDENTIALS=true"""

GKE_GCLOUD_AUTH_INSTALL_HINT = """\
Install gke-gcloud-auth-plugin for use with kubectl by following \
https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl#install_plugin"""

GKE_GCLOUD_AUTH_PLUGIN_NOT_FOUND = """\
ACTION REQUIRED: gke-gcloud-auth-plugin, \
which is needed for continued use of kubectl, was not found or is not executable. \
""" + GKE_GCLOUD_AUTH_INSTALL_HINT


def _ExecAuthPlugin(impersonate_service_account=None):
  """Generate and return an exec auth plugin config.

  Constructs an exec auth plugin config entry readable by kubectl.
  This tells kubectl to call out to gke-gcloud-auth-plugin and
  parse the output to retrieve access tokens to authenticate to
  the kubernetes master.

  Kubernetes GKE Auth Provider plugin is defined at
  https://kubernetes.io/docs/reference/access-authn-authz/authentication/#client-go-credential-plugins

  GKE GCloud Exec Auth Plugin code is at
  https://github.com/kubernetes/cloud-provider-gcp/tree/master/cmd/gke-gcloud-auth-plugin

  Args:
    impersonate_service_account: str, service account to impersonate.

  Returns:
    dict, valid exec auth plugin config entry.
  Raises:
    Error: Only one of --dns-endpoint or USE_APPLICATION_DEFAULT_CREDENTIALS
    should be set at a time.
  """

  use_application_default_credentials = (
      properties.VALUES.container.use_app_default_credentials.GetBool()
  )
  command = _GetGkeGcloudPluginCommandAndPrintWarning()

  exec_cfg = {
      'command': command,
      'apiVersion': 'client.authentication.k8s.io/v1beta1',
      'installHint': GKE_GCLOUD_AUTH_INSTALL_HINT,
      'provideClusterInfo': True,
  }

  args = []
  if use_application_default_credentials:
    args.append('--use_application_default_credentials')
  if impersonate_service_account:
    args.append('--impersonate_service_account=' + impersonate_service_account)

  if args:
    exec_cfg['args'] = args

  return exec_cfg


def _AuthProvider(
    name='gcp', cmd_path=None, cmd_args=None, expiry_key=None, token_key=None
):
  """Generates and returns an auth provider config.

  Constructs an auth provider config entry readable by kubectl. This tells
  kubectl to call out to a specific gcloud command and parse the output to
  retrieve access tokens to authenticate to the kubernetes master.
  Kubernetes gcp auth provider plugin at
  https://github.com/kubernetes/kubernetes/tree/master/staging/src/k8s.io/client-go/plugin/pkg/client/auth/gcp

  Args:
    name: auth provider name
    cmd_path: str, authentication provider command path.
    cmd_args: str, authentication provider command arguments.
    expiry_key: str, authentication provider expiry key.
    token_key: str, authentication provider token key.

  Returns:
    dict, valid auth provider config entry.
  Raises:
    Error: Path to sdk installation not found. Please switch to application
    default credentials using one of

    $ gcloud config set container/use_application_default_credentials true
    $ export CLOUDSDK_CONTAINER_USE_APPLICATION_DEFAULT_CREDENTIALS=true.
  """
  provider = {'name': name}
  if (
      name == 'gcp'
      and not properties.VALUES.container.use_app_default_credentials.GetBool()
  ):
    bin_name = 'gcloud'
    if platforms.OperatingSystem.IsWindows():
      bin_name = 'gcloud.cmd'

    if cmd_path is None:
      sdk_bin_path = config.Paths().sdk_bin_path
      if sdk_bin_path is None:
        log.error(SDK_BIN_PATH_NOT_FOUND)
        raise Error(SDK_BIN_PATH_NOT_FOUND)
      cmd_path = os.path.join(sdk_bin_path, bin_name)
      try:
        # Print warning if gke-gcloud-auth-plugin is not present or executable
        _GetGkeGcloudPluginCommandAndPrintWarning()
      except Exception:  # pylint: disable=broad-except
        # Catch all exceptions to avoid any failures in this code path and
        # ignore the exceptions, as no action needs to be taken.
        pass

    cfg = {
        # Command for gcloud credential helper
        'cmd-path': cmd_path,
        # Args for gcloud credential helper
        'cmd-args': (
            cmd_args if cmd_args else 'config config-helper --format=json'
        ),
        # JSONpath to the field that is the raw access token
        'token-key': token_key if token_key else '{.credential.access_token}',
        # JSONpath to the field that is the expiration timestamp
        'expiry-key': (
            expiry_key if expiry_key else '{.credential.token_expiry}'
        ),
        # Note: we're omitting 'time-fmt' field, which if provided, is a
        # format string of the golang reference time. It can be safely omitted
        # because config-helper's default time format is RFC3339, which is the
        # same default kubectl assumes.
    }
    provider['config'] = cfg
  return provider


def _GetGkeGcloudPluginCommandAndPrintWarning():
  """Get Gke Gcloud Plugin Command to be used.

  Returns Gke Gcloud Plugin Command to be used. Also,
  prints warning if plugin is not present or doesn't work correctly.

  Returns:
    string, Gke Gcloud Plugin Command to be used.
  """
  bin_name = 'gke-gcloud-auth-plugin'
  if platforms.OperatingSystem.IsWindows():
    bin_name = 'gke-gcloud-auth-plugin.exe'
  command = bin_name

  # Check if command is in PATH and executable. Else, print critical(RED)
  # warning as kubectl will break if command is not executable.
  try:
    subprocess.run(
        [command, '--version'],
        timeout=5,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
  except Exception:  # pylint: disable=broad-except
    # Provide SDK Full path if command is not in PATH. This helps work
    # around scenarios where cloud-sdk install location is not in PATH
    # as sdk was installed using other distributions methods Eg: brew
    try:
      # config.Paths().sdk_bin_path throws an exception in some test envs,
      # but is commonly defined in prod environments
      sdk_bin_path = config.Paths().sdk_bin_path
      if sdk_bin_path is None:
        log.critical(GKE_GCLOUD_AUTH_PLUGIN_NOT_FOUND)
      else:
        sdk_path_bin_name = os.path.join(sdk_bin_path, command)
        subprocess.run(
            [sdk_path_bin_name, '--version'],
            timeout=5,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        command = sdk_path_bin_name  # update command if sdk_path_bin_name works
    except Exception:  # pylint: disable=broad-except
      log.critical(GKE_GCLOUD_AUTH_PLUGIN_NOT_FOUND)

  return command


def Context(name, cluster, user):
  """Generate and return a context kubeconfig object."""
  return {
      'name': name,
      'context': {
          'cluster': cluster,
          'user': user,
      },
  }


def EmptyKubeconfig():
  return {
      'apiVersion': 'v1',
      'contexts': [],
      'clusters': [],
      'current-context': '',
      'kind': 'Config',
      'preferences': {},
      'users': [],
  }

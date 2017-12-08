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
"""Utility wrappers around apitools generator."""

import json
import logging
import os
import re

from apitools.gen import gen_client
from tools.regen_apis import api_def
from mako import runtime
from mako import template


_COLLECTION_SUB_RE = r'[a-zA-Z_]+(?:\.[a-zA-Z0-9_]+)+'
_METHOD_ID_RE = re.compile(r'(?P<collection>{collection})\.get'.format(
    collection=_COLLECTION_SUB_RE))

_INIT_FILE_CONTENT = """\
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

"""


class NoDefaultApiError(Exception):
  """Multiple apis versions are specified but no default is set."""


class WrongDiscoveryDoc(Exception):
  """Unexpected discovery doc."""


class AmbiguousResourcePath(Exception):
  """Exception for when API path maps to two different resources."""

  def __init__(self, collection1, collection2):
    super(AmbiguousResourcePath, self).__init__(
        'Duplicate collection in {0} path {1} when merging {2} with path {3}'
        .format(collection1.name, collection1.path,
                collection2.name, collection2.path))


def GenerateApi(base_dir, root_dir, api_name, api_version, api_config):
  """Invokes apitools generator for given api."""
  discovery_doc = api_config['discovery_doc']

  args = [gen_client.__file__]

  unelidable_request_methods = api_config.get('unelidable_request_methods')
  if unelidable_request_methods:
    args.append('--unelidable_request_methods={0}'.format(
        ','.join(api_config['unelidable_request_methods'])))

  args.extend([
      '--init-file=empty',
      '--nogenerate_cli',
      '--infile={0}'.format(os.path.join(base_dir, root_dir, discovery_doc)),
      '--outdir={0}'.format(os.path.join(base_dir, root_dir, api_name,
                                         api_version)),
      '--overwrite',
      '--apitools_version=CloudSDK',
      '--root_package',
      '{0}.{1}.{2}'.format(
          root_dir.replace('/', '.'), api_name, api_version),
      'client',
  ])
  logging.debug('Apitools gen %s', args)
  gen_client.main(args)

  package_dir = ''
  for subdir in [base_dir, root_dir, api_name, api_version]:
    package_dir = os.path.join(package_dir, subdir)
    init_file = os.path.join(package_dir, '__init__.py')
    if not os.path.isfile(init_file):
      logging.warn('%s does not have __init__.py file, generating ...',
                   package_dir)
      with open(init_file, 'w') as f:
        f.write(_INIT_FILE_CONTENT)


def _MakeApiMap(root_package, api_config):
  """Converts a map of api_config into ApiDef.

  Args:
    root_package: str, root path of where generate api will reside.
    api_config: {api_name->api_version->{discovery,default,version,...}},
                description of each api.
  Returns:
    {api_name->api_version->ApiDef()}.

  Raises:
    NoDefaultApiError: if for some api with multiple versions
        default was not specified.
  """
  apis_map = {}
  apis_with_default = set()
  for api_name, api_version_config in api_config.iteritems():
    api_versions_map = apis_map.setdefault(api_name, {})
    has_default = False
    for api_version, api_config in api_version_config.iteritems():
      default = api_config.get('default', len(api_version_config) == 1)
      has_default = has_default or default
      client_classpath = '.'.join([
          root_package,
          api_name,
          api_version,
          '_'.join([api_name, api_version, 'client']),
          api_name.capitalize() + api_version.capitalize()])
      messages_modulepath = '.'.join([
          root_package,
          api_name,
          api_version,
          '_'.join([api_name, api_version, 'messages']),
      ])
      api_versions_map[api_version] = api_def.APIDef(
          client_classpath, messages_modulepath, default)
    if has_default:
      apis_with_default.add(api_name)

  apis_without_default = set(apis_map.keys()).difference(apis_with_default)
  if apis_without_default:
    raise NoDefaultApiError('No default client versions found for [{0}]!'
                            .format(', '.join(sorted(apis_without_default))))
  return apis_map


def GenerateApiMap(base_dir, root_dir, api_config):
  """Create an apis_map.py file in the given root_dir with for given api_config.

  Args:
      base_dir: str, Path of directory for the project.
      root_dir: str, Path of the map file location within the project.
      api_config: regeneration config for all apis.
  """

  api_def_filename, _ = os.path.splitext(api_def.__file__)
  with open(api_def_filename + '.py', 'rU') as api_def_file:
    api_def_source = api_def_file.read()

  tpl = template.Template(filename=os.path.join(os.path.dirname(__file__),
                                                'template.tpl'))
  api_map_file = os.path.join(base_dir, root_dir, 'apis_map.py')
  logging.debug('Generating api map at %s', api_map_file)
  api_map = _MakeApiMap(root_dir.replace('/', '.'), api_config)
  logging.debug('Creating following api map %s', api_map)
  with open(api_map_file, 'wb') as apis_map_file:
    ctx = runtime.Context(apis_map_file,
                          api_def_source=api_def_source,
                          apis_map=api_map)
    tpl.render_context(ctx)


class CollectionInfo(object):
  """Holds structural metadata for collection resources."""

  def __init__(self, api_name, api_version, base_url, name, path, params):
    self.api_name = api_name
    self.api_version = api_version
    self.base_url = base_url
    self.name = name
    self.path = path
    self.params = params

  def GetSplitPath(self, max_length):
    """Splits path into chunks of max_length."""
    parts = []
    path = self.path
    while path:
      if len(path) < max_length:
        index = max_length
      else:
        # Prefer to split on last '/'.
        index = path.rfind('/', 0, max_length - 1)
        if index < 0:
          index = min(max_length - 1, len(path) - 1)
      parts.append(path[:index+1])
      path = path[index+1:]
    return parts

  def __cmp__(self, other):
    return cmp((self.api_name, self.api_version, self.name),
               (other.api_name, other.api_version, other.name))

  def __str__(self):
    return self.name


def _GetPathParams(path):
  """Extract parameters from path."""
  parts = path.split('/')
  params = []
  for part in parts:
    if part.startswith('{') and part.endswith('}'):
      part = part[1:-1]
      if part.startswith('+'):
        params.append(part[1:])
      else:
        params.append(part)
  return params


def _ExtractResources(api_name, api_version, base_url, infos):
  """Extract resource definitions from discovery doc."""
  collections = []
  for name, info in infos.iteritems():
    if name == 'methods':
      get_method = info.get('get')
      if get_method:
        method_id = get_method['id']
        match = _METHOD_ID_RE.match(method_id)
        if match:
          collection_name = match.group('collection')
          path = get_method.get('flatPath')
          if not path:
            path = get_method.get('path')
          collection_info = CollectionInfo(
              api_name, api_version, base_url, collection_name,
              path, _GetPathParams(path))
          collections.append(collection_info)
    else:
      subresource_collections = _ExtractResources(
          api_name, api_version, base_url, info)
      collections.extend(subresource_collections)
  return collections


def GenerateResourceModule(base_dir, root_dir, api_config):
  """Create resource.py file in the given root_dir with for given api_config.

  Args:
      base_dir: str, Path of directory for the project.
      root_dir: str, Path of the resource file location within the project.
      api_config: regeneration config for all apis.
  Raises:
    WrongDiscoveryDoc: if discovery doc api name/version does not match.
  """
  tpl = template.Template(filename=os.path.join(os.path.dirname(__file__),
                                                'resources.tpl'))

  resource_file_name = os.path.join(base_dir, root_dir, 'resources.py')
  logging.debug('Generating resource module at %s', resource_file_name)

  collections = []
  for api_name, api_version_config in api_config.iteritems():
    for api_version, api_config in api_version_config.iteritems():
      discovery_doc = os.path.join(base_dir, root_dir,
                                   api_config['discovery_doc'])
      with open(discovery_doc, 'rU') as f:
        discovery = json.load(f)
      if discovery['version'] != api_version:
        raise WrongDiscoveryDoc('api version {0}, expected {1}'
                                .format(discovery['version'], api_version))
      if discovery['name'] != api_name:
        raise WrongDiscoveryDoc('api name {0}, expected {1}'
                                .format(discovery['name'], api_name))
      base_url = discovery['baseUrl']
      try:
        resource_collections = _ExtractResources(
            api_name, api_version, base_url, discovery['resources'])
      except AmbiguousResourcePath as e:
        logging.warn(e)
        continue
      collections.extend(resource_collections)

  with open(resource_file_name, 'wb') as output_file:
    ctx = runtime.Context(output_file, collections=sorted(collections))
    tpl.render_context(ctx)

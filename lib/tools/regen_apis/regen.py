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
from googlecloudsdk.api_lib.util import resource as resource_util
from tools.regen_apis import api_def
from mako import runtime
from mako import template


_COLLECTION_SUB_RE = r'[a-zA-Z_]+(?:\.[a-zA-Z0-9_]+)+'
_METHOD_ID_RE = re.compile(r'(?P<collection>{collection})\.get'.format(
    collection=_COLLECTION_SUB_RE))
_DEFAULT_PATH_NAME = ''

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

  package_dir = base_dir
  for subdir in [root_dir, api_name, api_version]:
    package_dir = os.path.join(package_dir, subdir)
    init_file = os.path.join(package_dir, '__init__.py')
    if not os.path.isfile(init_file):
      logging.warn('%s does not have __init__.py file, generating ...',
                   package_dir)
      with open(init_file, 'w') as f:
        f.write(_INIT_FILE_CONTENT)


def _CamelCase(snake_case):
  return ''.join(x.capitalize() for x in snake_case.split('_'))


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
      version = api_config.get('version', api_version)
      client_classpath = '.'.join([
          '_'.join([api_name, version, 'client']),
          _CamelCase(api_name) + _CamelCase(version)])
      messages_modulepath = '_'.join([api_name, version, 'messages'])
      api_versions_map[api_version] = api_def.APIDef(
          '.'.join([root_package, api_name, api_version]),
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
          request_type = ''.join(
              [s[0].upper() + s[1:]
               for s in re.findall(r'[^\._]+', collection_name)]) + 'GetRequest'
          # Remove api name from collection. It might not match passed in, or
          # even api name in url. We choose to use api name as defined by url.
          collection_name = collection_name.split('.', 1)[1]
          flat_path = get_method.get('flatPath')
          path = get_method.get('path')
          if flat_path == path:
            flat_path = None
          # Normalize base url so it includes api_version.
          url = base_url + path
          url_api_name, _, path = resource_util.SplitDefaultEndpointUrl(url)
          if flat_path:
            _, _, flat_path = resource_util.SplitDefaultEndpointUrl(
                base_url + flat_path)
          # Use url_api_name instead as it is assumed to be source of truth.
          # Also note that api_version not always equal to url_api_version,
          # this is the case where api_version is an alias.
          url = url[:-len(path)]
          collection_info = resource_util.CollectionInfo(
              url_api_name, api_version, url, collection_name,
              request_type, path,
              {_DEFAULT_PATH_NAME: flat_path} if flat_path else {},
              resource_util.GetParamsFromPath(path))
          collections.append(collection_info)
    else:
      subresource_collections = _ExtractResources(
          api_name, api_version, base_url, info)
      collections.extend(subresource_collections)
  return collections


def GenerateResourceModule(base_dir, root_dir, api_config):
  """Create resource.py file for each api with for given api_config.

  Args:
      base_dir: str, Path of directory for the project.
      root_dir: str, Path of the resource file location within the project.
      api_config: regeneration config for all apis.
  Raises:
    WrongDiscoveryDoc: if discovery doc api name/version does not match.
  """
  tpl = template.Template(filename=os.path.join(os.path.dirname(__file__),
                                                'resources.tpl'))

  for api_name, api_version_config in api_config.iteritems():
    for api_version, api_config in api_version_config.iteritems():
      discovery_doc = os.path.join(base_dir, root_dir,
                                   api_config['discovery_doc'])
      with open(discovery_doc, 'rU') as f:
        discovery = json.load(f)
      if discovery['version'] != api_version:
        logging.warn('Discovery api version %s does not match %s, '
                     'this client will be accessible via new alias.',
                     discovery['version'], api_version)
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
      custom_resources = api_config.get('resources', {})
      if custom_resources:
        for collection in resource_collections:
          if collection.name in custom_resources:
            custom_path = custom_resources[collection.name]
            if isinstance(custom_path, dict):
              collection.flat_paths.update(custom_path)
            elif isinstance(custom_path, basestring):
              collection.flat_paths[_DEFAULT_PATH_NAME] = custom_path

      api_dir = os.path.join(base_dir, root_dir, api_name, api_version)
      if not os.path.exists(api_dir):
        os.makedirs(api_dir)
      resource_file_name = os.path.join(api_dir, 'resources.py')
      logging.debug('Generating resource module at %s', resource_file_name)

      if resource_collections:
        with open(resource_file_name, 'wb') as output_file:
          ctx = runtime.Context(output_file,
                                collections=sorted(resource_collections),
                                base_url=resource_collections[0].base_url)
          tpl.render_context(ctx)

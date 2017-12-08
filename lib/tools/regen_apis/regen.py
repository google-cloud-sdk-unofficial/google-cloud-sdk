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

import logging
import os

from apitools.gen import gen_client
from tools.regen_apis import api_def
from mako import runtime
from mako import template


class NoDefaultApiError(Exception):
  """Multiple apis versions are specified but no default is set."""


def GenerateApi(base_dir, root_dir, api_name, api_version, api_config):
  """Invokes apitools generator for given api."""
  discovery_doc = api_config['discovery_doc']

  args = [gen_client.__file__]

  unelidable_request_methods = api_config.get('unelidable_request_methods')
  if unelidable_request_methods:
    args.append('--unelidable_request_methods={0}'.format(
        ','.join(api_config['unelidable_request_methods'])))

  args.extend([
      # TODO(b/25710611) enable empty init files.
      # '--init-file=empty',
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

  with open(api_def.__file__, 'r') as api_def_file:
    api_def_source = api_def_file.read()

  tpl = template.Template(filename=os.path.join(os.path.dirname(__file__),
                                                'template.tpl'))
  api_map_file = os.path.join(base_dir, root_dir, 'apis_map.py')
  logging.debug('Generating api map at %s', api_map_file)
  api_map = _MakeApiMap(root_dir.replace('/', '.'), api_config)
  logging.debug('Creating following api map %s', api_map)
  with open(api_map_file, 'w') as apis_map_file:
    ctx = runtime.Context(apis_map_file,
                          api_def_source=api_def_source,
                          apis_map=api_map)
    tpl.render_context(ctx)



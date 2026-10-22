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
"""Property values and sections container."""

import importlib
import os

from googlecloudsdk.core.properties import parsers
from googlecloudsdk.core.properties.exceptions import NoSuchPropertyError
from googlecloudsdk.core.util import encoding
import six


def IsInternalUserCheck():
  """Checks if the current user is an internal Google user.

  Checks the 'CLOUDSDK_INTERNAL_USER' environment variable first to decide
  whether the current user is an internal Google user.
  If the variable is not set, falls back to checking if the user's email
  domain is 'google.com'.

  Returns:
    bool: True if the user is an internal user, False otherwise.
  """
  if 'CLOUDSDK_INTERNAL_USER' in os.environ:
    return (
        encoding.GetEncodedValue(os.environ, 'CLOUDSDK_INTERNAL_USER') == 'true'
    )
  user_email = VALUES.core.account.Get()
  if user_email:
    parts = user_email.split('@')
    if len(parts) == 2:
      return parts[1] == 'google.com'
  return False


class _Sections(object):
  """Represents the available sections in the properties module."""

  _MAPPING = {
      'access_context_manager': '_SectionAccessContextManager',
      'accessibility': '_SectionAccessibility',
      'ai': '_SectionAi',
      'ai_platform': '_SectionAiPlatform',
      'api_client_overrides': '_SectionApiClientOverrides',
      'api_endpoint_overrides': '_SectionApiEndpointOverrides',
      'app': '_SectionApp',
      'artifacts': '_SectionArtifacts',
      'auth': '_SectionAuth',
      'batch': '_SectionBatch',
      'billing': '_SectionBilling',
      'builds': '_SectionBuilds',
      'code': '_SectionCode',
      'colab': '_SectionColab',
      'component_manager': '_SectionComponentManager',
      'composer': '_SectionComposer',
      'compute': '_SectionCompute',
      'config_delivery': '_SectionConfigDelivery',
      'container': '_SectionContainer',
      'container_attached': '_SectionContainerAttached',
      'container_aws': '_SectionContainerAws',
      'container_azure': '_SectionContainerAzure',
      'container_vmware': '_SectionContainerVmware',
      'container_bare_metal': '_SectionContainerBareMetal',
      'context_aware': '_SectionContextAware',
      'core': '_SectionCore',
      'ssh': '_SectionSsh',
      'scc': '_SectionScc',
      'deploy': '_SectionDeploy',
      'dataproc': '_SectionDataproc',
      'dataflow': '_SectionDataflow',
      'datafusion': '_SectionDatafusion',
      'datapipelines': '_SectionDataPipelines',
      'dataplex': '_SectionDataplex',
      'declarative': '_SectionDeclarative',
      'deployment_manager': '_SectionDeploymentManager',
      'devshell': '_SectionDevshell',
      'diagnostics': '_SectionDiagnostics',
      'edge_container': '_SectionEdgeContainer',
      'emulator': '_SectionEmulator',
      'eventarc': '_SectionEventarc',
      'experimental': '_SectionExperimental',
      'filestore': '_SectionFilestore',
      'functions': '_SectionFunctions',
      'gcloudignore': '_SectionGcloudignore',
      'gkehub': '_SectionGkeHub',
      'grpc': '_SectionGrpc',
      'gkebackup': '_SectionGkebackup',
      'healthcare': '_SectionHealthcare',
      # Bit of a hack here - we add a second mapping as this is the only
      # property section named with hyphens (all the others are consistent about
      # using underscores).
      'inframanager': '_SectionInfraManager',
      'infra-manager': '_SectionInfraManager',
      'interactive': '_SectionInteractive',
      'kuberun': '_SectionKubeRun',
      'lustre': '_SectionLustre',
      'looker': '_SectionLooker',
      'media_asset': '_SectionMediaAsset',
      'memcache': '_SectionMemcache',
      'metastore': '_SectionMetastore',
      'metrics': '_SectionMetrics',
      'ml_engine': '_SectionMlEngine',
      'mps': '_SectionMps',
      'netapp': '_SectionNetapp',
      'notebooks': '_SectionNotebooks',
      'privateca': '_SectionPrivateCa',
      'proxy': '_SectionProxy',
      'pubsub': '_SectionPubsub',
      'recaptcha': '_SectionRecaptcha',
      'redis': '_SectionRedis',
      'regional': '_SectionRegional',
      'resource_policy': '_SectionResourcePolicy',
      'run': '_SectionRun',
      'secrets': '_SectionSecrets',
      'servicehealth': '_SectionServiceHealth',
      'softwaredeliverytrust': '_SectionSoftwareDeliveryTrust',
      'spanner': '_SectionSpanner',
      'storage': '_SectionStorage',
      'survey': '_SectionSurvey',
      'test': '_SectionTest',
      'transfer': '_SectionTransfer',
      'transport': '_SectionTransport',
      'transcoder': '_SectionTranscoder',
      'vector_search': '_SectionVectorSearch',
      'vmware': '_SectionVmware',
      'web3': '_SectionWeb3',
      'workflows': '_SectionWorkflows',
      'workstations': '_SectionWorkstations',
  }

  def __init__(self):
    self.__sections = {}
    self._invocation_stack = parsers.INVOCATION_STACK

  def __getattr__(self, name):
    if name in self._MAPPING:
      cls_name = self._MAPPING[name]
      module_name = 'inframanager' if name == 'infra-manager' else name
      module = importlib.import_module(
          f'googlecloudsdk.core.properties.sections.{module_name}'
      )
      cls = getattr(module, cls_name)
      section = cls()
      self.__sections[section.name] = section
      setattr(self, name, section)
      return section
    raise AttributeError(
        "'_Sections' object has no attribute '{0}'".format(name)
    )

  @property
  def default_section(self):
    return self.core

  def __iter__(self):
    for name in self._MAPPING:
      yield getattr(self, name)

  def PushInvocationValues(self):
    self._invocation_stack.Push()

  def PopInvocationValues(self):
    self._invocation_stack.Pop()

  def SetInvocationValue(self, prop, value, flag):
    self._invocation_stack.SetValue(prop, value, flag)

  def GetLatestInvocationValues(self):
    return self._invocation_stack.GetLatest()

  def GetInvocationStack(self):
    return self._invocation_stack.GetStack()

  def Section(self, section_name):
    if section_name not in self.__sections:
      if section_name in self._MAPPING:
        return getattr(self, section_name)
      raise NoSuchPropertyError(
          'Section "{section}" does not exist.'.format(section=section_name)
      )
    return self.__sections[section_name]

  def AllSections(self, include_hidden=False):
    for name in self._MAPPING:
      getattr(self, name)
    return [
        name
        for name, value in six.iteritems(self.__sections)
        if not value.is_hidden or include_hidden
    ]

  def AllValues(
      self,
      list_unset=False,
      include_hidden=False,
      properties_file=None,
      only_file_contents=False,
  ):
    """Gets the entire collection of property values for all sections.

    Args:
      list_unset: bool, If True, include unset properties in the result.
      include_hidden: bool, True to include hidden properties in the result. If
        a property has a value set but is hidden, it will be included regardless
        of this setting.
      properties_file: PropertyFile, the file to read settings from.  If None
        the active property file will be used.
      only_file_contents: bool, True if values should be taken only from the
        properties file, false if flags, env vars, etc. should be consulted too.
        Mostly useful for listing file contents.

    Returns:
      {str:{str:str}}, A dict of sections to dicts of properties to values.
    """
    result = {}
    for section in self:
      section_result = section.AllValues(
          list_unset=list_unset,
          include_hidden=include_hidden,
          properties_file=properties_file,
          only_file_contents=only_file_contents,
      )
      if section_result:
        result[section.name] = section_result
    return result

  def AllPropertyValues(
      self,
      list_unset=False,
      include_hidden=False,
      properties_file=None,
      only_file_contents=False,
  ):
    """Gets the entire collection of property values for all sections.

    Args:
      list_unset: bool, If True, include unset properties in the result.
      include_hidden: bool, True to include hidden properties in the result. If
        a property has a value set but is hidden, it will be included regardless
        of this setting.
      properties_file: PropertyFile, the file to read settings from.  If None
        the active property file will be used.
      only_file_contents: bool, True if values should be taken only from the
        properties file, false if flags, env vars, etc. should be consulted too.
        Mostly useful for listing file contents.

    Returns:
      {str:{str:PropertyValue}}, A dict of sections to dicts of properties to
        property values.
    """
    result = {}
    for section in self:
      section_result = section.AllPropertyValues(
          list_unset=list_unset,
          include_hidden=include_hidden,
          properties_file=properties_file,
          only_file_contents=only_file_contents,
      )
      if section_result:
        result[section.name] = section_result
    return result

  def GetHelpString(self):
    """Gets a string with the help contents for all properties and descriptions.

    Returns:
      str, The string for the man page section.
    """
    messages = []
    # Force load all sections to ensure they are listed in the help string.
    for name in self._MAPPING:
      getattr(self, name)

    sections_list = [self.default_section]
    default_section_name = self.default_section.name
    sections_list.extend(
        sorted([
            s
            for name, s in six.iteritems(self.__sections)
            if name != default_section_name and not s.is_hidden
        ])
    )
    for section in sections_list:
      props = sorted([p for p in section if not p.is_hidden])
      if not props:
        continue
      messages.append('_{section}_::'.format(section=section.name))
      for prop in props:
        messages.append(
            '*{prop}*:::\n\n{text}'.format(prop=prop.name, text=prop.help_text)
        )
    return '\n\n\n'.join(messages)


VALUES = _Sections()


def FromString(property_string):
  """Gets the property object corresponding the given string.

  Args:
    property_string: str, The string to parse.  It can be in the format
      section/property, or just property if the section is the default one.

  Returns:
    properties.Property, The property or None if it failed to parse to a valid
      property.
  """
  section, prop = ParsePropertyString(property_string)
  if not prop:
    return None
  return VALUES.Section(section).Property(prop)


def ParsePropertyString(property_string):
  """Parses a string into a section and property name.

  Args:
    property_string: str, The property string in the format section/property.

  Returns:
    (str, str), The section and property.  Both will be none if the input
    string is empty.  Property can be None if the string ends with a slash.
  """
  if not property_string:
    return None, None

  if '/' in property_string:
    section, prop = tuple(property_string.split('/', 1))
  else:
    section = None
    prop = property_string

  section = section or VALUES.default_section.name
  prop = prop or None
  return section, prop

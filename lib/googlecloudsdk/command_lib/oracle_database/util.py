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

"""Common utilities for Oracle Database commands."""


from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.core.resource import resource_expr_rewrite


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='The Cloud location for the {resource}.')


def GetLocationResourceSpec(resource_name='location'):
  return concepts.ResourceSpec(
      'oracledatabase.projects.locations',
      resource_name=resource_name,
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=True)


class GcloudFilterBackend(resource_expr_rewrite.Backend):
  """The expression rewrite backend for Database."""

  def __init__(self, server_filter_fields):
    super(GcloudFilterBackend, self).__init__()
    # server_filter_fields can be a list or a dict.
    # If it's a dict, it maps client-side field name to server-side field name.
    if isinstance(server_filter_fields, list):
      self._server_filter_fields = {k: k for k in server_filter_fields}
    else:
      self._server_filter_fields = server_filter_fields

  def RewriteTerm(self, key, op, operand, key_type):
    """Rewrites <key op operand> to <key op operand quoted> if key is supported."""
    del key_type  # unused in RewriteTerm
    if key in self._server_filter_fields:
      server_key = self._server_filter_fields[key]
      if op == '=':
        return server_key + op + self.Quote(operand, always=True)
    return None


class MatchAnything(object):
  """A helper class that matches any equality comparison."""

  def __eq__(self, other):
    return True

  def __ne__(self, other):
    return False

  def __lt__(self, other):
    return True

  def __le__(self, other):
    return True

  def __gt__(self, other):
    return True

  def __ge__(self, other):
    return True

  def __str__(self):
    return 'MatchAnything'

  def __bool__(self):
    return True

  def __nonzero__(self):
    return True


class ResourceWrapper(object):
  """A wrapper that adds extra fields to a resource for filtering."""

  def __init__(self, resource, extra_fields):
    self._resource = resource
    self._extra_fields = extra_fields

  def __getattr__(self, name):
    if name in self._extra_fields:
      return self._extra_fields[name]
    return getattr(self._resource, name)

  def __getitem__(self, name):
    # Support dict-like access if the original resource supports it.
    if hasattr(self._resource, '__getitem__'):
      try:
        return self._resource[name]
      except (KeyError, TypeError):
        pass
    if name in self._extra_fields:
      return self._extra_fields[name]
    raise KeyError(name)

  def __contains__(self, name):
    return name in self._extra_fields or hasattr(self._resource, name)

  def __iter__(self):
    if hasattr(self._resource, '__iter__'):
      return iter(self._resource)
    return iter([])

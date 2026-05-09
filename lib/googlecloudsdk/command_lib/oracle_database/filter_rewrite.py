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
"""Oracle Database resource filter expression rewrite backend."""


from googlecloudsdk.core.resource import resource_expr_rewrite


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


class GiVersionBackend(resource_expr_rewrite.Backend):
  """GiVersion resource filter expression rewrite backend."""

  def RewriteTerm(self, key, op, operand, key_type):
    """Rewrites <key op operand>."""
    del key_type  # unused in RewriteTerm

    if op not in ['=', '!=', ':', '<', '<=', '>', '>=']:
      return None

    if key in ['shape', 'gcp_oracle_zone', 'gi_version']:
      return '{key}{op}{operand}'.format(
          key=key, op=op, operand=self.Quote(operand, always=True))
    return None

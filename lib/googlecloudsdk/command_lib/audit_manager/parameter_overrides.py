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
"""Helpers for the `--parameter-overrides` flag of Audit Manager commands."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import arg_parsers_usage_text
from googlecloudsdk.core import yaml

# `ParamValue.oneofValue` is a `Parameter`, so the message is cyclic. ArgObject
# needs a finite spec, so nested `oneofValue` is accepted up to this depth.
_MAX_ONEOF_DEPTH = 3


def _Object(help_text, spec=None, value_type=None, repeated=False, hidden=None):
  """Returns a nested ArgObject for one field of the overrides schema."""
  return arg_parsers.ArgObject(
      spec=spec,
      value_type=value_type,
      help_text=help_text,
      repeated=repeated,
      hidden=hidden,
  )


def _ParamValueSpec(depth):
  """Returns the ArgObject spec for a `ParamValue` at the given nesting depth."""
  spec = {
      'stringValue': _Object('A string value.', value_type=str),
      'boolValue': _Object('A boolean value.', value_type=bool),
      'numberValue': _Object('A numeric value.', value_type=float),
      'stringListValue': _Object(
          'A list of strings.',
          spec={
              'values': _Object(
                  'The strings in the list.', value_type=str, repeated=True
              )
          },
      ),
  }
  if depth < _MAX_ONEOF_DEPTH:
    spec['oneofValue'] = _Object(
        'The selected sub-parameter of a `oneOf` parameter, with its own'
        ' `name` and `parameterValue`. Can be nested up to {} levels.'.format(
            _MAX_ONEOF_DEPTH
        ),
        spec=_ParameterSpec(depth + 1),
        # Document one level only; deeper levels are still parsed.
        hidden=True if depth > 0 else None,
    )
  return spec


def _ParameterSpec(depth):
  """Returns the ArgObject spec for a `Parameter` at the given nesting depth."""
  return {
      'name': _Object('Name of the parameter.', value_type=str),
      'parameterValue': _Object(
          'Value of the parameter. Set exactly one of the following fields.',
          spec=_ParamValueSpec(depth),
      ),
  }


class _NonEmptyMapType(arg_parsers_usage_text.DefaultArgTypeWrapper):
  """Rejects an empty map while keeping the wrapped ArgObject's help text."""

  def __call__(self, arg_value):
    try:
      value = self.arg_type(arg_value)
    except arg_parsers.ArgumentTypeError:
      raise
    except (TypeError, ValueError, yaml.Error) as e:
      raise arg_parsers.ArgumentTypeError(
          'Expected a JSON or YAML object, or a path to a .json or .yaml'
          ' file: {}'.format(e)
      ) from e
    if not value:
      raise arg_parsers.ArgumentTypeError(
          'Must be a non-empty map of cloud control resource names to'
          ' parameter overrides.'
      )
    return value


def ParameterOverridesType():
  """Returns an ArgObject type that parses `--parameter-overrides`.

  The type accepts inline JSON/YAML or a path to a `.json`/`.yaml` file, rejects
  unknown keys and empty maps, and returns a dict in the shape of the API's
  `parameterOverrides` map, ready for `encoding.DictToMessage`.
  """
  return _NonEmptyMapType(
      arg_parsers.ArgObject(
          key_type=_Object(
              'Full resource name of the cloud control, for example'
              ' `organizations/123/locations/global/cloudControls/my-control`,'
              ' as returned by `gcloud compliance-manager cloud-controls'
              ' list`.',
              value_type=str,
          ),
          value_type=_Object(
              'Parameter overrides for the cloud control.',
              spec={
                  'parameters': _Object(
                      'Parameters to override.',
                      spec=_ParameterSpec(0),
                      repeated=True,
                  )
              },
          ),
          help_text=(
              'Map from cloud control resource name to the overrides for that'
              ' cloud control.'
          ),
      )
  )

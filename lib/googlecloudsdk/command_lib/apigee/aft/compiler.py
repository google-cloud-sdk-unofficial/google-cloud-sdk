# -*- coding: utf-8 -*- # Lint as: python3
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
"""Compiles an Apigee template into a Proxy."""

import copy
from typing import Any, Dict, List, TypeVar, Callable, Optional, Union
from googlecloudsdk.command_lib.apigee.aft import models


_TypeToRewrite = TypeVar("_TypeToRewrite")
_FieldPath = List[Union[str, int]]


def _rewritten(
    dicted_data: Any,
    type_to_rewrite: type[_TypeToRewrite],
    rewriter: Callable[[_FieldPath, _TypeToRewrite], _TypeToRewrite],
    ancestor_path: Optional[_FieldPath] = None,
) -> Any:
  """Returns a copy of the given data structure with rewritten values.

  Args:
    dicted_data: The data to rewrite. If a Dict-like or List-like object, it
      will be traversed. Otherwise, it will be either rewritten (if of type
      type_to_rewrite) or copied as-is (if not of type type_to_rewrite).
    type_to_rewrite: The type to rewrite.
    rewriter: Called on each value of type type_to_rewrite with the value's
      full path within dicted_data; its return value will replace the original
      value.
    ancestor_path: If dicted_data is a nested object, this is the path to
      it from the top of the data structure.

  Returns:
    A copy of dicted_data with the specified values rewritten.
  """
  path: _FieldPath = ancestor_path or []
  if isinstance(dicted_data, type_to_rewrite):
    return rewriter(path, dicted_data)

  if isinstance(dicted_data, dict):
    rewritten = {}
    for key in dicted_data:
      value = dicted_data[key]
      child_path = path + [key]
      rewritten[key] = _rewritten(value, type_to_rewrite, rewriter, child_path)
    return rewritten

  if isinstance(dicted_data, list):
    return [
        _rewritten(e, type_to_rewrite, rewriter, path + [idx])
        for idx, e in enumerate(dicted_data)
    ]

  return copy.deepcopy(dicted_data)


def _make_replacer(
    needle: str, replacement: str
) -> Callable[[_FieldPath, str], str]:
  """Returns a function that replaces a string with another string.

  Args:
    needle: The string to replace.
    replacement: The string to replace it with.

  Returns:
    A function that takes a string and returns a copy of it where all
    occurrences of needle are replaced with replacement.
  """
  return lambda fp, x: x.replace(needle, replacement)


class ApigeeCompiler:
  """Compiles an Apigee template into a Proxy."""

  def compile(
      self,
      template: models.Template,
      features: List[models.Feature],
      parameters: Optional[Dict[str, str]] = None,
  ) -> models.Proxy:
    """Compiles an Apigee template into a Proxy.

    Args:
      template: The Apigee template to compile.
      features: The list of Apigee features to use. It's the caller's
        responsibility to look up the appropriate feature files referenced by
        the template's template.features field.
      parameters: The list of parameters to use.

    Returns:
      The compiled Apigee Proxy.
    """
    if parameters is None:
      parameters = {}

    # Convert template to dict for easier manipulation
    template_dict = models.to_dict(template)

    # Validate the required top-level schema fields (missing-first) before
    # composing. `template_dict` is camelCase, so read the camelCase keys with
    # a default so a missing field is reported cleanly by the validator rather
    # than raising a KeyError.
    models.validate_gateway(template_dict.get("gateway", ""))
    models.validate_schema_version(template_dict.get("schemaVersion", ""))

    proxy_dict = {
        # gateway/schemaVersion are authoring metadata carried onto the
        # compiled Proxy. compile() rebuilds the Proxy from proxy_dict via
        # models.from_dict below, so these keys are read back (and re-validated
        # by Proxy.__post_init__). They are dropped from the emitted bundle.
        "gateway": template_dict.get("gateway", ""),
        "schemaVersion": template_dict.get("schemaVersion", ""),
        "name": template_dict["name"],
        "description": template_dict["description"],
        "parameters": template_dict["parameters"],
        "priority": template_dict.get("priority"),
        "tests": template_dict.get("tests"),
        "endpoints": copy.deepcopy(template_dict.get("endpoints", [])),
        "policies": copy.deepcopy(template_dict.get("policies", [])),
        "targets": copy.deepcopy(template_dict.get("targets", [])),
        "resources": copy.deepcopy(template_dict.get("resources", [])),
    }

    proxy_dict = self.proxy_apply_features(proxy_dict, features, parameters)

    # Convert back to Proxy dataclass.
    return models.from_dict(models.Proxy, proxy_dict)

  def proxy_apply_features(
      self,
      proxy_dict: Dict[str, Any],
      features: List[models.Feature],
      parameters: Optional[Dict[str, str]] = None,
  ) -> Dict[str, Any]:
    """Applies features to a proxy dictionary in priority order."""
    if parameters is None:
      parameters = {}

    # Sort features by priority
    features = sorted(features, key=(
        lambda x: x.priority if x.priority is not None else 100
    ))

    # First apply features with targets & endpoints
    for feature in features:
      if feature.endpoints or feature.targets:
        proxy_dict = self.proxy_apply_feature(proxy_dict, feature, parameters)

    # Now apply features with just policies
    for feature in features:
      if not feature.endpoints and not feature.targets:
        proxy_dict = self.proxy_apply_feature(proxy_dict, feature, parameters)

    return proxy_dict

  def proxy_apply_feature(
      self,
      proxy_dict: Dict[str, Any],
      feature: models.Feature,
      parameters: Optional[Dict[str, str]] = None,
  ) -> Dict[str, Any]:
    """Applies a single feature to a proxy dictionary."""
    if parameters is None:
      parameters = {}

    feature_dict = models.to_dict(feature)

    # Replace parameters in feature
    feature_dict = self.feature_replace_parameters(
        feature_dict, proxy_dict["parameters"], parameters
    )

    # Namespace policies and resources. Use UID if available, otherwise just
    # the feature name.
    prefix = feature_dict.get("uid") or feature_dict["name"]

    namespaced_policy_names = {}
    for policy in feature_dict.get("policies", []):
      original_name = policy["name"]
      new_name = f"{prefix}-{original_name}"
      namespaced_policy_names[original_name] = new_name

    def policy_namespacer(fp: _FieldPath, x: str) -> str:
      if fp and fp[-1] == "name" and x in namespaced_policy_names:
        return namespaced_policy_names[x]
      if x.endswith(".") and x[:-1] in namespaced_policy_names:
        return namespaced_policy_names[x[:-1]] + "."
      return x

    feature_dict = _rewritten(feature_dict, str, policy_namespacer)

    namespaced_resource_names = {}
    namespaced_resource_references = {}
    for resource in feature_dict.get("resources", []):
      original_name = resource["name"]
      new_name = f"{prefix}-{original_name}"
      namespaced_resource_names[original_name] = new_name
      if original_name.endswith(".properties"):
        prop_name = original_name.replace(".properties", "")
        new_prop_name = new_name.replace(".properties", "")
        namespaced_resource_references[f"propertyset.{prop_name}."] = (
            f"propertyset.{new_prop_name}."
        )
      else:
        namespaced_resource_references[f"://{original_name}"] = (
            f"://{new_name}"
        )

    def resource_namespacer(fp: _FieldPath, x: str) -> str:
      if fp and fp[-1] == "name" and x in namespaced_resource_names:
        return namespaced_resource_names[x]
      for old_ref, new_ref in namespaced_resource_references.items():
        x = x.replace(old_ref, new_ref)
      return x

    feature_dict = _rewritten(feature_dict, str, resource_namespacer)

    # Merge flows
    # In TS, it merged defaultEndpoint flows into all proxy endpoints.
    if feature_dict.get("defaultEndpoint"):
      for endpoint in proxy_dict["endpoints"]:
        for feature_flow in feature_dict["defaultEndpoint"].get("flows", []):
          for proxy_flow in endpoint.get("flows", []):
            if (
                proxy_flow.get("name") == feature_flow.get("name")
                and proxy_flow.get("mode") == feature_flow.get("mode")
                and proxy_flow.get("condition") == feature_flow.get("condition")
            ):
              proxy_flow["steps"].extend(feature_flow.get("steps", []))
              break
          else:  # no matching flow was found
            if "flows" not in endpoint:
              endpoint["flows"] = []
            endpoint["flows"].append(copy.deepcopy(feature_flow))

        if feature_dict["defaultEndpoint"].get("defaultFaultRule"):
          if endpoint.get("defaultFaultRule"):
            endpoint["defaultFaultRule"]["steps"].extend(
                feature_dict["defaultEndpoint"]["defaultFaultRule"].get(
                    "steps", []
                )
            )
          else:
            endpoint["defaultFaultRule"] = copy.deepcopy(
                feature_dict["defaultEndpoint"]["defaultFaultRule"]
            )

    # Non-default endpoints and targets
    if "endpoints" in feature_dict and feature_dict["endpoints"]:
      existing_endpoints = {
          endpoint["name"]: idx
          for idx, endpoint in enumerate(proxy_dict["endpoints"])
          if "name" in endpoint
      }
      for endpoint in feature_dict["endpoints"]:
        if endpoint["name"] in existing_endpoints:
          # Replace existing endpoint with the feature endpoint
          idx = existing_endpoints[endpoint["name"]]
          proxy_dict["endpoints"][idx] = endpoint
        else:
          if "name" in endpoint:
            existing_endpoints[endpoint["name"]] = len(proxy_dict["endpoints"])
          proxy_dict["endpoints"].append(endpoint)

    if "targets" in feature_dict and feature_dict["targets"]:
      existing_targets = {
          target["name"]: idx
          for idx, target in enumerate(proxy_dict["targets"])
          if "name" in target
      }
      for target in feature_dict["targets"]:
        if target["name"] in existing_targets:
          # Replace existing target with the feature target
          idx = existing_targets[target["name"]]
          proxy_dict["targets"][idx] = target
        else:
          if "name" in target:
            existing_targets[target["name"]] = len(proxy_dict["targets"])
          proxy_dict["targets"].append(target)

    # Append policies and resources
    if feature_dict.get("policies"):
      proxy_dict["policies"].extend(feature_dict["policies"])
    if feature_dict.get("resources"):
      proxy_dict["resources"].extend(feature_dict["resources"])

    return proxy_dict

  def feature_replace_parameters(
      self,
      feature_dict: Dict[str, Any],
      proxy_parameters: List[Dict[str, Any]],
      parameters: Dict[str, str],
  ) -> Dict[str, Any]:
    """Applies parameters to a feature dictionary."""
    rewritten_feature = copy.deepcopy(feature_dict)

    for parameter in feature_dict.get("parameters", []):
      param_value = parameter.get("default", "")
      param_name = parameter.get("name", "")
      uid = feature_dict.get("uid")
      proxy_param_key = (
          f"{feature_dict['name']}.{uid}.{param_name}" if uid else param_name
      )

      # Find in proxy parameters
      proxy_param = next(
          (p for p in proxy_parameters if p["name"] == proxy_param_key), None
      )
      if proxy_param and proxy_param.get("default"):
        param_value = proxy_param["default"]

      if proxy_param_key in parameters:
        param_value = parameters[proxy_param_key]
      elif param_name in parameters:
        param_value = parameters[param_name]

      if parameter.get("maps") and param_value in parameter["maps"]:
        param_value = parameter["maps"][param_value]

      if parameter.get("paths"):
        # This is a JSONPath parameter. The intended behavior for such
        # parameters is to rewrite the values in the feature that are specified
        # specified by the JSONPath expressions.
        #
        # However, the Google Cloud SDK includes no Python library for JSONPath,
        # so such parameters won't be supported until feature processing is
        # moved to the server side.
        error_msg = (
            f"Parameter {param_name} uses JSONPath, which is not yet supported."
        )
        raise NotImplementedError(error_msg)
      else:
        # When JSONPath is not used, the parameter is applied by simple string
        # replacement: all strings in the feature that contain {param_name} have
        # that macro replaced with param_value.
        replace_key = "{" + param_name + "}"
        rewriter = _make_replacer(replace_key, param_value)
        rewritten_feature = _rewritten(rewritten_feature, str, rewriter)

    return rewritten_feature

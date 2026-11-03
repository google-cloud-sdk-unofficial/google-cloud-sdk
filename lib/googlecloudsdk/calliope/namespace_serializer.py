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

"""Utilities for serializing parsed command namespace and concept data for parity verification."""

import datetime
import functools
import json
import os
import sys

from googlecloudsdk.core import properties
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files

_IGNORED_ARG_KEYS = frozenset({
    "calliope_command",
    "command_path",
    "CONCEPTS",
    "CONCEPT_ARGS",
})

_TYPE_NAME_NORMALIZERS = {}


def RegisterTypeNameNormalizer(type_name):
  """Decorator to register a normalizer function for a type name string."""

  def _Decorator(func):
    _TYPE_NAME_NORMALIZERS[type_name] = func
    return func

  return _Decorator


def _GetFullTypeName(obj):
  cls = type(obj)
  module = getattr(cls, "__module__", "")
  qualname = getattr(cls, "__qualname__", cls.__name__)
  if module and module != "builtins":
    return "{}.{}".format(module, qualname)
  return qualname


@functools.singledispatch
def NormalizeValue(obj):
  """Normalizes an arbitrary Python value into a JSON-serializable primitive."""
  full_name = _GetFullTypeName(obj)
  if full_name in _TYPE_NAME_NORMALIZERS:
    return _TYPE_NAME_NORMALIZERS[full_name](obj)
  if hasattr(obj, "RelativeName") and callable(obj.RelativeName):
    try:
      return obj.RelativeName()
    except Exception:  # pylint: disable=broad-exception-caught
      pass
  try:
    return str(obj)
  except Exception:  # pylint: disable=broad-exception-caught
    return "<unserializable>"


@RegisterTypeNameNormalizer("googlecloudsdk.calliope.arg_parsers.HostPort")
def _NormalizeHostPort(obj):
  host = getattr(obj, "host", None)
  port = getattr(obj, "port", None)
  if host is not None and port is not None:
    return "{}:{}".format(host, port)
  if host is not None:
    return str(host)
  if port is not None:
    return ":{}".format(port)
  return ""


@RegisterTypeNameNormalizer("re.Pattern")
def _NormalizePattern(obj):
  return obj.pattern


@NormalizeValue.register(str)
@NormalizeValue.register(int)
@NormalizeValue.register(float)
@NormalizeValue.register(bool)
@NormalizeValue.register(type(None))
def _(obj):
  return obj


@NormalizeValue.register(dict)
def _(obj):
  return {str(k): NormalizeValue(v) for k, v in obj.items()}


@NormalizeValue.register(list)
@NormalizeValue.register(tuple)
def _(obj):
  return [NormalizeValue(v) for v in obj]


@NormalizeValue.register(set)
@NormalizeValue.register(frozenset)
def _(obj):
  items = [NormalizeValue(v) for v in obj]
  try:
    return sorted(items)
  except TypeError:
    return sorted(items, key=str)


@NormalizeValue.register(datetime.datetime)
def _(obj):
  return obj.isoformat()


@NormalizeValue.register(datetime.timedelta)
def _(obj):
  return obj.total_seconds()


def NormalizeArgs(args):
  """Extracts and normalizes non-private argument values from a Namespace or dict."""
  if isinstance(args, dict):
    raw = args
  elif hasattr(args, "__dict__"):
    raw = vars(args)
  else:
    return {}
  return {
      k: NormalizeValue(v)
      for k, v in raw.items()
      if not k.startswith("_") and k not in _IGNORED_ARG_KEYS
  }


def _IsEmpty(val):
  """Returns True if val is None or an empty string, sequence, or mapping."""
  if val is None:
    return True
  if isinstance(val, (str, list, tuple, dict)) and not val:
    return True
  return False


def _IsMissingValueIgnored(val, ignore_empty):
  return _IsEmpty(val) if ignore_empty else val is None


def _FindMatchingKey(k, target_dict):
  """Finds the corresponding key for k in target_dict, if present."""
  if k in target_dict:
    return k
  stripped = k.rstrip("_")
  if stripped in target_dict:
    return stripped
  with_underscore = "{}_".format(k)
  if with_underscore in target_dict:
    return with_underscore
  alt_sep = k.replace("-", "_") if "-" in k else k.replace("_", "-")
  if alt_sep in target_dict:
    return alt_sep
  return None


def CompareArgs(py_args, go_args, ignore_empty=False):
  """Compares normalized argument mappings from Python and Go.

  Args:
    py_args: An argparse.Namespace or dict of Python argument values.
    go_args: An argparse.Namespace or dict of Go argument values.
    ignore_empty: If True, treats None and empty containers ("", [], {}) as
      equivalent.

  Returns:
    dict[str, dict[str, Any]]: Mapping of mismatched argument keys to
    {'expected': py_val, 'actual': go_val, 'status':
    'mismatch'|'missing_in_go'|'missing_in_py'}.
  """
  norm_py = NormalizeArgs(py_args)
  norm_go = NormalizeArgs(go_args)
  mismatches = {}

  for k, py_val in norm_py.items():
    go_key = _FindMatchingKey(k, norm_go)
    if go_key is None:
      if not _IsMissingValueIgnored(py_val, ignore_empty):
        mismatches[k] = {
            "expected": py_val,
            "actual": None,
            "status": "missing_in_go",
        }
      continue

    go_val = norm_go[go_key]
    if ignore_empty and _IsEmpty(py_val) and _IsEmpty(go_val):
      continue
    if type(py_val) is not type(go_val) or py_val != go_val:
      mismatches[k] = {
          "expected": py_val,
          "actual": go_val,
          "status": "mismatch",
      }

  for k, go_val in norm_go.items():
    if _FindMatchingKey(k, norm_py) is not None:
      continue
    if not _IsMissingValueIgnored(go_val, ignore_empty):
      mismatches[k] = {
          "expected": None,
          "actual": go_val,
          "status": "missing_in_py",
      }

  return mismatches


def CompareNamespaces(
    py_ns,
    go_ns,
    ignore_empty=False,
    check_concepts=False,
):
  """Compares Python and Go namespace dumps and returns human-readable mismatch strings."""
  mismatches = []
  py_args = (
      py_ns.get("args", py_ns)
      if isinstance(py_ns, dict) and isinstance(py_ns.get("args", py_ns), dict)
      else py_ns
  )
  go_args = (
      go_ns.get("args", go_ns)
      if isinstance(go_ns, dict) and isinstance(go_ns.get("args", go_ns), dict)
      else go_ns
  )

  for k, diff in CompareArgs(
      py_args, go_args, ignore_empty=ignore_empty
  ).items():
    status = diff.get("status")
    py_val = diff["expected"]
    go_val = diff["actual"]
    if status == "missing_in_go":
      mismatches.append(
          "Key '{}' in Py ({}) but missing in Go".format(k, py_val)
      )
    elif status == "missing_in_py":
      mismatches.append(
          "Key '{}' in Go ({}) but missing in Py".format(k, go_val)
      )
    else:
      mismatches.append(
          "Key '{}' mismatch: Py ({!r} / {}) != Go ({!r} / {})".format(
              k, py_val, type(py_val), go_val, type(go_val)
          )
      )

  if (
      not check_concepts
      or not isinstance(py_ns, dict)
      or not isinstance(go_ns, dict)
  ):
    return mismatches
  if "concepts" not in py_ns and "concepts" not in go_ns:
    return mismatches

  py_concepts = py_ns.get("concepts", {})
  go_concepts = go_ns.get("concepts", {})
  if not isinstance(py_concepts, dict) or not isinstance(go_concepts, dict):
    return mismatches

  for ck, py_cval in py_concepts.items():
    if ck not in go_concepts:
      mismatches.append(
          "Concept '{}' in Py ({!r}) but missing in Go".format(ck, py_cval)
      )
    elif go_concepts[ck] != py_cval:
      mismatches.append(
          "Concept '{}' mismatch: Py ({!r}) != Go ({!r})".format(
              ck, py_cval, go_concepts[ck]
          )
      )
  for ck, go_cval in go_concepts.items():
    if ck not in py_concepts:
      mismatches.append(
          "Concept '{}' in Go ({!r}) but missing in Py".format(ck, go_cval)
      )

  return mismatches


class NamespaceEncoder(json.JSONEncoder):
  """JSON encoder that cleanly converts sets and un-serializable objects."""

  def default(self, o):
    return NormalizeValue(o)


def GetConceptsDict(args, calliope_command):
  """Extracts parsed concept relative names or string representations from command arguments."""
  concepts_dict = {}
  if getattr(args, "CONCEPTS", None) is not None:
    try:
      for attr in dir(args.CONCEPTS):
        if attr.startswith("_") or attr in ("Reset", "ArgNames"):
          continue
        parser = getattr(args.CONCEPTS, attr, None)
        if hasattr(parser, "Parse"):
          try:
            parsed = parser.Parse()
            if parsed is not None:
              concepts_dict[attr] = (
                  parsed.RelativeName()
                  if hasattr(parsed, "RelativeName")
                  else str(parsed)
              )
          except Exception:  # pylint: disable=broad-exception-caught
            pass
    except Exception:  # pylint: disable=broad-exception-caught
      pass
  if getattr(args, "CONCEPT_ARGS", None) is not None:
    concept_parser = args.CONCEPT_ARGS
    for attr_name in getattr(concept_parser, "_attributes", {}):
      try:
        val = getattr(args, attr_name, None)
        if val is not None:
          concepts_dict[attr_name] = (
              val.RelativeName() if hasattr(val, "RelativeName") else str(val)
          )
      except Exception:  # pylint: disable=broad-exception-caught
        pass
  try:
    handler = getattr(
        getattr(calliope_command, "ai", None), "concept_handler", None
    )
    if handler and hasattr(handler, "_all_concepts"):
      for c_details in handler._all_concepts:  # pylint: disable=protected-access
        name = c_details.get("name")
        c_info = c_details.get("concept_info")
        if name and name not in concepts_dict:
          parsed = None
          lazy_parse = getattr(handler, name, None)
          if lazy_parse and hasattr(lazy_parse, "Parse"):
            try:
              parsed = lazy_parse.Parse()
            except Exception:  # pylint: disable=broad-exception-caught
              parsed = None
          if parsed is None and c_info and hasattr(c_info, "Parse"):
            try:
              parsed = c_info.Parse(args)
            except TypeError:
              try:
                parsed = c_info.Parse(
                    getattr(c_info, "attribute_to_args_map", {}),
                    getattr(c_info, "base_fallthroughs_map", {}),
                    parsed_args=args,
                )
              except Exception:  # pylint: disable=broad-exception-caught
                parsed = None
            except Exception:  # pylint: disable=broad-exception-caught
              parsed = None
          if parsed is not None:
            concepts_dict[name] = (
                parsed.RelativeName()
                if hasattr(parsed, "RelativeName")
                else str(parsed)
            )
  except Exception:  # pylint: disable=broad-exception-caught
    pass
  return concepts_dict


def DumpNamespaceDict(args, calliope_command):
  """Builds and returns the 3-tier dictionary containing args, concepts, and properties."""
  return {
      "args": NormalizeArgs(args),
      "concepts": GetConceptsDict(args, calliope_command),
      "properties": properties.VALUES.AllValues(list_unset=False),
  }


def HandleNamespaceSerialization(args, calliope_command):
  """Checks environment variables and dumps structured namespace JSON if requested.

  Args:
    args: The argparse.Namespace holding parsed CLI arguments.
    calliope_command: The calliope._Command instance being executed.

  Returns:
    bool: True if namespace serialization was requested and handled, False
    otherwise.
  """
  dump_to_path = encoding.GetEncodedValue(
      os.environ, "GCLOUD_DUMP_NAMESPACE_TO"
  )
  dump_to_stdout = (
      encoding.GetEncodedValue(os.environ, "PARITY_DUMP_NAMESPACE") == "1"
  )
  if not dump_to_path and not dump_to_stdout:
    return False

  should_exit = (
      dump_to_stdout
      or encoding.GetEncodedValue(os.environ, "GCLOUD_EXIT_AFTER_DUMP") == "1"
  )

  try:
    dump_dict = DumpNamespaceDict(args, calliope_command)
    if dump_to_path:
      with files.FileWriter(dump_to_path, create_path=True) as f:
        json.dump(dump_dict, f, cls=NamespaceEncoder, indent=2, sort_keys=True)
    if dump_to_stdout:
      sys.stdout.write(
          json.dumps(dump_dict, cls=NamespaceEncoder, sort_keys=True) + "\n"
      )
      sys.stdout.flush()
  except Exception as e:  # pylint: disable=broad-exception-caught
    sys.stderr.write("Failed to dump namespace: {}\n".format(e))
    sys.stderr.flush()
    if should_exit:
      sys.exit(1)
    raise

  if should_exit:
    sys.exit(0)
  return True

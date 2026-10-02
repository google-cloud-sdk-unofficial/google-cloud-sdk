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

import json
import os
import sys

from googlecloudsdk.core import properties
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files


class NamespaceEncoder(json.JSONEncoder):
  """JSON encoder that cleanly converts sets and un-serializable objects."""

  def default(self, o):
    if isinstance(o, (set, frozenset)):
      try:
        return sorted(o)
      except TypeError:
        return sorted(o, key=str)
    if hasattr(o, "RelativeName") and callable(o.RelativeName):
      try:
        return o.RelativeName()
      except Exception:  # pylint: disable=broad-exception-caught
        pass
    try:
      return json.JSONEncoder.default(self, o)
    except TypeError:
      try:
        return str(o)
      except Exception:  # pylint: disable=broad-exception-caught
        return "<unserializable>"


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
      "args": {
          k: v
          for k, v in vars(args).items()
          if not k.startswith("_")
          and k != "calliope_command"
          and k not in ("CONCEPTS", "CONCEPT_ARGS")
      },
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

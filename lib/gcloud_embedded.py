# Lint as: python3
# -*- coding: utf-8 -*- #
#
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

"""Embedded entrypoint for gcloud, handling sys.exit() gracefully.

Workaround for Py_BytesMain exit issue.
Py_BytesMain calls exit() instead of returning when sys.exit() is called in
Python.
See https://github.com/python/cpython/pull/153446

TODO(b/534428647): Delete this file entirely once upstream fix is in bundled
python, and revert to using gcloud.py directly.
"""

import ctypes
import os
import sys
import traceback

import gcloud
from googlecloudsdk.core.util import encoding


def main():
  """Main entry point for embedded execution."""
  exit_code = 0
  try:
    gcloud.main()
  except SystemExit as e:
    if isinstance(e.code, int):
      exit_code = e.code
    elif e.code is None:
      exit_code = 0
    else:
      sys.stderr.write(str(e.code) + '\n')
      exit_code = 1
  except KeyboardInterrupt:
    exit_code = 130
  except BaseException:  # pylint: disable=broad-except
    traceback.print_exc(file=sys.stderr)
    exit_code = 1

  # Write exit code to Go memory if pointer is provided.
  ptr_env = encoding.GetEncodedValue(os.environ, 'GOCLOUD_EXIT_CODE_PTR')
  if ptr_env:
    try:
      addr = int(ptr_env)
      if addr != 0:
        ctypes.c_int32.from_address(addr).value = exit_code
        return  # Success
    except Exception:  # pylint: disable=broad-except
      pass  # Fail silently and fall back to sys.exit

  sys.exit(exit_code)


if __name__ == '__main__':
  main()

# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for cleaning dataflow errors to be user friendly."""

TENSORFLOW_OP_MATCHER = "\n\nCaused by op"


def filter_tensorflow_error(error_string):
  """Removes information from a tensorflow error to hide Dataflow details.

  TF appends the operation details if they exist, but the stacktrace
  is not useful to the user, so we remove it if present.

  Args:
    error_string: PredictionError error detail, error caught during Session.run

  Returns:
    error_string with only base error message instead of full traceback.
  """
  return error_string.split(TENSORFLOW_OP_MATCHER)[0]

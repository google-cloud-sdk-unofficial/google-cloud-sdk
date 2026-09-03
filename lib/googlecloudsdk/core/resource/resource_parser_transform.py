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

"""Transforms used during parsing of resource projection expressions.

These transforms (always, if, map, synthesize) are recognized at parse time
and discarded, serving as directives rather than runtime value morphing.
"""


def TransformAlways(r):
  """Marks a transform sequence to always be applied.

  In some cases transforms are disabled. Prepending always() to a transform
  sequence causes the sequence to always be evaluated.

  Example:
    `some_field.always().foo().bar()`:::
    Always applies foo() and then bar().

  Args:
    r: A resource.

  Returns:
    r.
  """
  # This method is used as a decorator in transform expressions. It is
  # recognized at parse time and discarded.
  return r


def TransformIf(r, expr):
  """Disables the projection key if the flag name filter expr is false.

  Args:
    r: A JSON-serializable object.
    expr: A command flag filter name expression. See `gcloud topic filters` for
      details on filter expressions. The expression variables are flag names
      without the leading *--* prefix and dashes replaced by underscores.

  Example:
    `table(name, value.if(NOT short_format))`:::
    Lists a value column if the *--short-format* command line flag is not
    specified.

  Returns:
    r
  """
  del expr
  return r


def TransformMap(r, depth=1):
  """Applies the next transform in the sequence to each resource list item.

  Example:
    ```list_field.map().foo().list()```:::
    Applies foo() to each item in list_field and then list() to the resulting
    value to return a compact comma-separated list.
    ```list_field.*foo().list()```:::
    ```*``` is shorthand for map().
    ```list_field.map().foo().map().bar()```:::
    Applies foo() to each item in list_field and then bar() to each item in the
    resulting list.
    ```abc.xyz.map(2).foo()```:::
    Applies foo() to each item in xyz[] for all items in abc[].
    ```abc.xyz.**foo()```:::
    ```**``` is shorthand for map(2).

  Args:
    r: A resource.
    depth: The list nesting depth.

  Returns:
    r.
  """
  # This method is used as a decorator in transform expressions. It is
  # recognized at parse time and discarded.
  del depth
  return r


def TransformSynthesize(r, *args):
  """Synthesizes a new resource from the schema arguments.

  A list of tuple arguments controls the resource synthesis. Each tuple is a
  schema that defines the synthesis of one resource list item. Each schema
  item defines the synthesis of one synthesized_resource attribute from an
  original_resource attribute.

  There are three kinds of schema items:

  *name:literal*:::
  The value for the name attribute in the synthesized resource is the literal
  value.
  *name=key*:::
  The value for the name attribute in the synthesized_resource is the
  value of key in the original_resource.
  *key*:::
  All the attributes of the value of key in the original_resource are
  added to the attributes in the synthesized_resource.
  :::

  Args:
    r: A resource list.
    *args: The list of schema tuples.

  Example:
    This returns a list of two resource items:::
    `synthesize((name:up, upInfo), (name:down, downInfo))`
    If upInfo and downInfo serialize to:::
    `{"foo": 1, "bar": "yes"}`
    and:::
    `{"foo": 0, "bar": "no"}`
    then the synthesized resource list is:::
    `[{"name": "up", "foo": 1, "bar": "yes"},
      {"name": "down", "foo": 0, "bar": "no"}]`
    This could then be displayed by a nested table using:::
    `synthesize(...):format="table(name, foo, bar)"`


  Returns:
    A synthesized resource list.
  """
  # This method is used as a decorator in transform expressions. It is
  # recognized at parse time and discarded.
  del args
  return r

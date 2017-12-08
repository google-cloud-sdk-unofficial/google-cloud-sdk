# Copyright 2015 Google Inc. All Rights Reserved.
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

"""A command that reads JSON data and lists it."""

import json
import sys

from googlecloudsdk.calliope import base
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_property


class Aggregator(object):
  """Aggregates a field in an iterable object to a single list.

  The returned object is another iterable.

  Example:
    iterable = Aggregator(iterable, key)
    for item in iterable:
      VisitEachItemInEachResourceList(item)

  Attributes:
    _iterable: The original iterable.
    _key: The lexed key name.
    _list: The current list.
    _stop: If True then the object is not iterable and it has already been
      returned.
  """

  def __init__(self, iterable, key):
    self._iterable = iterable
    self._key = key
    self._list = []
    self._index = 0
    self._stop = False

  def __iter__(self):
    return self

  def _NextItem(self):
    """Returns the next item from self._iterable.

    Raises:
      StopIteration when self._iterable is exhausted.

    Returns:
      The next item from self._iterable.
    """
    try:
      # Object is a generator or iterator.
      return self._iterable.next()
    except AttributeError:
      pass
    try:
      # Object is a list.
      return self._iterable.pop(0)
    except (AttributeError, KeyError, TypeError):
      pass
    except IndexError:
      raise StopIteration
    # Object is not iterable -- treat it as the only item.
    if self._iterable is None or self._stop:
      raise StopIteration
    self._stop = True
    return self._iterable

  def next(self):
    """Returns the next item in the aggregated list."""
    while self._index >= len(self._list):
      obj = self._NextItem()
      self._list = resource_property.Get(obj, self._key) or []
      if not isinstance(self._list, list):
        self._list = [self._list]
      self._index = 0
    item = self._list[self._index]
    self._index += 1
    return item


class ListFromJson(base.ListCommand):
  """Read JSON data and list it on the standard output.

  *{command}* is a test harness for the output resource *--aggregate*,
  *--filter* and *--format* flags. It behaves like any other `gcloud ... list`
  command with respect to those flags.

  The input JSON data is either a single resource object or a list of resource
  objects of the same type. The resources are printed on the standard output.
  The default output format is *json*.
  """

  @staticmethod
  def Args(parser):
    # TODO(user): Drop --aggregate when the --aggregate global flag lands.
    parser.add_argument(
        '--aggregate',
        metavar='KEY',
        default=None,
        help=('Aggregate the lists named by KEY into a single list'
              ' that can be controlled by *--filter* and *--format*.'))
    parser.add_argument(
        'json_file',
        metavar='JSON-FILE',
        nargs='?',
        default=None,
        help=('A file containing JSON data for a single resource or a list of'
              ' resources of the same type. If omitted then the standard input'
              ' is read.'))

  def Run(self, args):
    if args.json_file:
      with open(args.json_file, 'r') as f:
        resources = json.load(f)
    else:
      resources = json.load(sys.stdin)
    # TODO(user): Drop this if when the --aggregate global flag lands.
    if args.aggregate:
      key = resource_lex.Lexer(args.aggregate).Key()
      resources = Aggregator(resources, key)
    return resources

  def Format(self, args):
    return 'json'

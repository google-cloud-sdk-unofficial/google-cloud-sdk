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

"""Sqlite-backed config store."""

import json
import logging
import os
import sqlite3
from typing import Dict

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.configurations import named_configs
import six


class Error(exceptions.Error):
  """Exceptions for the cli module."""


class _SqlCursor(object):
  """Context manager to access sqlite store."""

  def __init__(self, store_file):
    self._store_file = store_file
    self._connection = None
    self._cursor = None

  def __enter__(self):
    self._connection = sqlite3.connect(
        self._store_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
        isolation_level=None,  # Use autocommit mode.
        check_same_thread=True,  # Only creating thread may use the connection.
    )
    # Wait up to 1 second for any locks to clear up.
    # https://sqlite.org/pragma.html#pragma_busy_timeout
    self._connection.execute('PRAGMA busy_timeout = 1000')
    self._cursor = self._connection.cursor()
    return self

  def __exit__(self, exc_type, unused_value, unused_traceback):
    if not exc_type:
      # Don't try to commit if exception is in progress.
      self._connection.commit()
    self._connection.close()

  def RowCount(self):
    return self._cursor.rowcount

  def Execute(self, *args):
    return self._cursor.execute(*args)


def GetConfigStore(config_name=None):
  """Gets the config sqlite store for a given config name.

  Args:
    config_name: string, The configuration name to get the config store for.

  Returns:
    SqliteConfigStore, The corresponding config store, or None if no config.
  """
  # Automatically defaults to active config if config_name is not specified
  if config_name is None:
    # Need try catch due to CLOUDSDK_CONFIG not writeable case, see b/290619868
    try:
      config_name = named_configs.ConfigurationStore.ActiveConfig().name
    except named_configs.NamedConfigFileAccessError:
      return None
  return _GetSqliteStore(config_name)


def _BooleanValidator(attribute_name, attribute_value):
  """Validates boolean attributes.

  Args:
    attribute_name: str, the name of the attribute
    attribute_value: str | bool, the value of the attribute to validate

  Raises:
    InvalidValueError: if value is not boolean
  """
  accepted_strings = [
      'true',
      '1',
      'on',
      'yes',
      'y',
      'false',
      '0',
      'off',
      'no',
      'n',
      '',
      'none',
  ]
  if Stringize(attribute_value).lower() not in accepted_strings:
    raise InvalidValueError(
        'The [{0}] value [{1}] is not valid. Possible values: [{2}]. '
        '(See http://yaml.org/type/bool.html)'.format(
            attribute_name,
            attribute_value,
            ', '.join([x if x else "''" for x in accepted_strings]),
        )
    )


def Stringize(value):
  if isinstance(value, six.string_types):
    return value
  return str(value)


class InvalidValueError(Error):
  """An exception to be raised when the set value of a config attribute is invalid."""


class SqliteConfigStore(object):
  """Sqlite backed config store."""

  def __init__(self, store_file, config_name):
    self._cursor = _SqlCursor(store_file)
    self._config_name = config_name
    self._Execute(
        'CREATE TABLE IF NOT EXISTS config '
        '(config_attr TEXT PRIMARY KEY, value BLOB)'
    )

  def _Execute(self, *args):
    with self._cursor as cur:
      return cur.Execute(*args)

  def _LoadAttribute(self, config_attr, required):
    """Returns the attribute value from the SQLite table."""
    loaded_config = None
    with self._cursor as cur:
      try:
        loaded_config = cur.Execute(
            'SELECT value FROM config WHERE config_attr = ?',
            (config_attr,),
        ).fetchone()
      except sqlite3.OperationalError as e:
        logging.warning(
            'Could not load config attribute [%s] in cache: %s',
            config_attr,
            str(e),
        )
    if loaded_config is None and required:
      logging.warning(
          'The required config attribute [%s] is not set.',
          config_attr,
      )
    elif loaded_config is None:
      return None

    return loaded_config[0]

  def _Load(self):
    """Returns the entire config object from the SQLite table."""
    loaded_config = None
    with self._cursor as cur:
      try:
        loaded_config = cur.Execute(
            'SELECT config_attr, value FROM config ORDER BY rowid',
        ).fetchall()
      except sqlite3.OperationalError as e:
        logging.warning(
            'Could not store config attribute in cache: %s', (str(e))
        )

    return loaded_config

  def Get(self, config_attr, required=False):
    """Gets the given attribute.

    Args:
      config_attr: string, The attribute key to get.
      required: bool, True to raise an exception if the attribute is not set.

    Returns:
      object, The value of the attribute, or None if it is not set.
    """
    attr_value = self._LoadAttribute(config_attr, required)
    if attr_value is None or Stringize(attr_value).lower() == 'none':
      return None
    return attr_value

  def Set(self, config_attr, config_value):
    """Sets the value for an attribute.

    Args:
      config_attr: string, the primary key of the attribute to store.
      config_value: obj, the value of the config key attribute.
    """
    if isinstance(config_value, Dict):
      config_value = json.dumps(config_value).encode('utf-8')
    self._StoreAttribute(
        config_attr,
        config_value,
    )

  def _GetBoolAttribute(self, config_attr, required, validate=True):
    """Gets the given attribute in bool form.

    Args:
      config_attr: string, The attribute key to get.
      required: bool, True to raise an exception if the attribute is not set.
      validate: bool, True to validate the value

    Returns:
      bool, The value of the attribute, or None if it is not set.
    """
    attr_value = self._LoadAttribute(config_attr, required)
    if validate:
      _BooleanValidator(config_attr, attr_value)
    if attr_value is None:
      return None
    attr_string_value = Stringize(attr_value).lower()
    if attr_string_value == 'none':
      return None
    return attr_string_value in ['1', 'true', 'on', 'yes', 'y']

  def GetBool(self, config_attr, required=False, validate=True):
    """Gets the boolean value for this attribute.

    Args:
      config_attr: string, The attribute key to get.
      required: bool, True to raise an exception if the attribute is not set.
      validate: bool, Whether or not to run the fetched value through the
        validation function.

    Returns:
      bool, The boolean value for this attribute, or None if it is not set.

    Raises:
      InvalidValueError: if value is not boolean
    """
    value = self._GetBoolAttribute(config_attr, required, validate=validate)
    return value

  def _GetIntAttribute(self, config_attr, required):
    """Gets the given attribute in integer form.

    Args:
      config_attr: string, The attribute key to get.
      required: bool, True to raise an exception if the attribute is not set.

    Returns:
      int, The integer value of the attribute, or None if it is not set.
    """
    attr_value = self._LoadAttribute(config_attr, required)
    if attr_value is None:
      return None
    try:
      return int(attr_value)
    except ValueError as exc:
      raise InvalidValueError(
          'The attribute [{attr}] must have an integer value: [{value}]'.format(
              attr=config_attr, value=attr_value
          )
      ) from exc

  def GetInt(self, config_attr, required=False):
    """Gets the integer value for this attribute.

    Args:
      config_attr: string, The attribute key to get.
      required: bool, True to raise an exception if the attribute is not set.

    Returns:
      int, The integer value for this attribute.
    """
    value = self._GetIntAttribute(config_attr, required)
    return value

  def GetJSON(self, config_attr, required=False):
    """Gets the JSON value for this attribute.

    Args:
      config_attr: string, The attribute key to get.
      required: bool, True to raise an exception if the attribute is not set.

    Returns:
      The JSON value for this attribute or None.

    Raises:
      sqlite3.DataError: if the attribute value is None.
    """
    attr_value = self._LoadAttribute(config_attr, required)
    if attr_value is None:
      raise sqlite3.DataError(
          'The attribute [{attr}] is not set.'.format(attr=config_attr)
      )
    try:
      return json.loads(attr_value)
    except ValueError:
      return attr_value

  def _StoreAttribute(self, config_attr: str, config_value):
    """Stores the input config attributes to the record of config_name in the cache.

    Args:
      config_attr: string, the primary key of the attribute to store.
      config_value: obj, the value of the config key attribute.
    """
    self._Execute(
        'REPLACE INTO config (config_attr, value) VALUES (?,?)',
        (config_attr, config_value),
    )

  def DeleteConfig(self):
    """Permanently erases the config .db file."""
    config_db_path = config.Paths().config_db_path.format(self._config_name)

    try:
      if os.path.exists(config_db_path):
        os.remove(config_db_path)
      else:
        logging.warning(
            'Failed to delete config DB: path [%s] does not exist.',
            config_db_path,
        )
    except OSError as e:
      logging.warning('Could not delete config from cache: %s', str(e))

  def _DeleteAttribute(self, config_attr: str) -> bool:
    """Deletes a specified attribute from the config.

    Args:
      config_attr: string, the primary key of the attribute to delete.

    Returns:
      Whether the attribute was successfully deleted.

    Raises:
      sqlite3.OperationalError: if the attribute could not be deleted.
    """
    self._Execute(
        'DELETE FROM config WHERE config_attr = ?',
        (config_attr,),
    )
    # Check if deletion itself was successful
    if self._cursor.RowCount() < 1:
      raise sqlite3.OperationalError(
          'Could not delete attribute [%s] from config store [%s].'
          % (config_attr, self._config_name)
      )
    return True

  def Remove(self, config_attr: str) -> bool:
    """Removes an attribute from the config.

    Args:
      config_attr: string, the primary key of the attribute to remove.

    Returns:
      Whether the attribute was successfully removed.
    """
    return self._DeleteAttribute(config_attr)


def _GetSqliteStore(config_name) -> SqliteConfigStore:
  """Get a sqlite-based Config Store."""
  sqlite_config_file = config.Paths().config_db_path.format(config_name)
  config_store = SqliteConfigStore(sqlite_config_file, config_name)
  return config_store

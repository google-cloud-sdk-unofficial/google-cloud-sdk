#!/usr/bin/env python
"""The classes used to define config used to delegate BQ commands to gcloud."""

from collections.abc import Callable
from typing import Dict, List, Optional, Union
from typing_extensions import TypeAlias

PrimitiveFlagValue: TypeAlias = Union[str, bool, int]


class BigqueryGcloudDelegationUserError(Exception):
  """Class to represent a user error during gcloud delegation."""


class FlagMapping:
  """Defines how to create a gcloud command flag from a bq flag.

  For example this would return True:

  FlagMapping(
      bq_name='httplib2_debuglevel',
      gcloud_name='log-http',
      bq_to_gcloud_mapper=lambda x: x > 0,
  ).bq_to_gcloud_mapper(1)
  """

  def __init__(
      self,
      bq_name: str,  # The name of the original bq flag.
      gcloud_name: str,  # The gcloud flag that is mapped to.
      bq_to_gcloud_mapper: Optional[
          Callable[[PrimitiveFlagValue], PrimitiveFlagValue]
      ] = None,
  ):
    self.bq_name = bq_name
    self.gcloud_name = gcloud_name
    if bq_to_gcloud_mapper:
      self.bq_to_gcloud_mapper = bq_to_gcloud_mapper
    else:
      self.bq_to_gcloud_mapper = self.default_map_bq_value_to_gcloud_value

  # TODO(b/398206856): Simplify this function and validate behaviour.
  def default_map_bq_value_to_gcloud_value(
      self, bq_flag_value: PrimitiveFlagValue
  ) -> PrimitiveFlagValue:
    """Takes a bq flag value and returns the equivalent gcloud flag value."""
    if isinstance(bq_flag_value, bool):
      return bq_flag_value or False
    elif isinstance(bq_flag_value, int):
      return bq_flag_value
    else:
      return str(bq_flag_value)


class UnsupportedFlagMapping(FlagMapping):
  """Defines a bq global flag that is not supported in gcloud."""

  def __init__(
      self,
      bq_name: str,
      error_message: str,
  ):
    def raise_unsupported_flag_error(x: Union[str, bool]) -> Union[str, bool]:
      raise BigqueryGcloudDelegationUserError(error_message)

    super().__init__(bq_name, 'unsupported_flag', raise_unsupported_flag_error)


class GlobalFlagsMap:
  """The bq to gcloud global flag mappings.

  For example:

  GlobalFlagsMap([
    FlagMapping(
        bq_name='project_id',
        gcloud_name='project'),
    FlagMapping(
        bq_name='httplib2_debuglevel',
        gcloud_name='log-http', lambda x: x > 0)
  ]).map_to_gcloud_global_flags({
      'project_id': 'my_project',
      'httplib2_debuglevel': 1
  })

  Would return:

  {'project': 'my_project', 'log-http': True}
  """

  def __init__(self, global_flags: List[FlagMapping]):
    self.flag_mapping_from_bq_name = {}
    for flag_mapping in global_flags:
      bq_flag = flag_mapping.bq_name
      if bq_flag in self.flag_mapping_from_bq_name:
        raise ValueError(f'Duplicate bq flag: {bq_flag}')
      self.flag_mapping_from_bq_name[bq_flag] = flag_mapping

  def map_to_gcloud_global_flags(
      self, bq_global_flags: Dict[str, PrimitiveFlagValue]
  ) -> Dict[str, PrimitiveFlagValue]:
    """Returns the equivalent gcloud global flags for a set of bq flags.

    Args:
      bq_global_flags: The bq flags that will be mapped. For example,
        {'project_id': 'my_project', 'httplib2_debuglevel': 1}

    Returns:
      The equivalent gcloud flags. For example,
      {'project': 'my_project', 'log-http': True}
    """
    gcloud_flags = {}
    for bq_flag, bq_flag_value in bq_global_flags.items():
      if bq_flag not in self.flag_mapping_from_bq_name:
        raise ValueError(f'Unsupported bq flag: {bq_flag}')
      flag_mapper = self.flag_mapping_from_bq_name[bq_flag]
      gcloud_flags[flag_mapper.gcloud_name] = flag_mapper.bq_to_gcloud_mapper(
          bq_flag_value
      )
    return gcloud_flags

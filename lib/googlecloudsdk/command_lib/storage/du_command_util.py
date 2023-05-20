# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Functions for du command to display resource size."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage import list_util
from googlecloudsdk.command_lib.storage import ls_command_util
from googlecloudsdk.command_lib.storage.list_util import BaseFormatWrapper
from googlecloudsdk.command_lib.storage.list_util import BaseListExecutor
from googlecloudsdk.command_lib.storage.resources import shim_format_util


class _ObjectFormatWrapper(BaseFormatWrapper):
  """For formatting how obejects are printed when listed by du."""

  def __str__(self):
    """Returns string of select properties from resource."""
    size = getattr(self.resource, 'size', 0)
    url_string, metageneration_string = self._check_and_handles_all_versions()

    # Example: 6194    gs://test/doc/README.md   metageneration
    return ('{size:<13}{url}{metageneration}').format(
        size=list_util.check_and_convert_to_readable_sizes(
            size, self._readable_sizes, use_gsutil_style=self._use_gsutil_style
        ),
        url=url_string,
        metageneration=metageneration_string,
    )


class _ContainerSummaryFormatWrapper(BaseFormatWrapper):
  """For formatting how containers are printed when listed by du."""

  def __init__(
      self,
      resource,
      all_versions=False,
      container_size=None,
      readable_sizes=False,
      use_gsutil_style=False,
  ):
    """See BaseFormatWrapper class for function doc strings."""
    super(_ContainerSummaryFormatWrapper, self).__init__(
        resource,
        all_versions=all_versions,
        display_detail=ls_command_util.DisplayDetail.SHORT,
        readable_sizes=readable_sizes,
        use_gsutil_style=use_gsutil_style,
    )
    self._container_size = container_size

  def __str__(self):
    """Returns string of select properties from resource."""
    # Buckets and prefixes: only print container_size.
    url_string = self.resource.storage_url.versionless_url_string

    # Convert to human readable format.
    size = list_util.check_and_convert_to_readable_sizes(
        self._container_size, self._readable_sizes, self._use_gsutil_style
    )

    # Example: 6194    gs://test/doc/README.md   metageneration
    return ('{size:<13}{url}').format(
        size=size,
        url=url_string,
    )


class DuExecutor(BaseListExecutor):
  """Helper class for the Du command."""

  def __init__(
      self,
      cloud_urls,
      all_versions=False,
      readable_sizes=False,
      summarize=False,
      total=False,
      use_gsutil_style=False,
      zero_terminator=False,
  ):
    """See BaseListExecutor class for function doc strings."""

    super(DuExecutor, self).__init__(
        cloud_urls=cloud_urls,
        all_versions=all_versions,
        total=total,
        readable_sizes=readable_sizes,
        recursion_flag=True,
        use_gsutil_style=use_gsutil_style,
        zero_terminator=zero_terminator,
    )
    self._summarize = summarize
    if not self._summarize:
      self._container_summary_wrapper = _ContainerSummaryFormatWrapper
      self._object_wrapper = _ObjectFormatWrapper

  def _print_summary_for_top_level_url(
      self, resource_url, only_display_buckets, object_count, total_bytes
  ):
    if not self._summarize:
      return
    if self._readable_sizes:
      total_bytes = shim_format_util.get_human_readable_byte_value(
          total_bytes, use_gsutil_style=self._use_gsutil_style
      )
    print(
        '{size:<13}{url}'.format(
            size=total_bytes, url=resource_url.url_string
        )
    )

  def _print_total(self, all_sources_total_bytes):
    print(
        '{size:<13}total'.format(
            size=list_util.check_and_convert_to_readable_sizes(
                all_sources_total_bytes,
                self._readable_sizes,
                self._use_gsutil_style,
            )
        )
    )

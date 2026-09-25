# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Command for cache invalidation."""


import argparse
import textwrap
from typing import Any, List, Optional, Tuple

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import batch_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.url_maps import flags
from googlecloudsdk.command_lib.compute.url_maps import url_maps_utils
from googlecloudsdk.command_lib.projects import util as project_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources as core_resources

_MAX_PATH_LENGTH = 1024
_MAX_TAGS_COUNT = 10
_MAX_TAG_LENGTH = 120
_TAG_MIN_ASCII = 33
_TAG_MAX_ASCII = 126
_MAX_CONTENT_TYPE_PART_LENGTH = 64


def _GetProjectNumber(project_identifier: str) -> str:
  """Returns the project number for a project ID.

  Args:
    project_identifier: The project identifier, which can be either a project ID
      or a project number.

  Returns:
    The project number for the project identifier.
  """
  if project_identifier.isdigit():
    return project_identifier

  return str(project_util.GetProjectNumber(project_identifier))


def _ResolveInvalidateCacheBackendResource(
    args: argparse.Namespace,
    collection: str,
    url_map_ref: core_resources.Resource,
    resources: core_resources.Registry,
) -> Optional[core_resources.Resource]:
  """Parses the backend resource that is routed to by a URL map from args.

  This function handles parsing a backend service or backend bucket that is
  routed to by a URL map.

  Args:
    args: The arguments provided to the invalidate-cache command.
    collection: one of 'compute.backendServices' or 'compute.backendBuckets'.
    url_map_ref: The resource reference to the URL map. This is returned by
      parsing the URL map arguments provided.
    resources: ComputeApiHolder resources manager.

  Returns:
    Backend service or bucket reference parsed from args.
  """
  if collection == 'compute.backendServices':
    value = getattr(args, 'backend_service', None)
  elif collection == 'compute.backendBuckets':
    value = getattr(args, 'backend_bucket', None)
  else:
    return None

  return resources.Parse(
      value,
      collection=collection,
      params={'project': url_map_ref.project},
  )


def _ResolveInvalidateCacheBackendUri(
    args: argparse.Namespace,
    url_map_ref: core_resources.Resource,
    resources: core_resources.Registry,
) -> Optional[str]:
  """Resolves backend service or bucket and returns URI with project number.

  Args:
    args: The arguments provided to the invalidate-cache command.
    url_map_ref: The resource reference to the URL map.
    resources: ComputeApiHolder resources.

  Returns:
    Formatted URI string with project number, or None if neither flag is set.
  """
  if getattr(args, 'backend_service', None) is not None:
    collection = 'backendServices'
    flag_name = '--backend-service'
  elif getattr(args, 'backend_bucket', None) is not None:
    collection = 'backendBuckets'
    flag_name = '--backend-bucket'
  else:
    return None

  try:
    backend_ref = _ResolveInvalidateCacheBackendResource(
        args, f'compute.{collection}', url_map_ref, resources
    )
  except core_resources.Error as e:
    raise calliope_exceptions.InvalidArgumentException(flag_name, str(e)) from e

  if backend_ref is None:
    return None

  try:
    project_number = _GetProjectNumber(backend_ref.project)
  except (apitools_exceptions.HttpError, core_exceptions.Error) as e:
    raise calliope_exceptions.InvalidArgumentException(
        flag_name,
        f'Could not resolve project number for project [{backend_ref.project}].'
        ' Cloud CDN cache invalidation requires the project number, not the '
        'project ID, for backend references. Please verify that the Cloud '
        'Resource Manager API is enabled and that you have '
        '`resourcemanager.projects.get` permission, or specify the backend '
        'using the project number directly (e.g. '
        '`projects/<PROJECT_NUMBER>/...` or `--project <PROJECT_NUMBER>`).',
    ) from e

  return f'projects/{project_number}/global/{collection}/{backend_ref.Name()}'


def _ValidPath(path: str) -> str:
  """Validates the path argument."""
  if not path.startswith('/'):
    raise argparse.ArgumentTypeError(
        f'Path must start with /; received: [{path}]'
    )
  if '?' in path or '#' in path:
    raise argparse.ArgumentTypeError(
        f'Path must not contain ? or #; received: [{path}]'
    )
  star_count = path.count('*')
  if star_count > 1 or (star_count == 1 and not path.endswith('*')):
    raise argparse.ArgumentTypeError(
        'Path must have at most one wildcard (*) at the end of the path; '
        f'received: [{path}]'
    )
  if len(path) > _MAX_PATH_LENGTH:
    raise argparse.ArgumentTypeError(
        f'Path must be less than or equal to {_MAX_PATH_LENGTH} characters'
        f' long; received: [{path}] of length {len(path)}. Consider using a'
        ' wildcard (*) to match longer paths, (e.g.'
        f' [{path[:_MAX_PATH_LENGTH - 1]}*])'
    )
  return path


def _ValidTags(tags: str) -> list[str]:
  """Validates the tags argument."""
  tag_list = tags.split(',')
  if len(tag_list) > _MAX_TAGS_COUNT:
    raise argparse.ArgumentTypeError(
        f'Tags must be a comma-delimited list of at most {_MAX_TAGS_COUNT}'
        f' tags; received: [{tags!r}] of length {len(tag_list)}'
    )
  stripped_tags = [tag.strip() for tag in tag_list]
  for tag in stripped_tags:
    if not tag:
      raise argparse.ArgumentTypeError('Tags must not contain empty strings')
    if len(tag) > _MAX_TAG_LENGTH:
      raise argparse.ArgumentTypeError(
          f'Tags must not contain strings exceeding {_MAX_TAG_LENGTH}'
          f' characters; received: [{tag!r}] of length {len(tag)}'
      )
    for char in tag:
      if not _TAG_MIN_ASCII <= ord(char) <= _TAG_MAX_ASCII:
        raise argparse.ArgumentTypeError(
            'Tags must contain strings with visible ASCII characters only from'
            f' `!` to `~`; received: [{char}] in [{tag}]'
        )
  return stripped_tags


def _ValidContentType(content_type: str) -> str:
  """Validates content-type matcher."""
  if ';' in content_type:
    raise argparse.ArgumentTypeError(
        f'Content-type must not contain parameters; received: [{content_type}]'
    )
  parts = content_type.split('/')
  if len(parts) != 2:
    raise argparse.ArgumentTypeError(
        'Content-type must be in the type/subtype format; received: '
        f'[{content_type}]'
    )
  for part in parts:
    if not part:
      raise argparse.ArgumentTypeError(
          "Content-type's type and subtype must not be empty; received: "
          f'[{content_type}]'
      )
    if len(part) > _MAX_CONTENT_TYPE_PART_LENGTH:
      raise argparse.ArgumentTypeError(
          "Content-type's type and subtype must not exceed "
          f'{_MAX_CONTENT_TYPE_PART_LENGTH} characters long; '
          f'received: [{part}] of length {len(part)}'
      )
    if not part[0].isalnum():
      raise argparse.ArgumentTypeError(
          "Content-type's type and subtype must start with an alphanumeric "
          f'character; received: [{part}]'
      )
    for char in part:
      if not (char.isalnum() or char in '!#$&-^_.+'):
        raise argparse.ArgumentTypeError(
            "Content-type's type and subtype must only contain alphanumeric "
            f'characters or `!#$&-^_.+`; received: [{char}] in [{part}]'
        )
  return content_type


def _DetailedHelp():
  return {
      'brief':
          'Invalidate specified objects for a URL map in Cloud CDN caches.',
      'DESCRIPTION':
          """\
      *{command}* requests that Cloud CDN stop using cached content for
      resources at a particular URL path or set of URL paths.

      *{command}* may succeed even if no content is cached for some or all
      URLs with the given path.
      """,
  }


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.PREVIEW)
class InvalidateCdnCache(base.SilentCommand):
  """Invalidate specified objects for a URL map in Cloud CDN caches."""

  _support_extended_matchers = False

  detailed_help = _DetailedHelp()
  URL_MAP_ARG = None

  @classmethod
  def _ValidHost(cls, host: str) -> str:
    """Validates the host argument.

    If _support_extended_matchers is True, allows a single wildcard '*' at the
    beginning of the host, immediately followed by a '.'.

    Args:
      host: The host string to validate.

    Returns:
      The validated host string.

    Raises:
      argparse.ArgumentTypeError: If the host is invalid.
    """
    star_count = host.count('*')
    if not cls._support_extended_matchers and star_count > 0:
      raise argparse.ArgumentTypeError(
          f'Host must not contain a wildcard (*); received: [{host}]'
      )
    if star_count > 1 or (star_count == 1 and not host.startswith('*.')):
      msg = (
          'Host must have at most one wildcard (*). If present, it must be the '
          'first character of the host, followed immediately by a `.` '
          f'character; received: [{host}]'
      )
      raise argparse.ArgumentTypeError(msg)
    if len(host) > 1024:
      msg = (
          'Host must be less than or equal to 1024 characters long; received: '
          f'[{host}] of length {len(host)}'
      )
      raise argparse.ArgumentTypeError(msg)
    host_for_idna = host
    if star_count == 1:
      # Strip '*.' prefix for IDNA validation.
      host_for_idna = host[2:]
    if not host_for_idna:
      raise argparse.ArgumentTypeError(
          f'Host must be a valid host name; received: [{host}]'
      )
    try:
      host_for_idna.encode('idna')
    except UnicodeError as e:
      raise argparse.ArgumentTypeError(
          f'Host must be a valid host name; received: [{host}]'
      ) from e
    return host

  @classmethod
  def Args(cls, parser):
    """Adds invalidate-cdn-cache arguments to the parser."""
    cls.URL_MAP_ARG = flags.GlobalUrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser, cust_metavar='URLMAP')

    parser.add_argument(
        '--path',
        type=_ValidPath,
        help=textwrap.dedent("""\
        A path specifying which objects to invalidate. PATH must start with
        ``/'' and the only place a ``*'' is allowed is at the end of the path.
        It will be matched against URL paths, which do not include scheme, host,
        or any text after the first ``?'' or ``#'' (and those characters are not
        allowed here). For example, for the URL
        ``https://example.com/whatever/x.html?a=b'', the path is
        ``/whatever/x.html''.

        If PATH ends with ``*'', the preceding string is a prefix, and all URLs
        whose paths begin with it will be invalidated. If PATH doesn't end with
        ``*'', then only URLs with exactly that path will be invalidated.

        Examples:
        - ``'', ``*'', anything that doesn't start with ``/'': error
        - ``/'': just the root URL
        - ``/*'': everything
        - ``/x/y'': ``/x/y'' only (and not ``/x/y/'')
        - ``/x/y/'': ``/x/y/'' only (and not ``/x/y'')
        - ``/x/y*'': ``/x/y'' and everything with the prefix (e.g. ``/x/yy'',
          ``/x/y/z'')
        """),
    )

    if cls._support_extended_matchers:
      host_help = textwrap.dedent("""\
          If set, this invalidation will apply only to requests to the specified
          host. The leftmost label may be a wildcard. If present, the `*` must
          be the first character of the host, followed immediately by a `.`
          character.

          For example, `*.example.com` is valid, and it will match requests to
          www.example.com and api.example.com, but not to example.com or
          dev.api.example.com.
          """)
    else:
      host_help = textwrap.dedent("""\
          If set, this invalidation will apply only to requests to the
          specified host.
          """)
    parser.add_argument('--host', type=cls._ValidHost, help=host_help)

    parser.add_argument(
        '--tags',
        type=_ValidTags,
        help=textwrap.dedent("""\
        A single tag or a comma-delimited list of tags. When multiple tags are
        specified, the invalidation applies them using boolean OR logic.

        Example:
        - ``--tags=abcd,user123''
        """),
    )

    if cls._support_extended_matchers:
      parser.add_argument(
          '--http-status',
          type=arg_parsers.BoundedInt(200, 599),
          help=textwrap.dedent("""\
          If set, this invalidation will apply only to cached responses with the
          specified HTTP status code. Valid range is 200 to 599.
          """),
      )
      parser.add_argument(
          '--content-type',
          type=_ValidContentType,
          help=textwrap.dedent("""\
          If set, this invalidation rule will only apply to responses with the
          given Content-Type header. Content-type parameters are not allowed in
          a rule, and they are ignored from the response when matching.

          For example, "text/html; charset=UTF-8" is not allowed in a rule. An
          invalidation rule with content-type: "text/html" will match responses
          with both "text/html" and "text/html; charset=UTF-8" Content-Type
          headers.

          Wildcards are not allowed.
          """),
      )
      backend_group = parser.add_mutually_exclusive_group()
      backend_group.add_argument(
          '--backend-service',
          help=textwrap.dedent("""\
          If set, this invalidation will apply only to requests routed to the
          specified backend service. Either the id of a backend service in this
          project, or the full resource URI can be specified, e.g.,
          `projects/PROJECT_NUMBER/global/backendServices/BACKEND_SERVICE`.
          """),
      )
      backend_group.add_argument(
          '--backend-bucket',
          help=textwrap.dedent("""\
          If set, this invalidation will apply only to requests routed to the
          specified backend bucket. Either the id of a backend bucket in this
          project, or the full resource URI can be specified, e.g.,
          `projects/PROJECT_NUMBER/global/backendBuckets/BACKEND_BUCKET`.
          """),
      )

    base.ASYNC_FLAG.AddToParser(parser)

  def _CreateRequests(
      self,
      holder: base_classes.ComputeApiHolder,
      args: argparse.Namespace,
      url_map_ref: core_resources.Resource,
      backend_service_uri: Optional[str],
  ) -> List[Tuple[Any, str, Any]]:
    """Returns a list of requests necessary for cache invalidations."""
    if (
        args.path is None
        and args.host is None
        and args.tags is None
        and (
            not self._support_extended_matchers
            or (
                args.http_status is None
                and args.content_type is None
                and backend_service_uri is None
            )
        )
    ):
      extended_matchers = ''
      if self._support_extended_matchers:
        extended_matchers = (
            ', --http-status, --content-type, --backend-service,'
            ' --backend-bucket'
        )
      raise compute_exceptions.ArgumentError(
          'At least one matcher must be specified (--path, --host,'
          f' --tags{extended_matchers})'
      )

    messages = holder.client.messages
    cache_invalidation_rule_kwargs = {
        'path': args.path,
        'host': args.host,
    }
    if args.tags is not None:
      cache_invalidation_rule_kwargs['cacheTags'] = args.tags
    if self._support_extended_matchers:
      if args.http_status is not None:
        cache_invalidation_rule_kwargs['httpStatus'] = args.http_status
      if args.content_type is not None:
        cache_invalidation_rule_kwargs['contentType'] = args.content_type
      if backend_service_uri is not None:
        cache_invalidation_rule_kwargs['backendService'] = backend_service_uri

    return [(
        holder.client.apitools_client.urlMaps,
        'InvalidateCache',
        messages.ComputeUrlMapsInvalidateCacheRequest(
            project=url_map_ref.project,
            urlMap=url_map_ref.Name(),
            cacheInvalidationRule=messages.CacheInvalidationRule(
                **cache_invalidation_rule_kwargs
            ),
        ),
    )]

  def Run(self, args):
    """Issues requests necessary to invalidate a URL map cdn cache."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    url_map_ref = self.URL_MAP_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.GLOBAL,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )
    if url_maps_utils.IsRegionalUrlMapRef(url_map_ref):
      raise compute_exceptions.ArgumentError(
          'Invalid flag [--region]:'
          ' Regional URL maps do not support Cloud CDN caching.'
      )

    backend_service_uri = None
    if self._support_extended_matchers:
      backend_service_uri = _ResolveInvalidateCacheBackendUri(
          args,
          url_map_ref,
          holder.resources,
      )

    requests = self._CreateRequests(
        holder, args, url_map_ref, backend_service_uri
    )
    if args.async_:
      resources, errors = batch_helper.MakeRequests(
          requests=requests,
          http=client.apitools_client.http,
          batch_url=client.batch_url,
      )
      if errors:
        utils.RaiseToolException(errors)

      for invalidation_operation in resources:
        log.status.write(
            f'Invalidation pending for [{invalidation_operation.targetLink}]\n'
        )
        log.status.write(
            f'Monitor its progress at [{invalidation_operation.selfLink}]\n'
        )
      return resources
    else:
      # We want to run through the generator that MakeRequests returns in order
      # to actually make the requests.
      resources = client.MakeRequests(requests)

    return resources


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class InvalidateCdnCacheBeta(InvalidateCdnCache):
  _support_extended_matchers = True


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class InvalidateCdnCacheAlpha(InvalidateCdnCacheBeta):
  pass

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
"""Contains the properties for the 'core' section."""

import enum
import textwrap

from googlecloudsdk.core.properties.completers import COMPLETERS
from googlecloudsdk.core.properties.exceptions import InvalidProjectError
from googlecloudsdk.core.properties.exceptions import InvalidValueError
from googlecloudsdk.core.properties.exceptions import UnknownFormatError
from googlecloudsdk.core.properties.types import _Section
from googlecloudsdk.core.properties.validators import _AssertValidator
from googlecloudsdk.core.properties.validators import _LooksLikeAProjectName
from googlecloudsdk.core.properties.validators import _VALID_ASSERTIONS
from googlecloudsdk.core.properties.validators import _VALID_PROJECT_REGEX
from googlecloudsdk.core.properties.validators import ExistingAbsoluteFilepathValidator
from googlecloudsdk.core.resource import resource_printer_types as formats
import six


class _SectionCore(_Section):
  """Contains the properties for the 'core' section."""

  class InteractiveUXStyles(enum.Enum):
    NORMAL = 0
    OFF = 1
    TESTING = 2

  def __init__(self):
    super(_SectionCore, self).__init__('core')
    self.account = self._Add(
        'account',
        help_text=(
            'Account `gcloud` should use for authentication. '
            'Run `gcloud auth list` to see your currently available accounts.'
        ),
    )
    self.assert_ = self._Add(
        'assert',
        hidden=True,
        choices=list(_VALID_ASSERTIONS),
        validator=_AssertValidator,
        help_text=(
            '*(EXPERIMENTAL)* This property is experimental and '
            'not for production use. Assertions required for command '
            'execution, such as `readonly`.'
        ),
    )
    self.disable_collection_path_deprecation_warning = self._AddBool(
        'disable_collection_path_deprecation_warning',
        hidden=True,
        help_text=(
            'If False, any usage of collection paths will result in '
            'deprecation warning. Set it to False to disable it.'
        ),
    )
    self.default_regional_backend_service = self._AddBool(
        'default_regional_backend_service',
        help_text=(
            'If True, backend services in `gcloud compute backend-services`'
            ' will be regional by default. Setting the `--global` flag is'
            ' required for global backend services.'
        ),
    )
    self.disable_color = self._AddBool(
        'disable_color',
        help_text=(
            'If True, color will not be used when printing messages in '
            'the terminal.'
        ),
    )
    self.disable_command_lazy_loading = self._AddBool(
        'disable_command_lazy_loading', hidden=True
    )
    self.command_impl = self._Add(
        'command_impl',
        choices=['declarative', 'python'],
        default='python',
        hidden=True,
        help_text=(
            'Determines whether to prefer the declarative YAML or the Python'
            ' implementation of a command when both exist.'
        ),
    )
    self.disable_prompts = self._AddBool(
        'disable_prompts',
        help_text=(
            'If True, the default answer will be assumed for all user prompts.'
            ' However, for any prompts that require user input, an error will'
            ' be raised. This is equivalent to either using the global'
            ' `--quiet` flag or setting the environment variable'
            ' `CLOUDSDK_CORE_DISABLE_PROMPTS` to 1. Setting this property is'
            ' useful when scripting with `gcloud`.'
        ),
    )
    self.display_hints = self._AddBool(
        'display_hints',
        default=False,
        hidden=True,
        help_text='If True, the `--agent-hints` flag will be active.',
    )
    self.disable_usage_reporting = self._AddBool(
        'disable_usage_reporting',
        help_text=(
            'If True, anonymous statistics on SDK usage will not be collected.'
            ' This value is set by your choices during installation, but can be'
            ' changed at any time.  For more information, see [Usage'
            ' statistics](/sdk/docs/usage-statistics).'
        ),
    )
    self.enable_gri = self._AddBool(
        'enable_gri',
        default=False,
        hidden=True,
        help_text=(
            'If True, the parser for gcloud Resource Identifiers will be '
            'enabled when interpreting resource arguments.'
        ),
    )
    self.resource_completion_style = self._Add(
        'resource_completion_style',
        choices=('flags', 'gri'),
        default='flags',
        hidden=True,
        help_text=(
            'The resource completion style controls how resource strings '
            'are represented in command argument completions.  All styles, '
            'including uri, are handled on input.'
        ),
    )
    self.lint = self._Add(
        'lint',
        # Current runtime lint patterns. Delete from this comment when the
        # pattern usage has been deleted.
        #
        #   AddCacheUpdaters: Throws an exception for each command that needs
        #     a parser.display_info.AddCacheUpdater() call.
        #
        # When running tests set default=PATTERN[,PATTERN...] here to weed out
        # all occurrences of the patterns. Patterns are checked using substring
        # matching on the lint property string value:
        #
        #   if 'AddCacheUpdaters' in properties.VALUES.core.lint.Get():
        #     # AddCacheUpdaters lint check enabled.
        default='none',
        hidden=True,
        help_text=(
            'Enable the runtime linter for specific patterns. '
            'Each occurrence of a runtime pattern raises an exception. '
            'The pattern names are source specific. Consult the source for '
            'details.'
        ),
    )
    self.verbosity = self._Add(
        'verbosity',
        help_text=(
            'Default logging verbosity for `gcloud` commands.  This is the'
            ' equivalent of using the global `--verbosity` flag. Supported'
            ' verbosity levels: `debug`, `info`, `warning`, `error`,'
            ' `critical`, and `none`.'
        ),
    )
    self.user_output_enabled = self._AddBool(
        'user_output_enabled',
        help_text=(
            'True, by default. If False, messages to the user and command'
            ' output on both standard output and standard error will be'
            ' suppressed.'
        ),
        default=True,
    )
    self.interactive_ux_style = self._Add(
        'interactive_ux_style',
        help_text=(
            'How to display interactive UX elements like progress bars '
            'and trackers.'
        ),
        hidden=True,
        default=_SectionCore.InteractiveUXStyles.NORMAL,
        choices=[x.name for x in list(_SectionCore.InteractiveUXStyles)],
    )
    self.log_http = self._AddBool(
        'log_http',
        help_text=(
            'If True, log HTTP requests and responses to the logs.  '
            'To see logs in the terminal, adjust `verbosity` settings. '
            'Otherwise, logs are available in their respective log files.'
        ),
        default=False,
    )
    self.log_http_redact_token = self._AddBool(
        'log_http_redact_token',
        help_text=(
            'If true, this prevents log_http from printing access tokens.'
            ' This property does not have effect unless log_http is true.'
        ),
        default=True,
        hidden=True,
    )
    self.log_http_show_request_body = self._AddBool(
        'log_http_show_request_body',
        help_text=(
            'If true, this allows log_http to print the request body'
            ' for debugging purposes on requests with the'
            ' "redact_request_body_reason" parameter set on '
            ' core.credentials.transports.GetApitoolsTransports.'
            ' Note: this property does not have any effect unless'
            ' log_http is true.'
        ),
        default=False,
        hidden=True,
    )
    self.log_http_streaming_body = self._AddBool(
        'log_http_streaming_body',
        help_text=(
            'If True, log the streaming body instead of logging the "<streaming'
            ' body>" text. This flag results in reading the entire response'
            ' body in memory. This property does not have effect unless'
            ' log_http is true.'
        ),
        default=False,
        hidden=True,
    )
    self.http_timeout = self._Add('http_timeout', hidden=True)
    self.check_gce_metadata = self._AddBool(
        'check_gce_metadata', hidden=True, default=True
    )
    self.print_completion_tracebacks = self._AddBool(
        'print_completion_tracebacks',
        hidden=True,
        help_text=(
            'If True, print actual completion exceptions with traceback '
            'instead of the nice UX scrubbed exceptions.'
        ),
    )
    self.print_unhandled_tracebacks = self._AddBool(
        'print_unhandled_tracebacks', hidden=True
    )
    self.print_handled_tracebacks = self._AddBool(
        'print_handled_tracebacks', hidden=True
    )
    self.trace_token = self._Add(
        'trace_token',
        help_text=(
            'Token used to route traces of service requests for '
            'investigation of issues. This token will be provided by Google '
            'support.'
        ),
    )
    self.request_reason = self._Add('request_reason', hidden=True)
    self.pass_credentials_to_gsutil = self._AddBool(
        'pass_credentials_to_gsutil',
        default=True,
        help_text=(
            'If True, pass the configured Google Cloud CLI authentication '
            'to gsutil.'
        ),
    )
    self.api_key = self._Add(
        'api_key',
        hidden=True,
        help_text=(
            'If provided, this API key is attached to all outgoing API calls.'
        ),
    )
    self.should_prompt_to_enable_api = self._AddBool(
        'should_prompt_to_enable_api',
        default=True,
        hidden=True,
        help_text=(
            'If true, will prompt to enable an API if a command fails due'
            ' to the API not being enabled.'
        ),
    )
    self.color_theme = self._Add(
        'color_theme',
        help_text='Color palette for output.',
        hidden=True,
        default='off',
        choices=['off', 'normal', 'testing'],
    )
    self.use_legacy_flattened_format = self._AddBool(
        'use_legacy_flattened_format',
        hidden=True,
        default=False,
        help_text=(
            'If True, use legacy format for flattened() and text().'
            'Please note that this option will not be supported indefinitely.'
        ),
    )

    # Only formats that accept empty projections can be used globally
    supported_global_formats = sorted([
        formats.CONFIG,
        formats.DEFAULT,
        formats.DISABLE,
        formats.FLATTENED,
        formats.JSON,
        formats.LIST,
        formats.NONE,
        formats.OBJECT,
        formats.TEXT,
    ])

    def FormatValidator(print_format):
      if print_format and print_format not in supported_global_formats:
        raise UnknownFormatError(print_format, supported_global_formats)

    self.format = self._Add(
        'format',
        validator=FormatValidator,
        help_text=textwrap.dedent(
            """\
        Sets the format for printing all command resources. This overrides the
        default command-specific human-friendly output format. Use
        `--verbosity=debug` flag to view the command-specific format. If both
        `core/default_format` and `core/format` are specified, `core/format`
        takes precedence. If both `core/format` and `--format` are specified,
        `--format` takes precedence. The supported formats are limited to:
        `{0}`. For more details run $ gcloud topic formats. Run `$ gcloud config
        set --help` to see more information about `core/format`""".format(
                '`, `'.join(supported_global_formats)
            )
        ),
    )

    self.default_format = self._Add(
        'default_format',
        default='default',
        validator=FormatValidator,
        help_text=textwrap.dedent("""\
        Sets the default format for printing command resources.
        `core/default_format` overrides the default yaml format. If the command
        contains a command-specific output format, it takes precedence over the
        `core/default_format` value. Use `--verbosity=debug` flag to view the
        command-specific format. Both `core/format` and `--format` also take
        precedence over `core/default_format`. The supported formats are limited
        to: `{0}`. For more details run $ gcloud topic formats. Run `$ gcloud
        config set --help` to see more information about
        `core/default_format`""".format('`, `'.join(supported_global_formats))),
    )

    def ShowStructuredLogsValidator(show_structured_logs):
      if show_structured_logs is None:
        return
      if show_structured_logs not in ['always', 'log', 'terminal', 'never']:
        raise InvalidValueError((
            'show_structured_logs must be one of: '
            '[always, log, terminal, never]'
        ))

    self.show_structured_logs = self._Add(
        'show_structured_logs',
        choices=['always', 'log', 'terminal', 'never'],
        default='never',
        hidden=False,
        validator=ShowStructuredLogsValidator,
        help_text=textwrap.dedent("""\
        Control when JSON-structured log messages for the current verbosity
        level (and above) will be written to standard error. If this property
        is disabled, logs are formatted as `text` by default.
        +
        Valid values are:
            *   `never` - Log messages as text
            *   `always` - Always log messages as JSON
            *   `log` - Only log messages as JSON if stderr is a file
            *   `terminal` - Only log messages as JSON if stderr is a terminal
        +
        If unset, default is `never`."""),
    )

    def MaxLogDaysValidator(max_log_days):
      if max_log_days is None:
        return
      try:
        if int(max_log_days) < 0:
          raise InvalidValueError('Max number of days must be at least 0')
      except ValueError as exc:
        raise InvalidValueError(
            'Max number of days must be an integer'
        ) from exc

    self.max_log_days = self._Add(
        'max_log_days',
        validator=MaxLogDaysValidator,
        help_text=(
            'Maximum number of days to retain log files before deleting. If set'
            ' to 0, turns off log garbage collection and does not delete log'
            ' files. If unset, the default is 30 days.'
        ),
        default='30',
    )

    self.disable_file_logging = self._AddBool(
        'disable_file_logging',
        default=False,
        help_text=(
            'If True, `gcloud` will not store logs to a file. This may '
            'be useful if disk space is limited.'
        ),
    )

    self.parse_error_details = self._Add(
        'parse_error_details',
        help_text=(
            'If True, `gcloud` will attempt to parse and interpret '
            'error details in API originating errors. If False, `gcloud` will '
            ' write flush error details as is to stderr/log.'
        ),
        default=True,
    )

    self.custom_ca_certs_file = self._Add(
        'custom_ca_certs_file',
        validator=ExistingAbsoluteFilepathValidator,
        help_text='Absolute path to a custom CA cert file.',
    )

    def ProjectValidator(project):
      """Checks to see if the project string is valid."""
      if project is None:
        return

      if not isinstance(project, six.string_types):
        raise InvalidValueError('project must be a string')
      if project == '':  # pylint: disable=g-explicit-bool-comparison
        raise InvalidProjectError(
            'The project property is set to the empty string, which is invalid.'
        )
      if _VALID_PROJECT_REGEX.match(project):
        return

      if _LooksLikeAProjectName(project):
        raise InvalidProjectError(
            'The project property must be set to a valid project ID, not the '
            'project name [{value}]'.format(value=project)
        )
      # Non heuristics for a better error message.
      raise InvalidProjectError(
          'The project property must be set to a valid project ID, '
          '[{value}] is not a valid project ID.'.format(value=project)
      )

    self.project = self._Add(
        'project',
        help_text=(
            'Project ID of the Cloud Platform project to operate on by default.'
            '  This can be overridden by using the global `--project` flag.'
        ),
        validator=ProjectValidator,
        completer=COMPLETERS['ProjectCompleter'],
        default_flag='--project',
    )
    self.project_number = self._Add(
        'project_number',
        help_text=(
            'This property is for tests only. It should be kept in sync '
            'with core/project.'
        ),
        internal=True,
        hidden=True,
    )

    self.universe_domain = self._Add(
        'universe_domain',
        help_text='Sets the domain of the universe to use for API requests.',
        default='googleapis.com',
    )

    self.credentialed_hosted_repo_domains = self._Add(
        'credentialed_hosted_repo_domains', hidden=True
    )

    def ConsoleLogFormatValidator(console_log_format):
      if console_log_format is None:
        return
      if console_log_format not in ['standard', 'detailed']:
        raise InvalidValueError(
            'console_log_format must be one of: [standard, detailed]'
        )

    self.console_log_format = self._Add(
        'console_log_format',
        choices=['standard', 'detailed'],
        default='standard',
        validator=ConsoleLogFormatValidator,
        help_text=textwrap.dedent("""\
        Control the format used to display log messages to the console.
        +
        Valid values are:
            *   `standard` - Simplified log messages are displayed on the console.
            *   `detailed` - More detailed messages are displayed on the console.
        +
        If unset, default is `standard`."""),
    )

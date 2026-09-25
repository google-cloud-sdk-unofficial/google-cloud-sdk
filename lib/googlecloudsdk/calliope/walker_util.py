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

"""A collection of CLI walkers."""


import collections
import io
import os

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.calliope import markdown
from googlecloudsdk.calliope import walker
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.document_renderers import render_document
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import pkg_resources
import six


_HELP_HTML_DATA_FILES = [
    'favicon.ico',
    'index.html',
    '_menu_.css',
    '_menu_.js',
    '_title_.html',
]

_FLATTENING_TRACKS = ['alpha', 'beta', 'preview']


class DevSiteGenerator(walker.Walker):
  """Generates DevSite reference HTML in a directory hierarchy.

  This implements gcloud meta generate-help-docs --devsite-dir=DIRECTORY.

  Attributes:
    _directory: The DevSite reference output directory.
    _nodes: List of (command_path_tuple, is_group) for every visited node during
      the walk; the TOC/book structure is derived from it in Done().
    _top_level_items: List of (path, is_group) for the "flattening" items: the
      depth-1 groups/commands and the depth-2 groups/commands under the
      alpha/beta/preview tracks. Used to pick each page's _book.yaml sidebar and
      to decide which groups get a _book.yaml.
  """

  _REFERENCE = '/sdk/gcloud/reference'  # TOC reference directory offset.
  _TOC = '_toc.yaml'
  _BOOK = '_book.yaml'

  def __init__(
      self, cli, directory, hidden=False, progress_callback=None, restrict=None
  ):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      directory: The devsite output directory path name.
      hidden: Boolean indicating whether to consider the hidden CLI.
      progress_callback: f(float), The function to call to update the progress
        bar or None for no progress bar.
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups.
    """
    super(DevSiteGenerator, self).__init__(
        cli, progress_callback=progress_callback, restrict=restrict)
    self._directory = directory
    files.MakeDir(self._directory)
    self._top_level_items = []
    self._nodes = []

  def Visit(self, node, parent, is_group):
    """Renders a DevSite doc for each node and collects TOC/Book data.

    Args:
      node: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if node is a group, otherwise its is a command.

    Returns:
      The parent value, ignored here.
    """
    command = node.GetPath()
    depth = len(command) - 1
    # Flattening points: depth 1, and depth 2 under alpha/beta/preview groups.
    is_flattening_item = depth == 1 or (
        depth == 2 and command[1] in _FLATTENING_TRACKS
    )
    if is_flattening_item:
      item_path = '/'.join(command[1:])
      if (item_path, is_group) not in self._top_level_items:
        self._top_level_items.append((item_path, is_group))

    # Set up the destination dir for this level.
    if is_group:
      directory = os.path.join(self._directory, *command[1:])
      files.MakeDir(directory, mode=0o755)
    else:
      directory = os.path.join(self._directory, *command[1:-1])

    # Determine book_path for group-specific sidebar.
    book_path = '/sdk/_book.yaml'
    if len(command) > 1:
      # Prefer deeper flattening groups (depth 2 for alpha/beta)
      if len(command) > 2 and command[1] in _FLATTENING_TRACKS:
        sub_group = '/'.join(command[1:3])
        if (sub_group, True) in self._top_level_items:
          book_path = '/'.join([self._REFERENCE, sub_group, self._BOOK])

      # Fallback to top-level flattening group
      if book_path == '/sdk/_book.yaml':
        top_item = command[1]
        if (top_item, True) in self._top_level_items:
          book_path = '/'.join([self._REFERENCE, top_item, self._BOOK])

    # Render the DevSite document.
    path = (
        os.path.join(directory, 'index' if is_group else command[-1]) + '.html'
    )

    # Currently, devsite pages from GDU are automatically mirrored to all other
    # universes. To display Universe Disclaimer Information section correctly on
    # all universes after mirroring, temporarily override universe_domain
    # property to force the info section generated in devsite pages.
    universe_domain = None
    if properties.VALUES.core.universe_domain.IsExplicitlySet():
      universe_domain = properties.VALUES.core.universe_domain.Get()
    properties.VALUES.core.universe_domain.Set('universe')

    with files.FileWriter(path) as f:
      md = markdown.Markdown(node)
      render_document.RenderDocument(
          style='devsite',
          title=' '.join(command),
          fin=io.StringIO(md),
          out=f,
          command_node=node,
          book_path=book_path,
      )

    # reset universe_domain
    properties.VALUES.core.universe_domain.Set(universe_domain)

    # Collect data for _toc.yaml / _book.yaml generation in Done().
    self._nodes.append((tuple(command), is_group))
    return parent

  def Done(self):
    """Builds all _toc.yaml and _book.yaml files from the collected nodes."""
    nodes = sorted(self._nodes)
    children_by_parent = collections.defaultdict(list)
    for command, _ in nodes:
      if len(command) > 1:
        children_by_parent[command[:-1]].append(command)

    self._WriteTocFiles(nodes, children_by_parent)
    self._WriteBookFiles()

  def _RefPath(self, command):
    """Returns the devsite reference path for a command path tuple."""
    return '/'.join([self._REFERENCE, *command[1:]])

  def _WriteYaml(self, path, data):
    """Serializes data to path as a DevSite YAML file."""
    with files.FileWriter(path) as f:
      f.write(yaml.dump(data, round_trip=True))

  def _BuildTocSubtree(self, command, children_by_parent):
    """Recursively builds a nested TOC entry for command and its descendants.

    Args:
      command: The command path tuple for this entry.
      children_by_parent: {command_tuple: [child_command_tuple, ...]} in sorted
        order.

    Returns:
      An ordered mapping TOC entry with 'title', 'path', and (if the node has
      children) a nested 'section' list.
    """
    entry = collections.OrderedDict(
        title=yaml.DoubleQuotedScalarString(command[-1]),
        path=self._RefPath(command),
    )
    children = children_by_parent.get(command)
    if children:
      entry['section'] = [
          self._BuildTocSubtree(c, children_by_parent) for c in children]
    return entry

  def _WriteTocFiles(self, nodes, children_by_parent):
    """Writes the root, per-track, and per-group modular _toc.yaml files.

    Args:
      nodes: Sorted list of (command_tuple, is_group) for every visited node.
      children_by_parent: {command_tuple: [child_command_tuple, ...]} in sorted
        order.
    """
    # Root _toc.yaml: flat links to every depth-1 command/group.
    root_section = [
        collections.OrderedDict(
            title=yaml.DoubleQuotedScalarString('gcloud %s' % command[1]),
            path=self._RefPath(command),
        )
        for command, _ in nodes
        if len(command) == 2
    ]
    self._WriteYaml(
        os.path.join(self._directory, self._TOC),
        collections.OrderedDict(
            toc=[
                collections.OrderedDict(
                    title=yaml.DoubleQuotedScalarString('gcloud Reference'),
                    path=self._REFERENCE,
                    section=root_section,
                )
            ]
        ),
    )

    # Each depth-1 group and each depth-2 group under a track gets its own
    # modular _toc.yaml. Every other group is nested inside an ancestor's file.
    for command, is_group in nodes:
      if not is_group:
        continue
      depth = len(command) - 1
      toc_path = os.path.join(
          self._directory, *command[1:], self._TOC)
      if depth == 1 and command[1] in _FLATTENING_TRACKS:
        # Track TOC: flat links to its depth-2 items. Each depth-2 group gets
        # its own modular file in a separate iteration of this loop.
        item = collections.OrderedDict(
            title=yaml.DoubleQuotedScalarString('gcloud %s' % command[1]),
            path=self._RefPath(command),
        )
        entries = [
            collections.OrderedDict(
                title=yaml.DoubleQuotedScalarString(child[-1]),
                path=self._RefPath(child),
            )
            for child in children_by_parent.get(command, [])
        ]
        if entries:
          item['section'] = entries
        self._WriteYaml(toc_path, collections.OrderedDict(toc=[item]))
      elif depth == 1:
        # Non-track top-level group: a single fully-nested modular TOC.
        item = self._BuildTocSubtree(command, children_by_parent)
        item['title'] = yaml.DoubleQuotedScalarString(
            'gcloud %s' % command[1]
        )
        self._WriteYaml(toc_path, collections.OrderedDict(toc=[item]))
      elif depth == 2 and command[1] in _FLATTENING_TRACKS:
        # Flattened subgroup under a track: its own fully-nested modular TOC.
        item = self._BuildTocSubtree(command, children_by_parent)
        self._WriteYaml(toc_path, collections.OrderedDict(toc=[item]))

  def _WriteBookFiles(self):
    """Writes a _book.yaml sidebar for every flattening group."""
    roots = sorted(
        path for path, _ in self._top_level_items if '/' not in path)
    groups = sorted(
        path for path, is_group in self._top_level_items if is_group)
    track_subgroups = collections.defaultdict(list)
    for sub, _ in self._top_level_items:
      parts = sub.split('/')
      if len(parts) == 2 and parts[0] in _FLATTENING_TRACKS:
        track_subgroups[parts[0]].append(sub)
    for track in track_subgroups:
      track_subgroups[track].sort()

    for group in groups:
      book_path = os.path.join(
          self._directory, *group.split('/'), self._BOOK)
      contents = (
          '# WARNING: THIS FILE IS AUTO-GENERATED, DO NOT EDIT\n'
          'extends: /docs/_book.yaml\n\n'
          + yaml.dump(
              self._BuildBookData(group, roots, track_subgroups),
              round_trip=True,
          )
      )
      with files.FileWriter(book_path) as f:
        f.write(contents)

  def _BuildBookData(self, group, roots, track_subgroups):
    """Builds the structured _book.yaml document for the given group.

    Args:
      group: The flattening group path (e.g. 'ai' or 'alpha/compute') whose
        sidebar is being generated.
      roots: Sorted list of the depth-1 item paths.
      track_subgroups: {track: [subgroup_path, ...]}.

    Returns:
      An ordered mapping representing the _book.yaml 'upper_tabs' document (the
      leading comment and 'extends' preamble are written separately).
    """
    section = []
    for root in roots:
      if root == group:
        # Active top-level group: expand its modular TOC.
        section.append(
            collections.OrderedDict(
                include='/'.join([self._REFERENCE, root, self._TOC])
            )
        )
      else:
        entry = collections.OrderedDict(
            title=yaml.DoubleQuotedScalarString('gcloud %s' % root),
            path='/'.join([self._REFERENCE, root]),
        )
        if root in _FLATTENING_TRACKS and group.startswith(root + '/'):
          # The active group lives under this track: list its sibling subgroups
          # and expand the active one.
          sub_entries = []
          for sub in track_subgroups.get(root, []):
            if sub == group:
              sub_entries.append(
                  collections.OrderedDict(
                      include='/'.join([self._REFERENCE, sub, self._TOC])
                  )
              )
            else:
              sub_entries.append(
                  collections.OrderedDict(
                      title=yaml.DoubleQuotedScalarString(sub.split('/')[-1]),
                      path='/'.join([self._REFERENCE, sub]),
                  )
              )
          entry['section'] = sub_entries
        section.append(entry)

    reference_contents = [
        collections.OrderedDict(
            heading=yaml.DoubleQuotedScalarString('Cloud Client Libraries')
        ),
        collections.OrderedDict(
            title=yaml.DoubleQuotedScalarString(
                'Cloud Client Libraries references'
            ),
            path='/sdk/docs/libraries-reference',
        ),
        collections.OrderedDict(
            heading=yaml.DoubleQuotedScalarString('Google Cloud CLI')
        ),
        collections.OrderedDict(
            title=yaml.DoubleQuotedScalarString('gcloud Reference'),
            path=self._REFERENCE,
            section=section,
        ),
    ]
    lower_tabs = [
        collections.OrderedDict(
            name='Overview',
            path='/sdk/docs',
            contents=[
                collections.OrderedDict(include='/sdk/_overview_tab.yaml')
            ],
        ),
        collections.OrderedDict(
            name=yaml.DoubleQuotedScalarString('Guides'),
            path='/sdk/docs/overview',
            contents=[
                collections.OrderedDict(include='/sdk/_guides_tab.yaml')
            ],
        ),
        collections.OrderedDict(
            name=yaml.DoubleQuotedScalarString('Reference'),
            contents=reference_contents,
        ),
        collections.OrderedDict(
            name=yaml.DoubleQuotedScalarString('Resources'),
            contents=[
                collections.OrderedDict(include='/sdk/_resources_tab.yaml')
            ],
        ),
    ]
    return collections.OrderedDict(
        upper_tabs=collections.OrderedDict(
            [('global-documentation-upper',
              collections.OrderedDict(lower_tabs=lower_tabs))]
        )
    )


class HelpTextGenerator(walker.Walker):
  """Generates help text files in a directory hierarchy.

  Attributes:
    _directory: The help text output directory.
  """

  def __init__(
      self, cli, directory, hidden=False, progress_callback=None, restrict=None
  ):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      directory: The Help Text output directory path name.
      hidden: Boolean indicating whether to consider the hidden CLI.
      progress_callback: f(float), The function to call to update the progress
        bar or None for no progress bar.
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups.
    """
    super(HelpTextGenerator, self).__init__(
        cli, progress_callback=progress_callback, restrict=restrict
    )
    self._directory = directory
    files.MakeDir(self._directory)

  def Visit(self, node, parent, is_group):
    """Renders a help text doc for each node in the CLI tree.

    Args:
      node: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if node is a group, otherwise its is a command.

    Returns:
      The parent value, ignored here.
    """
    # Set up the destination dir for this level.
    command = node.GetPath()

    if is_group:
      directory = os.path.join(self._directory, *command[1:])
    else:
      directory = os.path.join(self._directory, *command[1:-1])

    files.MakeDir(directory, mode=0o755)
    # Render the help text document.
    path = os.path.join(directory, 'GROUP' if is_group else command[-1])
    with files.FileWriter(path) as f:
      md = markdown.Markdown(node)
      render_document.RenderDocument(style='text', fin=io.StringIO(md), out=f)
    return parent


class DocumentGenerator(walker.Walker):
  """Generates style manpage files with suffix in an output directory.

  All files will be generated in one directory.

  Attributes:
    _directory: The document output directory.
    _style: The document style.
    _suffix: The output file suffix.
  """

  def __init__(self, cli, directory, style, suffix, progress_callback=None,
               restrict=None):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      directory: The manpage output directory path name.
      style: The document style.
      suffix: The generate document file suffix. None for .<SECTION>.
      progress_callback: f(float), The function to call to update the progress
        bar or None for no progress bar.
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups.
    """
    super(DocumentGenerator, self).__init__(
        cli, progress_callback=progress_callback, restrict=restrict)
    self._directory = directory
    self._style = style
    self._suffix = suffix
    files.MakeDir(self._directory)

  def Visit(self, node, parent, is_group):
    """Renders document file for each node in the CLI tree.

    Args:
      node: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if node is a group, otherwise its is a command.

    Returns:
      The parent value, ignored here.
    """

    if self._style == 'linter':
      meta_data = actions.GetCommandMetaData(node)
    else:
      meta_data = None
    command = node.GetPath()
    path = os.path.join(self._directory, '_'.join(command)) + self._suffix
    with files.FileWriter(path) as f:
      md = markdown.Markdown(node)
      render_document.RenderDocument(
          style=self._style,
          title=' '.join(command),
          fin=io.StringIO(md),
          out=f,
          command_metadata=meta_data,
      )
    return parent


class HtmlGenerator(DocumentGenerator):
  """Generates HTML manpage files with suffix .html in an output directory.

  The output directory will contain a man1 subdirectory containing all of the
  HTML manpage files.
  """

  def WriteHtmlMenu(self, command, out):
    """Writes the command menu tree HTML on out.

    Args:
      command: dict, The tree (nested dict) of command/group names.
      out: stream, The output stream.
    """

    def ConvertPathToIdentifier(path):
      return '_'.join(path)

    def WalkCommandTree(command, prefix):
      """Visit each command and group in the CLI command tree.

      Args:
        command: dict, The tree (nested dict) of command/group names.
        prefix: [str], The subcommand arg prefix.
      """
      level = len(prefix)
      visibility = 'visible' if level <= 1 else 'hidden'
      indent = level * 2 + 2
      name = command.get('_name_')
      args = prefix + [name]
      out.write(
          '{indent}<li class="{visibility}" id="{item}" '
          'onclick="select(event, this.id)">{name}'.format(
              indent=' ' * indent,
              visibility=visibility,
              name=name,
              item=ConvertPathToIdentifier(args),
          )
      )
      commands = command.get('commands', []) + command.get('groups', [])
      if commands:
        out.write('<ul>\n')
        for c in sorted(commands, key=lambda x: x['_name_']):
          WalkCommandTree(c, args)
        out.write('{indent}</ul>\n'.format(indent=' ' * (indent + 1)))
        out.write('{indent}</li>\n'.format(indent=' ' * indent))
      else:
        out.write('</li>\n')

    out.write("""\
<html>
<head>
<meta name="description" content="man page tree navigation">
<meta name="generator" content="gcloud meta generate-help-docs --html-dir=.">
<title> man page tree navigation </title>
<base href="." target="_blank">
<link rel="stylesheet" type="text/css" href="_menu_.css">
<script type="text/javascript" src="_menu_.js"></script>
</head>
<body>

<div class="menu">
 <ul>
""")
    WalkCommandTree(command, [])
    out.write("""\
 </ul>
</div>

</body>
</html>
""")

  def _GenerateHtmlNav(self, directory, cli, hidden, restrict):
    """Generates html nav files in directory."""
    tree = CommandTreeGenerator(cli).Walk(hidden=hidden, restrict=restrict)
    with files.FileWriter(os.path.join(directory, '_menu_.html')) as out:
      self.WriteHtmlMenu(tree, out)
    for file_name in _HELP_HTML_DATA_FILES:
      file_contents = pkg_resources.GetResource(
          'googlecloudsdk.api_lib.meta.help_html_data.', file_name
      )
      files.WriteBinaryFileContents(
          os.path.join(directory, file_name), file_contents
      )

  def __init__(
      self, cli, directory, hidden=False, progress_callback=None, restrict=None
  ):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      directory: The HTML output directory path name.
      hidden: Boolean indicating whether to consider the hidden CLI.
      progress_callback: f(float), The function to call to update the progress
        bar or None for no progress bar.
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups.
    """
    super(HtmlGenerator, self).__init__(
        cli,
        directory=directory,
        style='html',
        suffix='.html',
        progress_callback=progress_callback,
        restrict=restrict,
    )
    self._GenerateHtmlNav(directory, cli, hidden, restrict)


class ManPageGenerator(DocumentGenerator):
  """Generates manpage files with suffix .1 in an output directory.

  The output directory will contain a man1 subdirectory containing all of the
  manpage files.
  """

  _SECTION_FORMAT = 'man{section}'

  def __init__(
      self, cli, directory, hidden=False, progress_callback=None, restrict=None
  ):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      directory: The manpage output directory path name.
      hidden: Boolean indicating whether to consider the hidden CLI.
      progress_callback: f(float), The function to call to update the progress
        bar or None for no progress bar.
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups.
    """

    # Currently all gcloud manpages are in section 1.
    section_subdir = self._SECTION_FORMAT.format(section=1)
    section_dir = os.path.join(directory, section_subdir)
    super(ManPageGenerator, self).__init__(
        cli, directory=section_dir, style='man', suffix='.1',
        progress_callback=progress_callback, restrict=restrict
    )


class LinterGenerator(DocumentGenerator):
  """Generates linter files with suffix .json in an output directory."""

  def __init__(
      self, cli, directory, hidden=False, progress_callback=None, restrict=None
  ):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      directory: The linter output directory path name.
      hidden: Boolean indicating whether to consider the hidden CLI.
      progress_callback: f(float), The function to call to update the progress
        bar or None for no progress bar.
      restrict: Restricts the walk to the command/group dotted paths in this
        list. For example, restrict=['gcloud.alpha.test', 'gcloud.topic']
        restricts the walk to the 'gcloud topic' and 'gcloud alpha test'
        commands/groups.
    """

    super(LinterGenerator, self).__init__(
        cli,
        directory=directory,
        style='linter',
        suffix='.json',
        progress_callback=progress_callback,
        restrict=restrict,
    )


class CommandTreeGenerator(walker.Walker):
  """Constructs a CLI command dict tree.

  This implements the resource generator for gcloud meta list-commands.

  Attributes:
    _with_flags: Include the non-global flags for each command/group if True.
    _with_flag_values: Include flag value choices or :type: if True.
    _global_flags: The set of global flags, only listed for the root command.
  """

  def __init__(self, cli, with_flags=False, with_flag_values=False, **kwargs):
    """Constructor.

    Args:
      cli: The Cloud SDK CLI object.
      with_flags: Include the non-global flags for each command/group if True.
      with_flag_values: Include flags and flag value choices or :type: if True.
      **kwargs: Other keyword arguments to pass to Walker constructor.
    """
    super(CommandTreeGenerator, self).__init__(cli, **kwargs)
    self._with_flags = with_flags or with_flag_values
    self._with_flag_values = with_flag_values
    self._global_flags = set()

  def Visit(self, node, parent, is_group):
    """Visits each node in the CLI command tree to construct the dict tree.

    Args:
      node: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if node is a group, otherwise its is a command.

    Returns:
      The subtree parent value, used here to construct a dict tree.
    """
    name = node.name.replace('_', '-')
    info = {'_name_': name}
    if self._with_flags:
      all_flags = []
      for arg in node.GetAllAvailableFlags():
        value = None
        if self._with_flag_values:
          if arg.choices:
            choices = sorted(arg.choices)
            if choices != ['false', 'true']:
              value = ','.join([six.text_type(choice) for choice in choices])
          elif isinstance(arg.type, int):
            value = ':int:'
          elif isinstance(arg.type, float):
            value = ':float:'
          elif isinstance(arg.type, arg_parsers.ArgDict):
            value = ':dict:'
          elif isinstance(arg.type, arg_parsers.ArgList):
            value = ':list:'
          elif arg.nargs != 0:
            metavar = arg.metavar or arg.dest.upper()
            value = ':' + metavar + ':'
        for f in arg.option_strings:
          if value:
            f += '=' + value
          all_flags.append(f)
      no_prefix = '--no-'
      flags = []
      for flag in all_flags:
        if flag in self._global_flags:
          continue
        if flag.startswith(no_prefix):
          positive = '--' + flag[len(no_prefix) :]
          if positive in all_flags:
            continue
        flags.append(flag)
      if flags:
        info['_flags_'] = sorted(flags)
        if not self._global_flags:
          # Most command flags are global (defined by the root command) or
          # command-specific. Group-specific flags are rare. Separating out
          # the global flags streamlines command descriptions and prevents
          # global flag changes (we already have too many!) from making it
          # look like every command has changed.
          self._global_flags.update(flags)
    if is_group:
      if parent:
        if cli_tree.LOOKUP_GROUPS not in parent:
          parent[cli_tree.LOOKUP_GROUPS] = []
        parent[cli_tree.LOOKUP_GROUPS].append(info)
      return info
    if cli_tree.LOOKUP_COMMANDS not in parent:
      parent[cli_tree.LOOKUP_COMMANDS] = []
    parent[cli_tree.LOOKUP_COMMANDS].append(info)
    return None


class GCloudTreeGenerator(walker.Walker):
  """Generates an external representation of the gcloud CLI tree.

  This implements the resource generator for gcloud meta list-gcloud.
  """

  def Visit(self, node, parent, is_group):
    """Visits each node in the CLI command tree to construct the external rep.

    Args:
      node: group/command CommandCommon info.
      parent: The parent Visit() return value, None at the top level.
      is_group: True if node is a group, otherwise its is a command.

    Returns:
      The subtree parent value, used here to construct an external rep node.
    """
    return cli_tree.Command(node, parent)

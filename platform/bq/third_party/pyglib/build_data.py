# Copyright 2005 Google Inc.
# All Rights Reserved.
#
# Author: roth@google.com (Mark D. Roth), dgreiman@google.com (Douglas Greiman)

"""Access to google3 build data.

This module allows access to build data produced by Blaze when it compiles a
.par file. This is the Python analogue of the C++ build stamp headers and the
Java deploy jar's build-data.properties file. Data may include information
such as the CL and time at which the target was last built, the Sponge ID of the
build which created the target, and the user, client, and workspace from which
the build was invoked.
"""

import io
import sys
import time
from typing import Optional

from pyglib import resources

try:
  from google.base.python.clif import googleinit  # pylint: disable=g-import-not-at-top  # pytype: disable=import-error
except ImportError:
  googleinit = None


# Global data
_build_dict = None


def _ParseBuildData(filename: str) -> dict[str, str]:
  """Read Blaze-stamped build data from external file.

  Uses default values if build data file not available.

  Args:
    filename:  The path to the resource from which to read.

  Returns:
    A dictionary of build data info.
  """

  # Start with empty defaults
  build_data = {
      'BUILDINFO': '',
      'BUILDLABEL': '',
      'BUILDTOOL': '',
      'CHANGELIST': '-1',
      'BASELINECHANGELIST': '-1',
      'CLIENTNAME': '',
      'CLIENTSTATUS': '-2',
      'DEPOTPATH': '',
      'PAROPTIONS': '',
      'PLATFORM': '',
      'TARGET': '',
      'TIMESTAMP': '',
      'VERSIONMAP': '',
      }

  # Read generated build info if available
  try:
    build_data_str = resources.GetResource(filename).decode()
    # Parse as key/value pairs
    for line in build_data_str.splitlines():
      # Skip comments, blanks, and syntax errors
      if line.startswith('#') or not line.strip() or ':' not in line:
        continue

      key, value = line.split(':', 1)
      build_data[key] = value
  except IOError:
    # Build data not available. Most of time we don't need this info. However,
    # if you do need build data, you might want to check if --nostamp is
    # provided in your blazerc file.
    pass
  except Exception as unexpected_error:  # pylint: disable=broad-except
    # Tolerate other errors as well, but dump the error info to the log.
    #
    # NOTE: Errors parsing build data are somewhat more common when using
    # g3process with a .par file on borg since forked processes will share the
    # file descriptor (and file offset) for the .par file which can mess up file
    # reads.  The resulting ValueError is safe to ignore since the BUILD info
    # for the child processes is the same as for the parent and will have been
    # logged at startup.  See b/117880794 for more info.
    print('\nUnexpected error parsing build data from \'{}\': {}\n'.format(
        filename, unexpected_error), file=sys.stderr)

  return build_data


def _GetBuildData() -> dict[str, str]:
  """Read build data from external file, if not already read."""
  global _build_dict  # pylint: disable=global-statement
  if _build_dict is None:
    _build_dict = _ParseBuildData('google3/pyglib/build_data.txt')
  return _build_dict


def BuildInfo() -> str:
  """Return user, host, and directory of builder, as string."""
  return _GetBuildData().get('BUILDINFO', '')


def BuildLabel() -> str:
  """Return build label (passed to make-{opt,dbg} -l) as string."""
  return _GetBuildData().get('BUILDLABEL', '')


def BuildTool() -> str:
  """Return the build tool as string if we know it."""
  return _GetBuildData().get('BUILDTOOL', '')


def BuildID() -> str:
  """Return the build ID of the invocation which built the binary, if known."""
  return _GetBuildData().get('BUILDID', '')


def Changelist() -> int:
  """Return client workspace changelist, as int."""
  cl = _GetBuildData().get('CHANGELIST', '')
  try:
    changelist = int(cl.strip())
  except ValueError:
    changelist = -1
  return changelist


def BaselineChangelist() -> int:
  """Return the mainline CL number from which this was built.

  Returns:
    If built from a branch, the CL of mainline (//depot/google3) on which the
    branch was based, otherwise the same as `Changelist()`.
  """
  cl = _GetBuildData().get('BASELINECHANGELIST', '')
  try:
    changelist = int(cl.strip())
  except ValueError:
    changelist = -1
  return changelist


def CitcSnapshot() -> str:
  """Return CitC Snapshot number, as string."""
  citc_snapshot = _GetBuildData().get('CITCSNAPSHOT', '')
  if citc_snapshot == 'null':
    return ''
  return citc_snapshot


def CitcWorkspaceId() -> str:
  """Return CitC Workspace ID, as string, like whoami/123."""
  citc_workspace_id = _GetBuildData().get('CITCWORKSPACEID', '')
  return '' if citc_workspace_id == 'null' else citc_workspace_id


def SourceUri() -> str:
  """Return go/source-uri, as string."""
  return _GetBuildData().get('SOURCEURI', '')


def ClientName() -> str:
  """Return Perforce client name, as string."""
  return _GetBuildData().get('CLIENTNAME', '')


def ClientStatus() -> int:
  """Return Perforce client status, as int."""
  tmp_str = _GetBuildData().get('CLIENTSTATUS', '')
  try:
    status = int(tmp_str)
  except ValueError:
    status = -1
  return status


def DepotPath() -> str:
  """Return Perforce depot path, as string."""
  return _GetBuildData().get('DEPOTPATH', '')


def ParOptions() -> str:
  """Return list of autopar options, as string."""
  return _GetBuildData().get('PAROPTIONS', '')


def Platform() -> str:
  """Return google platform as string."""
  return _GetBuildData().get('PLATFORM', '')


def Target() -> str:
  """Return build target as string."""
  return _GetBuildData().get('TARGET', '')


def Timestamp() -> int:
  """Return timestamp in seconds since the Epoch, as int."""
  ts = _GetBuildData().get('TIMESTAMP', '')
  try:
    timestamp = int(ts.strip())
  except ValueError:
    timestamp = -1
  return timestamp


def TimestampAscii() -> str:
  """Return timestamp as a string: May 12 2009 13:59:22 (1242161962)."""
  timestamp = Timestamp()
  timestamp_str = ('%s (%d)' %
                   (time.asctime(time.localtime(timestamp)), timestamp))
  return timestamp_str


def Verifiable() -> int:
  """Return the value of VERIFIABLE, as integer."""
  verifiable = _GetBuildData().get('VERIFIABLE', '0')
  try:
    return int(verifiable)
  except ValueError:
    return 0


def VersionMap() -> str:
  """Return the map from VERSION_MAP as string."""
  vm = _GetBuildData().get('VERSIONMAP', '')
  if 'client_view {' in vm:
    return vm[:vm.index('client_view {') - 1].strip(',')
  else:
    return vm


def FullVersionMap() -> str:
  """Return VERSION_MAP as string, including the client_view."""
  return _GetBuildData().get('VERSIONMAP', '')


def BuildDebugMode() -> Optional[bool]:
  """Returns whether NDEBUG was defined when it has C++ deps, None otherwise."""
  return not googleinit.IsNDebugDefined() if googleinit else None


def ClientInfo() -> str:
  """Return Perforce client changelist and status as descriptive string."""
  info = ''
  cl = Changelist()
  vm = VersionMap()
  citc_snapshot = CitcSnapshot()
  build_client = ClientName()
  if vm:
    cs = ClientStatus()
    dp = DepotPath()
    if cs == 1:
      status_info = ' in a mint Components client based on %s' % dp
    elif cs == 0:
      status_info = ' in a modified Components client based on %s' % dp
    else:
      status_info = ' in a possibly-modified Components client'
    if citc_snapshot:
      status_info += ' in CitC workspace %s at snapshot %s' % (
          build_client, citc_snapshot)
    info = 'version map "%s"%s' % (vm, status_info)
    if cl > 0 and '/branches/' in dp:
      info += ' at branch changelist %d' % cl
  else:
    if cl == -1:
      info = ''
    elif cl == 0:
      info = 'unknown changelist'
    else:
      cs = ClientStatus()
      dp = DepotPath()
      if cs == 1:
        status_info = ' in a mint client based on %s' % dp
      elif cs == 0:
        status_info = ' in a modified client based on %s' % dp
      else:
        status_info = ' possibly in a modified client'
      if citc_snapshot:
        status_info += ' in CitC workspace %s at snapshot %s' % (
            build_client, citc_snapshot)
      info = 'changelist %d%s' % (cl, status_info)

  return info


def BuildData() -> str:
  """Return all build data as a nicely formatted string."""
  buf = io.StringIO()

  buf.write('Built on %s\n' % TimestampAscii())

  buf.write('Built by %s\n' % BuildInfo())

  buf.write('Built as %s\n' % Target())

  buildid = BuildID()
  if buildid:
    buf.write('Build ID: %s\n' % buildid)

  clientinfo = ClientInfo()
  if clientinfo:
    buf.write('Built from %s\n' % clientinfo)

  buildlabel = BuildLabel()
  if buildlabel:
    buf.write('Build label: %s\n' % buildlabel)

  buf.write('Build platform: %s\n' % Platform())

  buildtool = BuildTool()
  if buildtool:
    buf.write('Build tool: %s\n' % buildtool)

  paropts = ParOptions()
  if paropts:
    buf.write('Built with par options %s\n' % paropts)

  buf.write(
      'Currently running under Python {0}: {1}\n'.format(
          sys.version, sys.executable if sys.executable else 'embedded.'
      )
  )

  data_str = buf.getvalue()
  buf.close()

  return data_str

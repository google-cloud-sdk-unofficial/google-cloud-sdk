"""Library to send syslog messages used by ToolSearch.

These logs are collected to identify used (vs obsolete) binaries. See
https://goto.google.com/toolsearchlogging.
"""

# Import may fail if platform is not unix.
try:  # pylint: disable=g-statement-before-imports
  import syslog  # pylint: disable=g-import-not-at-top
except ImportError:
  syslog = None

import os
import socket
import stat
import struct
import sys
import time

from absl import flags

from pyglib import build_data

SYSLOG_ON_START = flags.DEFINE_boolean(
    'syslog_on_start',
    True,
    'syslog() on program start-up.  We collect these logs to '
    'identify used (vs obsolete) binaries.',
    allow_override=True,
    allow_override_cpp=True,
)

LOG_UNHASHED_ARGV = flags.DEFINE_boolean(
    'log_unhashed_argv',
    False,
    'Log args in cleartext. Make sure there is no security implication.',
)


# Address used to communicate tool logging messages to the local crudd daemon.
# Names starting with a NUL character are created in the abstract namespace.
# See man 7 unix.
# The read side of the socket is in //devtools/diagnostics/crudd:tool_logger.
# The corresponding C++ definition of this port is in //base/syslog_util.cc.
_TOOL_LOGGER_PORT = '\0google-toollogger-crudd'

# Installed location of the crudd binary used as a proxy for logging
# tool usage.
_TOOL_LOGGER_BINARY = '/usr/sbin/crudd'


def _DoesSocketBinaryPathMatchExpectedPath(sock, expected_path):
  """Return True if the path of sock's binary matches expected_path.

  This check can be used to validate that communication over an open socket
  is with the intended receiving binary, not a rogue that has taken over
  the socket address.  It only works on local (AF_UNIX) sockets.  For other
  socket types, it will always return false.
  This function will determine the pid of the open file descriptor,
  examine the file /proc/<pid>/cmdline, and compare the binary path
  listed there against expected_path.

  Args:
    sock: Open AF_UNIX socket connection.
    expected_path: Expected path of the listening binary.

  Returns:
    True if the path of socket_fd's binary matches expected_path.
  """
  so_peercred = getattr(socket, 'SO_PEERCRED', None)
  if so_peercred is None:
    architecture = os.uname()[4]
    if architecture == 'ppc64le':
      so_peercred = 21  # From Power PC /usr/include/asm/socket.h
    else:
      so_peercred = 17  # From /usr/include/asm-generic/socket.h
  pid, _, _ = struct.unpack(
      '3i',
      sock.getsockopt(socket.SOL_SOCKET, so_peercred, struct.calcsize('3i')),
  )
  if pid == 0:  # Can happen if the socket wasn't connected.
    return False
  infile = None
  try:
    try:
      # /proc/<pid>/cmdline contains the running location of the process to
      # communicate with.
      with open('/proc/%d/cmdline' % pid, 'r') as infile:
        # According to "man 5 proc", the command line arguments are
        # null-separated.
        sock_argv0 = infile.readline().split('\x00', 1)[0]
        return expected_path == sock_argv0
    except (IOError, IndexError):
      pass
  finally:
    if infile:
      infile.close()
  return False


def _SendSyslogByProxy(
    syslog_msg,
    blocking=False,
    socket_path=_TOOL_LOGGER_PORT,
    crudd_binary_path=_TOOL_LOGGER_BINARY,
):
  """Send a tool logging message to the crudd logging proxy.

  Args:
    syslog_msg: byte string or unicode - Message to write to syslog.
    blocking: boolean - If True, block until the message has been written.
    socket_path: string - Socket address to write to.
    crudd_binary_path: string - Installed location of the crudd tool_logger
      binary used as a proxy for syslog messages.  In production, this should be
      None when sending a message to syslog directly (w/o crudd) or should be
      _TOOL_LOGGER_BINARY.  Any other value is only used for the purpose of
      testing.

  Returns:
    True if the message was sent.
  """
  sendflags = 0
  if not blocking:
    sendflags |= socket.MSG_DONTWAIT
  # SOCK_DGRAM is needed when sending to syslog directly
  # SOCK_STREAM is needed when using abstract namespace
  for sock_type in (socket.SOCK_DGRAM, socket.SOCK_STREAM):
    fd = None
    try:
      try:
        fd = socket.socket(socket.AF_UNIX, sock_type)
        fd.connect(socket_path)
        if not crudd_binary_path or _DoesSocketBinaryPathMatchExpectedPath(
            fd, crudd_binary_path
        ):
          # This encode is needed for Python 3 but works fine in >= 2.6.
          if sys.version_info >= (2, 6) and not isinstance(syslog_msg, bytes):
            syslog_msg = syslog_msg.encode('utf-8')
          fd.sendall(syslog_msg, sendflags)
          return True
        break
      except socket.error:
        continue
    finally:
      if fd is not None:
        fd.close()
  return False


def ValidateIsTimeToSyslog(binary_name, checkpoint_parent_dir='/tmp'):
  """Validate whether to syslog on startup.

  To avoid excessive logging, we create a directory
  '/tmp/initgoogle_syslog_dir.uid'.  We touch a file named binary_name
  (munged to be a legal filesystem name) in that directory, every time
  we syslog.  If this binary_name file is already there and is less
  than a day old, we don't log.

  Args:
    binary_name: string - Name of the binary to write to the syslog.
    checkpoint_parent_dir: string - Path of the directory where checkpoint files
      should be stored.

  Returns:
    True if this run should be syslogged.
  """
  checkpoint_dir = os.path.join(
      checkpoint_parent_dir, 'initgoogle_syslog_dir.%d' % os.getuid()
  )
  # Munge binary_name to make it safe for a filename.
  munged_binary_name = binary_name.replace('/', '_')
  munged_binary_name = munged_binary_name.replace('.', '_')
  checkpoint_filename = os.path.join(checkpoint_dir, munged_binary_name)
  if not os.path.exists(checkpoint_dir):
    try:
      os.mkdir(checkpoint_dir, 0o700)
    except OSError:
      return False  # unable to create checkpoint dir

  statinfo = os.stat(checkpoint_dir)
  if (
      statinfo.st_uid != os.getuid()  # not owned by me
      or not stat.S_ISDIR(statinfo[stat.ST_MODE])  # not a directory
      or statinfo[stat.ST_MODE] & 0o777 != stat.S_IRWXU  # surprising perms
  ):
    return False
  if os.path.exists(checkpoint_filename):  # logged
    statinfo = os.stat(checkpoint_filename)
    if statinfo.st_mtime >= time.time() - 86400:  # logged recently
      return False

  # Update the checkpoint file to say we will syslog this time.
  try:
    with open(checkpoint_filename, 'w'):
      pass
  except IOError:
    return False  # unable to create the file

  return True


def _GetDefaultLogPath():
  """Return the default value for the log_path proto field for tool logging."""
  log_path = build_data.Target()  # will only be set for compiled targets
  if not log_path:
    log_path = sys.argv[0]
  return log_path


def _ProtoValueToString(key, value):
  """Convert a key, value pair into an ascii proto string.

  Only guaranteed to handle data types used by the ToolLog proto.

  Args:
    key: Proto field name
    value: Proto field value (may be a list or dictionary)

  Returns:
    String representation of the key, value pair in ascii proto format.
  """
  if isinstance(value, list):
    return ' '.join(_ProtoValueToString(key, v) for v in value)
  elif isinstance(value, dict):
    value = '{%s}' % _ProtoDictToString(value)
  # 'os' is known to be an enum and should not be escaped:
  elif isinstance(value, str) and key != 'os':
    value = '"%s"' % value.replace('"', r'\x22')
  return '%s:%s' % (key, str(value))


def _ProtoDictToString(proto_dict):
  """Convert a dictionary of key,value pairs into an ascii proto string.

  Only guaranteed to handle data types used by the ToolLog proto.

  Args:
    proto_dict: Dictionary representing the proto
      google3/devtools/toolindex/logger/tool_log.proto.

  Returns:
    String representation of the dict in ascii proto format.
  """
  parts = [_ProtoValueToString(k, v) for k, v in proto_dict.items()]
  proto_string = ' '.join(parts)
  return proto_string


def _GetToolLogProtoString(proto_dict, include_argv=True):
  """Return the ToolLog ascii proto string to syslog.

  Augments proto_dict with default values for certain fields that aren't
  specified and ensures that the returned ascii proto string can be
  sent to syslog.

  Args:
    proto_dict: Dictionary representing the proto
      google3/devtools/toolindex/logger/tool_log.proto.
    include_argv: Boolean.  If True, include argv in the proto string.  We only
      want to include it when logging usage via the crudd proxy, since it
      handles sanitization of potentially sensitive data.

  Returns:
    String representation of the dict in ascii proto format.
  """
  proto_dict_with_defaults = {
      'log_timestamp': int(time.time()),
      'uid': os.getuid(),
      'build_timestamp': build_data.Timestamp(),
      'host_name': socket.gethostname(),
      'log_path': _GetDefaultLogPath(),
      'language': 'py',
      'tool_type': 'cmdline',
      'logger': 'syslog_py',
      'argv': sys.argv[1:],
      'os': _LoggedOS(),
  }
  term_program = os.environ.get('TERM_PROGRAM')
  if term_program:
    proto_dict_with_defaults['term_program'] = term_program
  proto_dict_with_defaults.update(proto_dict)

  if not include_argv:
    proto_dict_with_defaults.pop('argv', None)
  proto_string = _ProtoDictToString(proto_dict_with_defaults)
  # Newline characters cause the syslog message to terminate prematurely
  return proto_string.replace('\n', ' ')


def _LoggedOS():
  """Returns the logs.normaleyes.Platform.OS enum value for the current OS."""
  if sys.platform.startswith('linux'):
    return 'LINUX_OS'
  elif sys.platform.startswith('darwin'):
    return 'MAC_OS'
  elif sys.platform.startswith('win32'):
    return 'WINDOWS'
  else:
    return 'UNSPECIFIED'


def MaybeSyslogOnStart(proto_dict=None):
  """Send a syslog message stating that this target was run.

  We collect these logs to identify used (vs obsolete) binaries.
  http://goto/toolsearchlogging

  Args:
    proto_dict: Dict representing devtools/toolindex/logger/tool_log.proto. Keys
      are the proto fields, values are the proto values.  For repeated fields,
      values should be a list (which again may contain single values or
      dictionaries depending on the repeated field type) For any fields not
      specified, sensible default information will be added.  See
      http://goto/toolsearchlogging for more details.
  """
  if syslog is None or not SYSLOG_ON_START.value:
    return
  proto_dict = proto_dict or {}
  hostname = socket.gethostname()
  # TODO(b/203587095): Update hostname check when w.googlers.com is in use.
  on_corp = hostname.endswith(('.corp.google.com', '.c.googlers.com'))

  proto_string = _GetToolLogProtoString(proto_dict)

  syslog_msg = 'ToolLogProto %s' % proto_string
  # We log initially to the crudd tool_logger which does additional filtering
  # before the final write to syslog.
  if not LOG_UNHASHED_ARGV.value and on_corp and _SendSyslogByProxy(syslog_msg):
    # Logging to crudd succeeded, finished.
    return

  # In Prod or logging to crudd failed. Fallback to logging directly to syslog
  # (with argv removed) so we don't lose data for users who aren't
  # running crudd. We have to provide a more detailed message in this
  # case since the crudd binary won't be adding additional details for us.
  # We also have to provide our own rate limiting (both Corp & Prod).
  if not LOG_UNHASHED_ARGV.value and not ValidateIsTimeToSyslog(
      _GetDefaultLogPath()
  ):
    return

  clean_proto_string = _GetToolLogProtoString(
      proto_dict, include_argv=LOG_UNHASHED_ARGV.value
  )
  # According to hugh, the new corp syslog collection facility only
  # collects LOG_AUTH (as of 4 May 2009), so we log to that.
  # For prod, apparently we need to use AUTH or AUTHPRIV, or else
  # use LOCAL1 and have the message match "caught SIG".
  syslog_msg = '<%d>ToolLogProto logjam_tag=tattler_initgoogle %s' % (
      syslog.LOG_AUTH | syslog.LOG_INFO,
      clean_proto_string,
  )
  _SendSyslogByProxy(syslog_msg, socket_path='/dev/log', crudd_binary_path=None)

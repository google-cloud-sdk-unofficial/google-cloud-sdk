# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Direct Connectivity Diagnostic."""

import io
import ipaddress
import json
import os
import re
import socket
import tempfile

from googlecloudsdk.command_lib.storage import path_util
from googlecloudsdk.command_lib.storage.diagnose import diagnostic
from googlecloudsdk.command_lib.storage.resources import gcs_resource_reference
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import gce_cache
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
import requests


_CORE_CHECK_NAME = 'Direct Connectivity Call'
_SUCCESS = 'Success.'
_NOT_FOUND = '[Not Found]'
_METADATA_BASE_URL = (  # gcloud-disable-gdu-domain
    'http://metadata.google.internal/computeMetadata/v1/instance/'
)
_METADATA_ZONE_URL = _METADATA_BASE_URL + 'zone'
_METADATA_MTU_URL = _METADATA_BASE_URL + 'network-interfaces/0/mtu'
_METADATA_NETWORK_URL = _METADATA_BASE_URL + 'network-interfaces/0/network'
_METADATA_IPV4_URL = _METADATA_BASE_URL + 'network-interfaces/0/ip'
_METADATA_IPV6_URL = _METADATA_BASE_URL + 'network-interfaces/0/ipv6s'
_METADATA_INSTANCE_ID_URL = _METADATA_BASE_URL + 'id'
_METADATA_PROJECT_NUM_URL = (  # gcloud-disable-gdu-domain
    'http://metadata.google.internal/computeMetadata/v1/'
    'project/numeric-project-id'
)
_LINUX_DMI_PRODUCT_NAME_FILE = '/sys/class/dmi/id/product_name'
_METADATA_SERVICE_ACCOUNTS_URL = _METADATA_BASE_URL + 'service-accounts/'
_METADATA_DEFAULT_SERVICE_ACCOUNT_TOKEN_URL = (
    _METADATA_BASE_URL + 'service-accounts/default/token'
)
_PRIMARY_NIC_IP_ERROR = (
    'Could not find a valid IPv4 or IPv6 address allocated to primary network'
    ' interface from metadata service.'
)
_COMPUTE_VM_MISSING_SA_ERROR = (
    'Compute VM missing service account. See: '
    'https://cloud.google.com/compute/docs/instances/change-service-account'
)
_SERVICE_ACCOUNT_INVALID_SCOPE_ERROR = (
    'Service account does not have a valid access scope attached. See: '
    'https://cloud.google.com/compute/docs/access/service-accounts#scopes_best_practice'
)
_SERVICE_ACCOUNT_GENERIC_ERROR = (
    'Encountered an unexpected error retrieving information about your'
    ' service account. Please try again later.'
)
_XDS_BOOTSTRAP_ENV_VAR = 'GRPC_XDS_BOOTSTRAP'
_XDS_BOOTSTRAP_CONFIG_ENV_VAR = 'GRPC_XDS_BOOTSTRAP_CONFIG'
_XDS_BOOTSTRAP_ERROR = (
    f'Direct Connectivity cannot be used with environment variables'
    f' "{_XDS_BOOTSTRAP_ENV_VAR}" or "{_XDS_BOOTSTRAP_CONFIG_ENV_VAR}".'
)


def _log_metadata_response_error(url, response):
  """Logs an error for a failed metadata service request."""
  if response is None:
    log.error('Failed to query metadata service at %s.', url)
  elif response.status_code != 200:
    log.error(
        'Metadata service request to %s returned status %s: %s',
        url,
        response.status_code,
        response.text,
    )
  elif not response.text.strip():
    log.error(
        'Metadata service request to %s returned an empty response body.',
        url,
    )


def _get_metadata_service_response(url, suppress_error_log=False):
  """Returns response object from the Metadata service."""
  try:
    response = requests.get(
        # gcloud-disable-gdu-domain
        url,
        headers={'Metadata-Flavor': 'Google'},
        timeout=5,
    )
    if response.status_code != 200 and not suppress_error_log:
      _log_metadata_response_error(url, response)
    return response
  except requests.exceptions.RequestException as e:
    if not suppress_error_log:
      log.error('Failed to query metadata service at %s: %s', url, e)
    return None


def _format_metadata_error(base_error, response):
  """Formats error message with HTTP status code and response details."""
  if response is not None and response.status_code != 200:
    details = response.text.strip()
    if details:
      return f'{base_error} (HTTP {response.status_code}: {details})'
    return f'{base_error} (HTTP {response.status_code})'
  return base_error


def _get_ips(dns_path, service_name):
  """Returns IPv4 and IPv6 addresses associated with a regular web URL."""
  res = []
  for ip in socket.getaddrinfo(dns_path, port=443, proto=socket.IPPROTO_TCP):
    if ip[0] == socket.AddressFamily.AF_INET6:
      res.append((ipaddress.ip_address(ip[4][0]), service_name + ' IPv6'))
    elif ip[0] == socket.AddressFamily.AF_INET:
      res.append((ipaddress.ip_address(ip[4][0]), service_name + ' IPv4'))
  return res


def _get_location_string_or_not_found(s):
  return '"{}"'.format(s.lower()) if s else _NOT_FOUND


def _check_zone_prefix(region, zone):
  """Returns true if the region is a prefix of the given zone."""
  return zone.lower().startswith(region.lower())


def _exec_and_return_code_and_stdout(command):
  """Returns exit code and standard output from executing a command."""
  out = io.StringIO()
  ret_code = execution_utils.Exec(
      command,
      no_exit=True,
      out_func=out.write,
  )
  return ret_code, out.getvalue().strip()


def _exec_gcloud_and_return_code_and_stdout(command_args):
  """Returns exit code and standard output from executing gcloud command."""
  command = execution_utils.ArgsForGcloud() + command_args
  return _exec_and_return_code_and_stdout(command)


def _get_zone():
  """Gets the zone of the VM from the Metadata service."""
  response = _get_metadata_service_response(_METADATA_ZONE_URL)
  if response is not None and response.status_code == 200:
    return response.text.strip().rsplit('/', 1)[-1]
  return ''


def _get_vm_network_name():
  """Returns the short name of the VM primary VPC network from metadata."""
  try:
    response = requests.get(
        # gcloud-disable-gdu-domain
        _METADATA_NETWORK_URL,
        headers={'Metadata-Flavor': 'Google'},
        timeout=5,
    )
    if (
        getattr(response, 'status_code', None) == 200
        and getattr(response, 'text', '').strip()
    ):
      return response.text.strip().rsplit('/', 1)[-1]
  except Exception:  # pylint: disable=broad-except
    pass
  return ''


def _rule_applies_to_tcp_port(rule_entries, target_port=443):
  """Returns true if firewall rule entries apply to TCP and target_port."""
  if not rule_entries:
    return True
  for entry in rule_entries:
    protocol = str(entry.get('IPProtocol', '')).lower()
    if protocol == 'all':
      return True
    if protocol in ('tcp', '6'):
      ports = entry.get('ports')
      if not ports:
        return True
      for port_spec in ports:
        if '-' in str(port_spec):
          parts = str(port_spec).split('-', 1)
          try:
            if int(parts[0]) <= target_port <= int(parts[1]):
              return True
          except ValueError:
            continue
        else:
          try:
            if int(port_spec) == target_port:
              return True
          except ValueError:
            continue
  return False


def _is_target_allowed_by_higher_priority(target, allow_rules, deny_priority):
  """Returns true if a higher-priority allow rule covers target on TCP 443."""
  for allow_rule in allow_rules:
    allow_priority = allow_rule.get('priority', 1000)
    if allow_priority > deny_priority:
      continue
    if not _rule_applies_to_tcp_port(allow_rule.get('allowed')):
      continue
    ranges = (
        allow_rule.get('destinationRanges')
        or allow_rule.get('sourceRanges')
        or []
    )
    for allow_ip_str in ranges:
      try:
        allow_net = ipaddress.ip_network(allow_ip_str, strict=False)
      except ValueError:
        continue
      if allow_net.version != target.version:
        continue
      if isinstance(target, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
        if target.subnet_of(allow_net):
          return True
      elif target in allow_net:
        return True
  return False


def _log_running_check(check_name):
  log.info('Running Check: {}'.format(check_name))


class DirectConnectivityDiagnostic(diagnostic.Diagnostic):
  """Direct Connectivity Diagnostic."""

  def __init__(
      self,
      bucket_resource: gcs_resource_reference.GcsBucketResource,
      logs_path=None,
  ):
    """Initializes the Direct Connectivity Diagnostic."""
    self._bucket_resource = bucket_resource
    self._cleaned_up = False
    self._process_count = 1
    self._results = []
    self._retain_logs = bool(logs_path)
    self._thread_count = 1
    self._vm_zone = None
    self._has_firewall_conflict = False
    self._vm_ipv4 = None
    self._vm_ipv6 = None

    if logs_path is None:
      self._logs_path = os.path.join(
          tempfile.gettempdir(),
          'direct_connectivity_log_'
          + path_util.generate_random_int_for_path()
          + '.txt',
      )
    else:
      self._logs_path = files.ExpandHomeDir(logs_path)

  @property
  def name(self) -> str:
    return 'Direct Connectivity Diagnostic'

  def _clean_up(self):
    """Restores environment variables and cleans up temporary cloud object."""
    if not self._cleaned_up:
      super(DirectConnectivityDiagnostic, self)._post_process()
      self._cleaned_up = True

  def _generic_check_for_string_in_logs(
      self,
      target_string,
  ):
    """Checks if target is substring of a line in the logs."""
    if not self._logs_path or not os.path.exists(self._logs_path):
      return False
    try:
      with files.FileReader(self._logs_path) as file_reader:
        for line in file_reader:
          if target_string in line:
            return True
    except Exception:  # pylint: disable=broad-except
      return False
    return False

  def _check_core_buckets_describe_call(self):
    """Returns true if get bucket success over Direct Connectivity infra."""
    if self._has_firewall_conflict:
      # Skipping as making this call without valid firewall rules will always
      # fail, preventing us from properly identifying if there is an issue with
      # this specific check.
      return (
          'Skipped because conflicting firewall rules were found. Please'
          ' resolve firewall issues first.'
      )
    self._set_env_variable('ATTEMPT_DIRECT_PATH', 1)
    self._set_env_variable(
        'CLOUDSDK_STORAGE_PREFERRED_API', 'grpc_with_json_fallback'
    )
    self._set_env_variable('GRPC_TRACE', 'http')
    self._set_env_variable('GRPC_VERBOSITY', 'debug')
    self._set_env_variable('CLOUDSDK_CORE_HTTP_TIMEOUT', 15)

    with files.FileWriter(self._logs_path) as file_writer:
      command = execution_utils.ArgsForGcloud() + [
          '--verbosity=debug',
          'storage',
          'buckets',
          'describe',
          self._bucket_resource.storage_url.url_string,
      ]

      return_code = execution_utils.Exec(
          command,
          err_func=file_writer.write,
          no_exit=True,
      )

    if return_code == 0:
      with files.FileReader(self._logs_path) as file_reader:
        for line in file_reader:
          if re.search(
              r'(?:\[ipv6:(?:%5B)?2001:4860:80[4-7].+\])|(?:\[ipv4:(?:%5B)?34\.126.+\])',
              line,
          ):
            return _SUCCESS
    return 'Failed. See log at ' + self._logs_path

  def _check_private_service_connect(self):
    """Checks if connecting to PSC endpoint."""
    if self._generic_check_for_string_in_logs(
        # gcloud-disable-gdu-domain
        target_string='.p.googleapis.com'
    ):
      return (
          'Found PSC endpoint. For context, search for ".p.googleapis.com" in'
          ' logs at '
          + self._logs_path
      )
    return _SUCCESS

  def _read_dmi_product_name(self):
    """Reads Linux DMI product name if available."""
    if not os.path.exists(_LINUX_DMI_PRODUCT_NAME_FILE):
      return ''
    try:
      return files.ReadFileContents(_LINUX_DMI_PRODUCT_NAME_FILE).strip()
    except Exception:  # pylint: disable=broad-except
      return ''

  def _check_inside_vm(self):
    """Checks if user is inside a GCE VM."""
    if gce_cache.GetOnGCE():
      product_name = self._read_dmi_product_name()
      if product_name and not product_name.startswith('Google'):
        return (
            f'DMI product name "{product_name}" does not match Google'
            ' Compute Engine.'
        )
      return _SUCCESS
    return 'Detected this command is not being run from within a VM.'

  def _check_traffic_director_access(self):
    """Checks if user can access Traffic Director service."""
    try:
      # gcloud-disable-gdu-domain
      requests.get('https://directpath-pa.googleapis.com:443')
      return _SUCCESS
    except requests.exceptions.RequestException:
      return 'Unable to connect to Traffic Director.'

  def _check_firewalls(self):
    """Checks if user can access Traffic Director service."""
    desired_ip_networks = [
        (ipaddress.ip_network('34.126.0.0/18'), 'Direct Connectivity IPv4'),
        (
            ipaddress.ip_network('2001:4860:8040::/42'),
            'Direct Connectivity IPv6',
        ),
    ]
    desired_ip_addresses = _get_ips(
        # gcloud-disable-gdu-domain
        'storage.googleapis.com',
        'storage.googleapis.com',
        # gcloud-disable-gdu-domain
    ) + _get_ips('directpath-pa.googleapis.com', 'Traffic Director')
    ret_code, stdout = _exec_gcloud_and_return_code_and_stdout(
        ['compute', 'firewall-rules', 'list', '--format=json']
    )
    if ret_code != 0:
      return 'Could not retrieve firewall rules. See STDERR messages.'
    try:
      firewall_response = json.loads(stdout)
    except (ValueError, json.JSONDecodeError):
      return 'Could not parse firewall rules response.'
    has_network_field = any(
        fw.get('network')
        for fw in firewall_response
        if fw.get('direction') == 'EGRESS' and not fw.get('disabled')
    )
    vm_network = _get_vm_network_name() if has_network_field else ''
    active_egress_rules = []
    for firewall in firewall_response:
      if firewall.get('direction') != 'EGRESS' or firewall.get('disabled'):
        continue
      fw_network = firewall.get('network', '').rsplit('/', 1)[-1]
      if vm_network and fw_network and fw_network != vm_network:
        continue
      active_egress_rules.append(firewall)

    allow_rules = [
        fw
        for fw in active_egress_rules
        if fw.get('allowed') and not fw.get('denied')
    ]
    deny_rules = [
        fw
        for fw in active_egress_rules
        if not (fw.get('allowed') and not fw.get('denied'))
    ]

    found_any_problem = False
    for firewall in deny_rules:
      if not _rule_applies_to_tcp_port(firewall.get('denied')):
        continue
      deny_priority = firewall.get('priority', 1000)
      found_firewall_problem = False
      ranges = (
          firewall.get('destinationRanges')
          or firewall.get('sourceRanges')
          or []
      )
      for firewall_ip_string in ranges:
        blocked_services = []
        try:
          firewall_network = ipaddress.ip_network(
              firewall_ip_string, strict=False
          )
        except ValueError:
          continue

        for desired_ip_network, service_name in desired_ip_networks:
          if (
              firewall_network.version == desired_ip_network.version
              and firewall_network.overlaps(desired_ip_network)
              and not _is_target_allowed_by_higher_priority(
                  desired_ip_network, allow_rules, deny_priority
              )
          ):
            if service_name not in blocked_services:
              blocked_services.append(service_name)

        for desired_ip_address, service_name in desired_ip_addresses:
          if (
              firewall_network.version == desired_ip_address.version
              and desired_ip_address in firewall_network
              and not _is_target_allowed_by_higher_priority(
                  desired_ip_address, allow_rules, deny_priority
              )
          ):
            if service_name not in blocked_services:
              blocked_services.append(service_name)

        for blocked_service in blocked_services:
          log.error(
              'Found firewall blocking {}: "{}"'.format(
                  blocked_service, firewall_ip_string
              )
          )
          found_firewall_problem = True

      if found_firewall_problem:
        log.error(
            'To disable run "gcloud compute firewall-rules update --disabled'
            ' {}"'.format(firewall['name'])
        )
        found_any_problem = True

    if found_any_problem:
      self._has_firewall_conflict = True
      return 'Found conflicting firewalls. See STDERR messages.'
    return _SUCCESS

  def _check_bucket_region(self):
    """Checks if bucket has problematic region."""

    bucket_location = self._bucket_resource.location.lower()
    vm_zone = _get_location_string_or_not_found(self._vm_zone)

    # Provide a warning if the bucket zone does not match the VM zone.
    if self._bucket_resource.location_type == 'zone':
      bucket_zone = _get_location_string_or_not_found(
          self._bucket_resource.data_locations[0]
          if self._bucket_resource.data_locations
          else None
      )
      if _NOT_FOUND in (bucket_zone, vm_zone) or bucket_zone != vm_zone:
        return (
            f'Rapid storage bucket "{self._bucket_resource}" zone '
            f'{bucket_zone} does not '
            f'match VM "{socket.gethostname()}" zone {vm_zone}. '
            'Transfer performance between the bucket and VM may be degraded.'
        )
    # Dual-region buckets may have replicas in the same region as the VM. For
    # custom dual-regions, the VM must be in one of the regions covered by the
    # dual-region. For predefined dual-regions, the customer can check manually.
    if self._bucket_resource.location_type == 'dual-region':
      if self._bucket_resource.data_locations:
        regions = self._bucket_resource.data_locations
        for region in regions:
          if _check_zone_prefix(region, self._vm_zone):
            return _SUCCESS
        return (
            f'Bucket "{self._bucket_resource}" locations'
            f' {_get_location_string_or_not_found(regions[0])} and'
            f' {_get_location_string_or_not_found(regions[1])} do not include'
            f' VM "{socket.gethostname()}" zone {vm_zone}'
        )
      location_string = _get_location_string_or_not_found(
          self._bucket_resource.location
      )
      return (
          f'Found bucket "{self._bucket_resource}" is in a dual-region. Ensure '
          f'VM "{socket.gethostname()}" is in one of the regions covered by '
          f'the dual-region by looking up the dual-region {location_string} in '
          'the following table: '
          'https://cloud.google.com/storage/docs/locations#predefined '
          f'VM zone {vm_zone} should start with one of the regions covered by '
          f'the dual-region {location_string}.'
      )
    # For other region types, the substring check is sufficient.
    if self._vm_zone and _check_zone_prefix(bucket_location, self._vm_zone):
      return _SUCCESS
    return 'Bucket "{}" location {} does not match VM "{}" zone {}'.format(
        self._bucket_resource,
        _get_location_string_or_not_found(bucket_location),
        socket.gethostname(),
        vm_zone,
    )

  def _check_vm_has_service_account(self):
    """Checks if VM has a service account."""
    sa_response = _get_metadata_service_response(
        _METADATA_SERVICE_ACCOUNTS_URL
    )
    if sa_response is None or sa_response.status_code != 200:
      return _format_metadata_error(_SERVICE_ACCOUNT_GENERIC_ERROR, sa_response)

    # If the service account response is 2xx but empty we know we are missing a
    # service account.
    if not sa_response.text.strip():
      return _COMPUTE_VM_MISSING_SA_ERROR

    # If we hit this block we know that we have a valid service account, now we
    # validate access scope.
    token_response = _get_metadata_service_response(
        _METADATA_DEFAULT_SERVICE_ACCOUNT_TOKEN_URL
    )

    # Here we explicitly check for the 404 error indicating that there is a
    # missing account scope
    # Stringly typing this is not ideal, but it allows us to give a more
    # specific error message.
    if (
        token_response is not None
        and token_response.status_code == 404
        and 'No service account scopes specified.' in token_response.text
    ):
      return _SERVICE_ACCOUNT_INVALID_SCOPE_ERROR

    if token_response is None or token_response.status_code != 200:
      return _format_metadata_error(
          _SERVICE_ACCOUNT_GENERIC_ERROR, token_response
      )

    try:
      token_data = json.loads(token_response.text)
    except (ValueError, TypeError) as e:
      log.error('Failed to parse service account token JSON: %s', e)
      return _SERVICE_ACCOUNT_GENERIC_ERROR

    # Validate payload is a dict.
    if not isinstance(token_data, dict):
      log.error('Service account token payload is not a dict: %s', token_data)
      return _SERVICE_ACCOUNT_GENERIC_ERROR

    # Here we check that the access token is a non-empty string
    access_token = token_data.get('access_token')
    if not isinstance(access_token, str) or not access_token.strip():
      log.error('Service account access token is invalid: %s', access_token)
      return _SERVICE_ACCOUNT_GENERIC_ERROR

    # Happy path - 2xx response with a valid service account and access token.
    return _SUCCESS

  def _check_vm_mtu(self):
    """Checks if VM has a MTU of at least 1460."""
    mtu_response = _get_metadata_service_response(_METADATA_MTU_URL)
    if (
        mtu_response is None
        or mtu_response.status_code != 200
        or not mtu_response.text.strip()
    ):
      return _format_metadata_error(
          'Could not determine MTU from metadata service.', mtu_response
      )
    mtu = mtu_response.text.strip()
    if mtu == '8896':
      return _SUCCESS
    network_response = _get_metadata_service_response(_METADATA_NETWORK_URL)
    if (
        network_response is None
        or network_response.status_code != 200
        or not network_response.text.strip()
    ):
      return _format_metadata_error(
          'Could not determine VPC network from metadata service.',
          network_response,
      )
    network = network_response.text.strip()
    return (
        f'Set the MTU of VPC network interface "{network}" to 8896 for optimal '
        'transfer performance. See: '
        'https://cloud.google.com/storage/docs/enable-grpc-api#configure-vpcsc'
    )

  def _parse_metadata_ip(self, url, expected_version, suppress_error_log=False):
    """Fetches and parses an IP of expected_version from Metadata service."""
    response = _get_metadata_service_response(
        url, suppress_error_log=suppress_error_log
    )
    if (
        response is None
        or response.status_code != 200
        or not response.text.strip()
    ):
      return None, response
    first_line = response.text.strip().splitlines()[0].split('/')[0].strip()
    try:
      ip = ipaddress.ip_address(first_line)
      if ip.version == expected_version:
        return str(ip), response
    except ValueError:
      pass
    return None, response

  def _can_bind_local_ip(self, ip_str, family):
    """Returns true if the local OS can bind a socket to ip_str."""
    try:
      with socket.socket(family, socket.SOCK_DGRAM) as sock:
        sock.bind((ip_str, 0))
      return True
    except OSError:
      return False

  def _extract_backend_addrs_from_logs(self):
    """Extracts Direct Connectivity (host, port) pairs from gRPC debug logs."""
    addrs = []
    if self._logs_path and os.path.exists(self._logs_path):
      ipv4_subnet = ipaddress.ip_network('34.126.0.0/18')
      ipv6_subnet = ipaddress.ip_network('2001:4860:8040::/42')
      ipv6_pattern = (
          r'(?:\[|%5B)(2001:4860:80[4-7][0-9a-fA-F]:[0-9a-fA-F:]+)'
          r'(?:\]|%5D):(\d+)'
      )
      try:
        with files.FileReader(self._logs_path) as file_reader:
          for line in file_reader:
            for match in re.finditer(r'(34\.126\.\d+\.\d+):(\d+)', line):
              try:
                ip = ipaddress.ip_address(match.group(1))
              except ValueError:
                continue
              if ip in ipv4_subnet:
                addr = (str(ip), int(match.group(2)))
                if addr not in addrs:
                  addrs.append(addr)
            for match in re.finditer(ipv6_pattern, line):
              try:
                ip = ipaddress.ip_address(match.group(1))
              except ValueError:
                continue
              if ip in ipv6_subnet:
                addr = (str(ip), int(match.group(2)))
                if addr not in addrs:
                  addrs.append(addr)
      except Exception:  # pylint: disable=broad-except
        pass
    return addrs

  def _can_route_udp_to_target(self, source_ip, dest_ip, dest_port, family):
    """Returns true if kernel can route UDP socket from source_ip to dest_ip."""
    try:
      with socket.socket(family, socket.SOCK_DGRAM) as sock:
        sock.bind((source_ip, 0))
        sock.connect((dest_ip, dest_port))
      return True
    except OSError:
      return False

  def _check_kernel_routability(self):
    """Checks kernel routing table to Direct Connectivity via UDP connect."""
    if not self._vm_ipv4 and not self._vm_ipv6:
      return (
          'Skipping kernel routability check because no valid primary NIC IP'
          ' was found from metadata service.'
      )
    addrs = self._extract_backend_addrs_from_logs()
    ipv4_addrs = [(h, p) for h, p in addrs if ':' not in h]
    ipv6_addrs = [(h, p) for h, p in addrs if ':' in h]
    if not (self._vm_ipv4 and ipv4_addrs) and not (
        self._vm_ipv6 and ipv6_addrs
    ):
      return (
          'Skipping kernel routability check because no backend addresses'
          ' were found in gRPC logs.'
      )
    if self._vm_ipv4 and ipv4_addrs:
      dest_ip, dest_port = ipv4_addrs[0]
      if not self._can_route_udp_to_target(
          self._vm_ipv4, dest_ip, dest_port, socket.AF_INET
      ):
        return (
            'Kernel routing table is missing a valid route from local IPv4'
            f' "{self._vm_ipv4}" to Direct Connectivity IPv4 backends.'
        )
    if self._vm_ipv6 and ipv6_addrs:
      dest_ip, dest_port = ipv6_addrs[0]
      if not self._can_route_udp_to_target(
          self._vm_ipv6, dest_ip, dest_port, socket.AF_INET6
      ):
        return (
            'Kernel routing table is missing a valid route from local IPv6'
            f' "{self._vm_ipv6}" to Direct Connectivity IPv6 backends.'
        )
    return _SUCCESS

  def _can_connect_tcp(
      self, host: str, port: int, timeout: float = 5.0
  ) -> bool:
    """Attempts a direct TCP connection to host:port."""
    try:
      with socket.create_connection((host, port), timeout=timeout):
        return True
    except OSError:
      return False

  def _check_direct_tcp_connectivity(self):
    """Checks direct TCP reachability to Direct Connectivity backends."""
    if self._has_firewall_conflict:
      # Skipping as making this call without valid firewall rules will always
      # fail, preventing us from properly identifying if there is an issue with
      # this specific check.
      return (
          'Skipped because conflicting firewall rules were found. Please'
          ' resolve firewall issues first.'
      )
    addrs = self._extract_backend_addrs_from_logs()
    if not addrs:
      return (
          'Skipping direct TCP connectivity check because no backend addresses'
          ' were found in gRPC logs.'
      )
    for host, port in addrs:
      if self._can_connect_tcp(host, port):
        return _SUCCESS
    formatted = ', '.join(
        f'[{h}]:{p}' if ':' in h else f'{h}:{p}' for h, p in addrs
    )
    return (
        'Failed to establish direct TCP connection to Direct Connectivity'
        f' backends ({formatted}). Traffic may be blocked by firewalls or'
        ' routing.'
    )

  def _check_xds_and_alts_errors(self):
    """Logs VM metadata and checks gRPC logs for xDS or ALTS errors."""
    if gce_cache.GetOnGCE():
      instance_id_resp = _get_metadata_service_response(
          _METADATA_INSTANCE_ID_URL, suppress_error_log=True
      )
      project_num_resp = _get_metadata_service_response(
          _METADATA_PROJECT_NUM_URL, suppress_error_log=True
      )
      instance_id = (
          instance_id_resp.text.strip()
          if instance_id_resp and instance_id_resp.status_code == 200
          else _NOT_FOUND
      )
      project_num = (
          project_num_resp.text.strip()
          if project_num_resp and project_num_resp.status_code == 200
          else _NOT_FOUND
      )
      log.debug(
          'VM Metadata - Instance ID: %s, Project Number: %s',
          instance_id,
          project_num,
      )

    if self._logs_path and os.path.exists(self._logs_path):
      try:
        with files.FileReader(self._logs_path) as file_reader:
          for line in file_reader:
            if 'alts handshake failed' in line.lower():
              return (
                  'Detected ALTS handshake failure in gRPC logs. Verify VM'
                  ' service account and metadata server reachability.'
              )
            is_xds_line = (
                'StreamAggregatedResources' in line or 'xds_client' in line
            )
            if is_xds_line and (
                'UNAVAILABLE' in line
                or 'PERMISSION_DENIED' in line
                or 'failed' in line
            ):
              return (
                  'Detected xDS control plane error in gRPC logs. Verify'
                  ' Traffic Director access and IAM permissions.'
              )
      except OSError:
        pass
    return _SUCCESS

  def _check_local_network_interfaces(self):
    """Checks if metadata IPs and ::1 loopback are assigned to local NICs."""
    if not self._vm_ipv4 and not self._vm_ipv6:
      return (
          'Skipping local network interface check because no valid primary NIC'
          ' IP was found from metadata service.'
      )
    if self._vm_ipv4 and not self._can_bind_local_ip(
        self._vm_ipv4, socket.AF_INET
    ):
      return (
          'Local network interface is missing metadata-assigned IPv4 address'
          f' "{self._vm_ipv4}".'
      )
    if self._vm_ipv6:
      if not self._can_bind_local_ip(self._vm_ipv6, socket.AF_INET6):
        return (
            'Local network interface is missing metadata-assigned IPv6 address'
            f' "{self._vm_ipv6}". IPv6 DHCP setup may have failed or not been'
            ' attempted.'
        )
      if not self._can_bind_local_ip('::1', socket.AF_INET6):
        return (
            'Local loopback interface is missing IPv6 loopback address "::1",'
            ' which gRPC clients use to detect IPv6 support.'
        )
    return _SUCCESS

  def _check_primary_nic_ips(self):
    """Checks if VM primary NIC has IPv4 or IPv6 allocated in metadata."""
    # We check both IPv4 and IPv6 metadata endpoints, but only one is expected
    # to succeed (e.g., IPv4-only VMs return a 404 on the IPv6 endpoint).
    # Pass suppress_error_log=True so we only emit error logs when both fail.
    self._vm_ipv4, ipv4_resp = self._parse_metadata_ip(
        _METADATA_IPV4_URL, 4, suppress_error_log=True
    )
    self._vm_ipv6, ipv6_resp = self._parse_metadata_ip(
        _METADATA_IPV6_URL, 6, suppress_error_log=True
    )
    if not self._vm_ipv4 and not self._vm_ipv6:
      _log_metadata_response_error(_METADATA_IPV4_URL, ipv4_resp)
      _log_metadata_response_error(_METADATA_IPV6_URL, ipv6_resp)
      return _PRIMARY_NIC_IP_ERROR
    return _SUCCESS

  def _check_xds_bootstrap_env_vars(self):
    """Checks if conflicting gRPC xDS bootstrap env vars are set."""
    if encoding.GetEncodedValue(
        os.environ, _XDS_BOOTSTRAP_ENV_VAR
    ) or encoding.GetEncodedValue(os.environ, _XDS_BOOTSTRAP_CONFIG_ENV_VAR):
      return _XDS_BOOTSTRAP_ERROR
    return _SUCCESS

  def _run(self):
    """Runs the diagnostic test."""
    log.warning(
        'This diagnostic is experimental. The output may change,'
        ' and checks may be added or removed at any time. Please do not rely on'
        ' the diagnostic being present.'
    )

    _log_running_check('Firewalls')
    try:
      firewall_res = self._check_firewalls()
    # pylint: disable=broad-except
    except Exception as e:
      # pylint: enable=broad-except
      firewall_res = e
    self._results.append(
        diagnostic.DiagnosticOperationResult(
            name='Firewalls',
            result=firewall_res,
            payload_description=(
                'Direct Connectivity requires access to various IP addresses'
                ' that may be blocked by firewalls.'
            ),
        )
    )

    _log_running_check(_CORE_CHECK_NAME)
    self._results.append(
        diagnostic.DiagnosticOperationResult(
            name=_CORE_CHECK_NAME,
            result=self._check_core_buckets_describe_call(),
            payload_description=(
                'Able to get bucket metadata using Direct'
                ' Connectivity network path.'
            ),
        )
    )

    self._vm_zone = _get_zone()

    for check, name, description in [
        (
            self._check_private_service_connect,
            'Private Service Connect',
            (
                'Checks for string in logs containing incompatible PSC endpoint'
                # gcloud-disable-gdu-domain
                ' of format "*.p.googleapis.com".'
            ),
        ),
        (
            self._check_inside_vm,
            'Compute Engine VM',
            (
                'Direct Connectivity is only accessible from within Compute'
                ' Engine virtual machines.'
            ),
        ),
        (
            self._check_xds_bootstrap_env_vars,
            'gRPC xDS Bootstrap',
            (
                'Checks that custom gRPC xDS bootstrap environment variables'
                ' are not overriding Direct Connectivity.'
            ),
        ),
        (
            self._check_traffic_director_access,
            'Traffic Director',
            (
                'Direct Connectivity requires access to the Traffic Director'
                ' service.'
            ),
        ),
        (
            self._check_bucket_region,
            'Bucket Region',
            (
                'To get the best performance, the bucket should have a replica'
                ' in the same region as the VM.'
            ),
        ),
        (
            self._check_vm_has_service_account,
            'VM has Service Account',
            'Direct Connectivity requires the VM have a service account.',
        ),
        (
            self._check_vm_mtu,
            'VPC Network MTU',
            (
                'Direct Connectivity performs best with a VPC network MTU of'
                ' 8896.'
            ),
        ),
        (
            self._check_primary_nic_ips,
            'Primary NIC IP Allocation',
            (
                'Direct Connectivity requires an IPv4 or IPv6 address allocated'
                ' to the primary network interface.'
            ),
        ),
        (
            self._check_local_network_interfaces,
            'Local Network Interfaces',
            (
                'Direct Connectivity requires metadata-allocated IPs and IPv6'
                ' loopback "::1" to be assigned to local network interfaces.'
            ),
        ),
        (
            self._check_kernel_routability,
            'Kernel Routability',
            (
                'Direct Connectivity requires valid kernel routing table'
                ' entries from local network interfaces to Direct Connectivity'
                ' subnets.'
            ),
        ),
        (
            self._check_direct_tcp_connectivity,
            'Direct TCP Connectivity',
            (
                'Checks direct TCP connectivity to Direct Connectivity backend'
                ' IP addresses.'
            ),
        ),
        (
            self._check_xds_and_alts_errors,
            'xDS and ALTS Handshake',
            (
                'Checks gRPC debug logs for xDS control plane or ALTS handshake'
                ' errors.'
            ),
        ),
    ]:
      try:
        _log_running_check(name)
        res = check()
      # pylint: disable=broad-except
      except Exception as e:
        # pylint: enable=broad-except
        res = e
      self._results.append(
          diagnostic.DiagnosticOperationResult(
              name=name,
              result=res,
              payload_description=description,
          )
      )

  def _post_process(self):
    """See _clean_up.

    Using redundant calls because we can clean up earlier during _run, and
    keeping _post_process ensures clean up if _run fails.
    """
    self._clean_up()

  @property
  def result(self) -> diagnostic.DiagnosticResult:
    """Returns the summarized result of the diagnostic execution."""
    return diagnostic.DiagnosticResult(
        name=self.name,
        operation_results=self._results,
    )

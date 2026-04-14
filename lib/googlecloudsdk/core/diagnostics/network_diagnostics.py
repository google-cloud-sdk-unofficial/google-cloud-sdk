# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""A module for diagnosing common network and proxy problems."""


import datetime
import re
import sys
import warnings

import certifi
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core import requests as core_requests
from googlecloudsdk.core.diagnostics import check_base
from googlecloudsdk.core.diagnostics import diagnostic_base
from googlecloudsdk.core.diagnostics import http_proxy_setup
from googlecloudsdk.core.util import files
import requests
from six.moves import urllib
import urllib3.exceptions

_NETWORK_TIMEOUT = 60  # Timeout in seconds when testing GET requests


class NetworkDiagnostic(diagnostic_base.Diagnostic):
  """Diagnose and fix local network connection issues."""

  def __init__(self, check_certs_host=None):
    intro = ('Network diagnostic detects and fixes local network connection '
             'issues.')
    checklist = []
    if check_certs_host:
      checklist.append(CertChecker(check_certs_host))
    checklist.append(ReachabilityChecker())
    super(NetworkDiagnostic, self).__init__(
        intro=intro, title='Network diagnostic', checklist=checklist
    )


def DefaultUrls():
  """Returns a list of hosts whose reachability is essential for the Cloud SDK.

  Returns:
    A list of urls (str) to check reachability for.
  """
  urls = ['https://accounts.google.com',
          'https://cloudresourcemanager.googleapis.com/v1beta1/projects',
          'https://www.googleapis.com/auth/cloud-platform']

  download_urls = (properties.VALUES.component_manager.snapshot_url.Get() or
                   config.INSTALLATION_CONFIG.snapshot_url)
  urls.extend(u for u in download_urls.split(',')
              if urllib.parse.urlparse(u).scheme in ('http', 'https'))
  return urls


class ReachabilityChecker(check_base.Checker):
  """Checks whether the hosts of given urls are reachable."""

  @property
  def issue(self):
    return 'network connection'

  def Check(self, urls=None, first_run=True):
    """Run reachability check.

    Args:
      urls: iterable(str), The list of urls to check connection to. Defaults to
        DefaultUrls() (above) if not supplied.
      first_run: bool, True if first time this has been run this invocation.

    Returns:
      A tuple of (check_base.Result, fixer) where fixer is a function that can
        be used to fix a failed check, or  None if the check passed or failed
        with no applicable fix.
    """
    if urls is None:
      if properties.IsDefaultUniverse():
        urls = DefaultUrls()
      else:
        result = check_base.Result(
            passed=True,
            message=(
                'Skipping reachability check for default URLs on non-default'
                ' universe.'))
        return result, None

    failures = []
    # Check reachability using requests
    for url in urls:
      fail = CheckURLRequests(url)
      if fail:
        failures.append(fail)

    if failures:
      fail_message = ConstructMessageFromFailures(failures, first_run)
      result = check_base.Result(passed=False, message=fail_message,
                                 failures=failures)
      fixer = http_proxy_setup.ChangeGcloudProxySettings
      return result, fixer

    pass_message = 'Reachability Check {0}.'.format('passed' if first_run else
                                                    'now passes')
    result = check_base.Result(passed=True, message='No URLs to check.'
                               if not urls else pass_message)
    return result, None


def CheckURLRequests(url):
  try:
    core_requests.GetSession(timeout=_NETWORK_TIMEOUT).request('GET', url)
  except requests.exceptions.RequestException as err:
    msg = 'requests cannot reach {0}:\n{1}\n'.format(
        url, err)
    return check_base.Failure(message=msg, exception=err)


def ConstructMessageFromFailures(failures, first_run):
  """Constructs error messages along with diagnostic information."""
  message = 'Reachability Check {0}.\n'.format('failed' if first_run else
                                               'still does not pass')
  for failure in failures:
    message += '    {0}\n'.format(failure.message)
  if first_run:
    message += ('Network connection problems may be due to proxy or '
                'firewall settings.\n')

  return message


class CertChecker(check_base.Checker):
  """Checks the certificate chain for a given host."""

  def __init__(self, host):
    self.host = host

  @property
  def issue(self):
    return 'certificate verification'

  def Check(self, first_run=True):
    if sys.version_info < (3, 13):
      result = check_base.Result(
          passed=False,
          message=(
              'Certificate diagnostics are only supported in Python 3.13 or'
              ' newer.'
          ),
      )
      return result, None
    try:
      from cryptography import x509  # pylint: disable=g-import-not-at-top
      from cryptography.x509 import verification  # pylint: disable=g-import-not-at-top
    except ImportError:
      result = check_base.Result(
          passed=False,
          message='Certificate diagnostics require the cryptography library.',
      )
      return result, None

    ca_certs_file = properties.VALUES.core.custom_ca_certs_file.Get()
    if not ca_certs_file:
      ca_certs_file = certifi.where()
    pem_data = files.ReadBinaryFileContents(ca_certs_file)
    local_certs = x509.load_pem_x509_certificates(pem_data)
    store = verification.Store(local_certs)
    url = (
        'https://' + self.host
        if not re.match('https?://', self.host)
        else self.host
    )
    parsed_url = urllib.parse.urlparse(url)
    hostname = parsed_url.hostname

    session = core_requests.GetSession(timeout=_NETWORK_TIMEOUT)
    captured_chain = None

    def CaptureHook(r, **unused_kwargs):
      nonlocal captured_chain
      sock = r.raw.connection.sock
      captured_chain = sock.get_unverified_chain()
      return r

    try:
      with warnings.catch_warnings():
        # We set verify=False in order to get the unverified chain ourselves;
        # this is intentional so we suppress this warning.
        warnings.simplefilter(
            'ignore', urllib3.exceptions.InsecureRequestWarning)
        with session.request(
            'GET',
            url,
            stream=True,  # Keep connection and socket alive for response hook.
            verify=False,
            hooks={'response': CaptureHook},
        ):
          # The CaptureHook populates captured_chain. The 'with' statement
          # ensures the connection is closed.
          pass
    except requests.exceptions.RequestException:
      return (
          check_base.Result(
              passed=False, message='Failed to connect to {}'.format(url)
          ),
          None,
      )

    assert captured_chain is not None
    server_certs = [
        x509.load_der_x509_certificate(der) for der in captured_chain]
    peer = server_certs[0]
    untrusted_intermediates = server_certs[1:]
    builder = (
        verification.PolicyBuilder()
        .store(store)
        .time(datetime.datetime.now(datetime.timezone.utc))
    )
    verifier = builder.build_server_verifier(x509.DNSName(hostname))
    try:
      verifier.verify(peer, untrusted_intermediates)
    except verification.VerificationError as ve:
      local_subjects = {cert.subject for cert in local_certs}
      top_cert = server_certs[-1]
      message = ['Certificate verification failed for {}.'.format(hostname)]
      message.append('Reason: {}'.format(ve))
      message.append('Server presented the following chain:')
      for i, cert in enumerate(server_certs):
        message.append(
            '  [{}] Subject: {}'.format(i, cert.subject.rfc4514_string())
        )
        message.append('      Issuer:  {}'.format(cert.issuer.rfc4514_string()))
      if (
          top_cert.subject == top_cert.issuer
          and top_cert.subject not in local_subjects
      ):
        missing_message = (
            'The root certificate ({}) is missing from your local CA file.'
            '\n'
            'Please obtain this missing certificate and append it to {}.'
            .format(top_cert.subject.rfc4514_string(), ca_certs_file)
        )
      elif (
          top_cert.subject != top_cert.issuer
          and top_cert.issuer not in local_subjects
      ):
        missing_message = (
            'The intermediary issuer certificate ({issuer}) is missing from the'
            ' server handshake and is missing from your local CA file.'
            '\n'
            'NOTE: Your network proxy is failing to present the full'
            ' certificate chain. This usually indicates a proxy'
            ' server implementation that is noncompliant with TLS standards.'
            '\n'
            'Either your network administrator needs to update your proxy'
            ' server to serve the entire intermediate chain, or you will need'
            ' to obtain the missing intermediate certificate and append it to'
            ' {ca_file}.'
        ).format(issuer=top_cert.issuer.rfc4514_string(), ca_file=ca_certs_file)
      else:
        missing_message = ''
      if missing_message:
        message.append('\nAnalysis: ' + missing_message)
      result = check_base.Result(passed=False, message='\n'.join(message))
      return result, None
    else:
      result = check_base.Result(
          passed=True,
          message='Certificate chain for {} verified successfully.'.format(
              hostname
          ),
      )
      return result, None

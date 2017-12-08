"""This package facilitates HTTP/REST requests to the registry."""



from containerregistry.client import docker_creds  # pylint: disable=unused-import
from containerregistry.client import docker_name
import httplib2  # pylint: disable=unused-import


class BadStatusException(Exception):
  """Exceptions when an unexpected HTTP status is returned."""

  def __init__(
      self,
      resp,
      content):
    message = 'Response:\n{resp}\nContent:\n{content}'.format(
        resp=resp, content=content)
    super(BadStatusException, self).__init__(message)
    self._resp = resp
    self._content = content

  @property
  def resp(self):
    return self._resp

  @property
  def status(self):
    return self._resp.status

  @property
  def content(self):
    return self._content


# pylint: disable=invalid-name
def Request(
    transport,
    url,
    credentials,
    accepted_codes=None,
    body=None,
    content_type=None):
  """Wrapper containing much of the boilerplate REST logic for Registry calls.

  Args:
    transport: the HTTP transport to use for requesting url
    url: the URL to which to talk
    credentials: the source of the Authorization header
    accepted_codes: the list of acceptable http status codes
    body: the body to pass into the PUT request (or None for GET)
    content_type: the mime-type of the request (or None for JSON)

  Raises:
    BadStatusException: the status codes wasn't among the acceptable set.

  Returns:
    The response of the HTTP request, and its contents.
  """
  headers = {
      'content-type': content_type if content_type else 'application/json',
      'Authorization': credentials.Get(),
      'X-Docker-Token': 'true',
      'user-agent': docker_name.USER_AGENT,
  }
  resp, content = transport.request(
      url, 'PUT' if body else 'GET',
      body=body, headers=headers)

  if resp.status not in accepted_codes:
    # Use the content returned by GCR as the error message.
    raise BadStatusException(resp, content)

  return resp, content


def Scheme(endpoint):
  """Returns https scheme for all the endpoints except localhost."""
  if endpoint.startswith('localhost:'):
    return 'http'
  else:
    return 'https'

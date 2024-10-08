"""Generated message classes for connectgateway version v1alpha1.

The Connect Gateway service allows connectivity from external parties to
connected Kubernetes clusters.
"""
# NOTE: This file is autogenerated and should not be edited by hand.

from __future__ import absolute_import

from apitools.base.protorpclite import messages as _messages
from apitools.base.py import encoding


package = 'connectgateway'


class ConnectgatewayProjectsLocationsMembershipsGenerateCredentialsRequest(_messages.Message):
  r"""A ConnectgatewayProjectsLocationsMembershipsGenerateCredentialsRequest
  object.

  Enums:
    OperatingSystemValueValuesEnum: Optional. The operating system where the
      kubeconfig will be used.

  Fields:
    forceUseAgent: Optional. Whether to force the use of Connect Agent-based
      transport. This will return a configuration that uses Connect Agent as
      the underlying transport mechanism for cluster types that would
      otherwise have used a different transport. Requires that Connect Agent
      be installed on the cluster. Setting this field to false is equivalent
      to not setting it.
    kubernetesNamespace: Optional. The namespace to use in the kubeconfig
      context. If this field is specified, the server will set the `namespace`
      field in kubeconfig context. If not specified, the `namespace` field is
      omitted.
    name: Required. The Fleet membership resource.
    operatingSystem: Optional. The operating system where the kubeconfig will
      be used.
    version: Optional. The Connect Gateway version to be used in the resulting
      configuration. Leave this field blank to let the server choose the
      version (recommended).
  """

  class OperatingSystemValueValuesEnum(_messages.Enum):
    r"""Optional. The operating system where the kubeconfig will be used.

    Values:
      OPERATING_SYSTEM_UNSPECIFIED: Generates a kubeconfig that works for all
        operating systems not defined below.
      OPERATING_SYSTEM_WINDOWS: Generates a kubeconfig that is specifically
        designed to work with Windows.
    """
    OPERATING_SYSTEM_UNSPECIFIED = 0
    OPERATING_SYSTEM_WINDOWS = 1

  forceUseAgent = _messages.BooleanField(1)
  kubernetesNamespace = _messages.StringField(2)
  name = _messages.StringField(3, required=True)
  operatingSystem = _messages.EnumField('OperatingSystemValueValuesEnum', 4)
  version = _messages.StringField(5)


class GenerateCredentialsResponse(_messages.Message):
  r"""Connection information for a particular membership.

  Fields:
    endpoint: The generated URI of the cluster as accessed through the Connect
      Gateway API.
    kubeconfig: A full YAML kubeconfig in serialized format.
  """

  endpoint = _messages.StringField(1)
  kubeconfig = _messages.BytesField(2)


class StandardQueryParameters(_messages.Message):
  r"""Query parameters accepted by all methods.

  Enums:
    FXgafvValueValuesEnum: V1 error format.
    AltValueValuesEnum: Data format for response.

  Fields:
    f__xgafv: V1 error format.
    access_token: OAuth access token.
    alt: Data format for response.
    callback: JSONP
    fields: Selector specifying which fields to include in a partial response.
    key: API key. Your API key identifies your project and provides you with
      API access, quota, and reports. Required unless you provide an OAuth 2.0
      token.
    oauth_token: OAuth 2.0 token for the current user.
    prettyPrint: Returns response with indentations and line breaks.
    quotaUser: Available to use for quota purposes for server-side
      applications. Can be any arbitrary string assigned to a user, but should
      not exceed 40 characters.
    trace: A tracing token of the form "token:<tokenid>" to include in api
      requests.
    uploadType: Legacy upload protocol for media (e.g. "media", "multipart").
    upload_protocol: Upload protocol for media (e.g. "raw", "multipart").
  """

  class AltValueValuesEnum(_messages.Enum):
    r"""Data format for response.

    Values:
      json: Responses with Content-Type of application/json
      media: Media download with context-dependent Content-Type
      proto: Responses with Content-Type of application/x-protobuf
    """
    json = 0
    media = 1
    proto = 2

  class FXgafvValueValuesEnum(_messages.Enum):
    r"""V1 error format.

    Values:
      _1: v1 error format
      _2: v2 error format
    """
    _1 = 0
    _2 = 1

  f__xgafv = _messages.EnumField('FXgafvValueValuesEnum', 1)
  access_token = _messages.StringField(2)
  alt = _messages.EnumField('AltValueValuesEnum', 3, default='json')
  callback = _messages.StringField(4)
  fields = _messages.StringField(5)
  key = _messages.StringField(6)
  oauth_token = _messages.StringField(7)
  prettyPrint = _messages.BooleanField(8, default=True)
  quotaUser = _messages.StringField(9)
  trace = _messages.StringField(10)
  uploadType = _messages.StringField(11)
  upload_protocol = _messages.StringField(12)


encoding.AddCustomJsonFieldMapping(
    StandardQueryParameters, 'f__xgafv', '$.xgafv')
encoding.AddCustomJsonEnumMapping(
    StandardQueryParameters.FXgafvValueValuesEnum, '_1', '1')
encoding.AddCustomJsonEnumMapping(
    StandardQueryParameters.FXgafvValueValuesEnum, '_2', '2')

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
"""Read and write properties for the CloudSDK."""

from googlecloudsdk.core import argv_utils
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.properties import completers
from googlecloudsdk.core.properties import constants
from googlecloudsdk.core.properties.exceptions import Error
from googlecloudsdk.core.properties.exceptions import InvalidProjectError
from googlecloudsdk.core.properties.exceptions import InvalidValueError
from googlecloudsdk.core.properties.exceptions import MissingInstallationConfig
from googlecloudsdk.core.properties.exceptions import NoSuchPropertyError
from googlecloudsdk.core.properties.exceptions import PropertiesParseError
from googlecloudsdk.core.properties.exceptions import PropertyValue
from googlecloudsdk.core.properties.exceptions import RequiredPropertyError
from googlecloudsdk.core.properties.exceptions import UnknownFormatError
from googlecloudsdk.core.properties.parsers import _GetProperty
from googlecloudsdk.core.properties.parsers import _GetPropertyWithoutCallback
from googlecloudsdk.core.properties.parsers import _GetPropertyWithoutDefault
from googlecloudsdk.core.properties.parsers import PersistProperty
from googlecloudsdk.core.properties.scope import InvalidScopeValueError
from googlecloudsdk.core.properties.scope import Scope
from googlecloudsdk.core.properties.sections.api_endpoint_overrides import _SectionApiEndpointOverrides
from googlecloudsdk.core.properties.sections.storage import CheckHashes
from googlecloudsdk.core.properties.sections.storage import StoragePreferredApi
from googlecloudsdk.core.properties.types import _Property
from googlecloudsdk.core.properties.types import _Section
from googlecloudsdk.core.properties.universe import GetUniverseDomain
from googlecloudsdk.core.properties.universe import IsDefaultUniverse
from googlecloudsdk.core.properties.validators import _B_468088880_FIXED
from googlecloudsdk.core.properties.validators import AccessPolicyValidator
from googlecloudsdk.core.properties.validators import ExistingAbsoluteFilepathValidator
from googlecloudsdk.core.properties.validators import Stringize
from googlecloudsdk.core.properties.values import _Sections
from googlecloudsdk.core.properties.values import FromString
from googlecloudsdk.core.properties.values import IsInternalUserCheck
from googlecloudsdk.core.properties.values import ParsePropertyString
from googlecloudsdk.core.properties.values import VALUES


# Try to parse the command line flags at import time to see if someone provided
# the --configuration flag.  If they did, this could affect the value of the
# properties defined in that configuration.  Since some libraries (like logging)
# use properties at startup, we want to use the correct configuration for that.
named_configs.FLAG_OVERRIDE_STACK.PushFromArgs(argv_utils.GetDecodedArgv())

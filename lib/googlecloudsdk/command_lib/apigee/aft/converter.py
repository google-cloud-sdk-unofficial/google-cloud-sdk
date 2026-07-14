# -*- coding: utf-8 -*- # Lint as: python3
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
"""Bidirectional conversion between proxy.yaml model and Apigee bundle ZIP.

This module implements the two pure conversion functions called out in the
gcloud Apigee Feature Templates DPD (go/gcloud-apigee-yaml-dpd):

* `proxy_to_bundle(proxy)` -- render a `models.Proxy` into an Apigee bundle
  ZIP (Forward direction).
* `bundle_to_proxy(zip_bytes)` -- parse an Apigee bundle ZIP back into a
  `models.Proxy` (Backward direction).

The implementation is intentionally "throwaway" (per the DPD non-goals): it
ports the conversion algorithm from the Go prototype at
`experimental/users/madhurranjanm/golang-apigee-templater/pkg/converter/`
and will eventually be superseded by the server-side templater service at
`cloud/api_products/apihub/shared/templater/` (go/apihub-templater-api).

Bundle layout (matches Apigee's mgmt API expectation):

    apiproxy/{ProxyName}.xml            # <APIProxy> root descriptor
    apiproxy/proxies/{endpoint}.xml     # one per Proxy.endpoints[i]
    apiproxy/targets/{target}.xml       # one per Proxy.targets[i]
    apiproxy/policies/{policy}.xml      # one per Proxy.policies[i]
    apiproxy/resources/{type}/{name}    # one per Proxy.resources[i]

Policy bodies use the `metadata` / `_text` convention to represent XML
attributes and text content as plain dicts (matching the Go prototype's
`xmlToMap`/`mapToXML`). Round-trip parity is *semantic*, not byte-identical
with Apigee UI emissions.
"""

import io
import posixpath
import re
from typing import Optional, Any
import xml.etree.ElementTree as ET
import zipfile

from googlecloudsdk.command_lib.apigee.aft import models


# ---- Bundle safety bounds (Backward direction) ----

# Total uncompressed bytes across all entries. Mirrors API Hub templater's
# default at cloud/api_products/apihub/shared/templater/converter/zip.go.
_MAX_UNCOMPRESSED_BYTES = 10 * 1024 * 1024  # 10 MiB
_MAX_ENTRIES = 256
_BUNDLE_PREFIX = 'apiproxy/'
_CONFIGURATION_VERSION = '4.0'


class InvalidBundleError(Exception):
  """Raised when a ZIP cannot be interpreted as an Apigee bundle."""


# ============================================================================
# Public API
# ============================================================================


def proxy_to_bundle(proxy: models.Proxy) -> bytes:
  """Renders a Proxy model into an Apigee bundle ZIP.

  Args:
    proxy: A `models.Proxy` instance.

  Returns:
    The bundle ZIP as bytes. The returned bytes are deterministic for a given
    input proxy (entries written in sorted order; dict keys serialized in
    sorted order within each XML element).
  """
  try:
    files = _proxy_to_files(proxy)
  except AttributeError as e:
    raise ValueError(f'{e}; proxy struct: {proxy!r}') from e
  return _pack_files(files)


def bundle_to_proxy(zip_bytes: bytes) -> models.Proxy:
  """Parses an Apigee bundle ZIP into a Proxy model.

  Args:
    zip_bytes: Raw bytes of an Apigee bundle ZIP.

  Returns:
    A `models.Proxy` instance.

  Raises:
    InvalidBundleError: If the input is not a recognizable Apigee bundle,
      exceeds safety bounds, or contains malformed XML.
  """
  files = _unpack_files(zip_bytes)
  return _files_to_proxy(files)


# ============================================================================
# Forward: Proxy -> {path: bytes}
# ============================================================================


def _proxy_to_files(proxy: models.Proxy) -> dict[str, bytes]:
  """Returns a dict mapping bundle ZIP paths to file bytes for `proxy`."""
  files = {}

  # Root descriptor: apiproxy/{name}.xml
  files[_BUNDLE_PREFIX + proxy.name + '.xml'] = _root_xml_bytes(proxy)

  # apiproxy/proxies/{endpoint}.xml
  for endpoint in proxy.endpoints:
    files[_BUNDLE_PREFIX + 'proxies/' + endpoint.name + '.xml'] = (
        _proxy_endpoint_xml_bytes(endpoint)
    )

  # apiproxy/targets/{target}.xml
  for target in proxy.targets:
    files[_BUNDLE_PREFIX + 'targets/' + target.name + '.xml'] = (
        _target_endpoint_xml_bytes(target)
    )

  # apiproxy/policies/{policy}.xml
  for policy in proxy.policies:
    files[_BUNDLE_PREFIX + 'policies/' + policy.name + '.xml'] = (
        _policy_xml_bytes(policy)
    )

  # apiproxy/resources/{type}/{name}
  for resource in proxy.resources:
    path = _BUNDLE_PREFIX + 'resources/' + resource.type + '/' + resource.name
    content = resource.content or ''
    files[path] = content.encode('utf-8')

  return files


def _root_xml_bytes(proxy: models.Proxy) -> bytes:
  """Builds the <APIProxy> root descriptor as bytes."""
  root = ET.Element('APIProxy', attrib={'name': proxy.name})
  _sub_text(root, 'ConfigurationVersion', _CONFIGURATION_VERSION)
  if proxy.description:
    _sub_text(root, 'Description', proxy.description)
  if proxy.display_name:
    _sub_text(root, 'DisplayName', proxy.display_name)

  # Policies list
  policies_el = ET.SubElement(root, 'Policies')
  for policy in proxy.policies:
    _sub_text(policies_el, 'Policy', policy.name)

  # ProxyEndpoints list
  pes_el = ET.SubElement(root, 'ProxyEndpoints')
  for endpoint in proxy.endpoints:
    _sub_text(pes_el, 'ProxyEndpoint', endpoint.name)

  # TargetEndpoints list
  tes_el = ET.SubElement(root, 'TargetEndpoints')
  for target in proxy.targets:
    _sub_text(tes_el, 'TargetEndpoint', target.name)

  # Resources list (URIs of the form `{type}://{name}`).
  resources_el = ET.SubElement(root, 'Resources')
  for resource in proxy.resources:
    _sub_text(resources_el, 'Resource', resource.type + '://' + resource.name)

  return _serialize(root)


def _proxy_endpoint_xml_bytes(endpoint: models.ProxyEndpoint) -> bytes:
  """Builds <ProxyEndpoint> as bytes."""
  root = ET.Element('ProxyEndpoint', attrib={'name': endpoint.name})

  # HTTPProxyConnection / BasePath
  conn_el = ET.SubElement(root, 'HTTPProxyConnection')
  _sub_text(conn_el, 'BasePath', endpoint.base_path or '')

  _add_flows(root, endpoint.flows or [])
  _add_postclientflow(root, endpoint.post_client_flow)

  # RouteRules
  for route in endpoint.routes or []:
    rule_el = ET.SubElement(root, 'RouteRule', attrib={'name': route.name})
    if route.condition is not None:
      _sub_text(rule_el, 'Condition', route.condition)
    if route.target is not None:
      _sub_text(rule_el, 'TargetEndpoint', route.target)

  _add_fault_rules(
      root,
      endpoint.fault_rules or [],
      endpoint.default_fault_rule
  )
  return _serialize(root)


def _target_endpoint_xml_bytes(target: models.Target) -> bytes:
  """Builds <TargetEndpoint> as bytes."""
  root = ET.Element('TargetEndpoint', attrib={'name': target.name})

  built_target = False

  if isinstance(target, models.ProxyTarget):
    # HTTPTargetConnection (URL + optional auth) or LocalTargetConnection
    local_conn = target.local_target_connection
    http_conn = target.http_target_connection
    if local_conn:
      local_el = _dict_to_element('LocalTargetConnection', local_conn)
      root.append(local_el)
      built_target = True
    elif http_conn:
      http_el = _dict_to_element('HTTPTargetConnection', http_conn)
      root.append(http_el)
      built_target = True

    _add_flows(root, target.flows or [])
    _add_fault_rules(
        root,
        target.fault_rules or [],
        target.default_fault_rule,
    )

  if not built_target:
    # Build <HTTPTargetConnection> from simplified Target fields.
    conn_el = ET.SubElement(root, 'HTTPTargetConnection')
    if target.url:
      _sub_text(conn_el, 'URL', target.url)
    if target.auth:
      auth_el = ET.SubElement(conn_el, 'Authentication')
      typed_el = ET.SubElement(auth_el, target.auth)
      if target.scopes:
        scopes_el = ET.SubElement(typed_el, 'Scopes')
        for scope in target.scopes:
          _sub_text(scopes_el, 'Scope', scope)
      if target.aud:
        aud_el = ET.SubElement(typed_el, 'Audience')
        aud_el.text = target.aud

  return _serialize(root)


def _policy_xml_bytes(policy: models.Policy) -> bytes:
  """Builds a policy XML file from `policy.content`.

  The value is rendered using `_dict_to_element` (the inverse of
  `_element_to_dict`).

  Args:
    policy: A `models.Policy` instance. `policy.content` must be a single-key
      dict whose key matches `policy.type`.

  Returns:
    The policy XML as bytes.
  """
  if not isinstance(policy.content, dict) or len(policy.content) != 1:
    raise ValueError(
        'Policy %r content must be a single-key dict; got %r'
        % (policy.name, policy.content)
    )
  ((tag, value),) = policy.content.items()
  if policy.type and tag.lower() != policy.type.lower():
    raise ValueError(
        'Policy %r: type %r does not match content root tag %r'
        % (policy.name, policy.type, tag)
    )
  root = _dict_to_element(tag, value)
  return _serialize(root)


# ---- Flow / FaultRule helpers ----

# Maps a Flow.name to its enclosing XML element name in a ProxyEndpoint /
# TargetEndpoint. Flows with names other than PreFlow / PostFlow live inside
# the generic <Flows> container.
_NAMED_FLOW_TAGS = {
    'PreFlow': 'PreFlow',
    'PostFlow': 'PostFlow',
}


def _add_flows(parent: ET.Element, flows: list[models.Flow]):
  """Appends <PreFlow> / <Flows> / <PostFlow> elements to `parent`.

  Original flow order is preserved by emitting any run of consecutive
  generic (non-PreFlow / non-PostFlow) flows into a single in-position
  `<Flows>` container. PreFlow / PostFlow flows are emitted as top-level
  siblings at their original positions.

  Args:
    parent: The parent XML element.
    flows: The list of flows to add.
  """
  i = 0
  while i < len(flows):
    flow = flows[i]
    tag = _NAMED_FLOW_TAGS.get(flow.name)
    if tag:
      flow_el = ET.SubElement(parent, tag, attrib={'name': flow.name})
      _populate_flow(flow_el, flow)
      i += 1
      continue
    # Collect consecutive generic flows into one <Flows>.
    j = i
    while j < len(flows) and flows[j].name not in _NAMED_FLOW_TAGS:
      j += 1
    flows_el = ET.SubElement(parent, 'Flows')
    for flow in flows[i:j]:
      flow_el = ET.SubElement(flows_el, 'Flow', attrib={'name': flow.name})
      _populate_flow(flow_el, flow)
    i = j


def _add_postclientflow(parent: ET.Element, flow: Optional[models.Flow]):
  """Appends a <PostClientFlow> child for `flow` to `parent` if not None."""
  if flow is None:
    return
  flow_el = ET.SubElement(parent, 'PostClientFlow', attrib={'name': flow.name})
  _populate_flow(flow_el, flow)


def _populate_flow(flow_el: ET.Element, flow: models.Flow):
  """Writes <Request>/<Response>/<Step> children of a flow element.

  If `flow.mode` is unset *and* there are no steps, no wrapper element is
  emitted. This preserves round-trip parity with flows that carry neither
  a mode nor any steps (commonly used as placeholders on target endpoints).

  Args:
    flow_el: The XML element representing the flow.
    flow: The flow model.
  """
  if flow.condition:
    _sub_text(flow_el, 'Condition', flow.condition)
  has_steps = bool(flow.steps)
  if not flow.mode and not has_steps:
    return
  mode = (flow.mode or 'Request').strip()
  if mode not in ('Request', 'Response'):
    mode = 'Request'
  wrapper = ET.SubElement(flow_el, mode)
  for step in flow.steps or []:
    step_el = ET.SubElement(wrapper, 'Step')
    _sub_text(step_el, 'Name', step.name)
    if step.condition is not None:
      _sub_text(step_el, 'Condition', step.condition)


def _add_fault_rules(
    parent: ET.Element,
    fault_rules: list[models.FaultRule],
    default_fault_rule: Optional[models.FaultRule],
):
  """Appends <FaultRules> and <DefaultFaultRule> children to `parent`."""
  if fault_rules:
    frs_el = ET.SubElement(parent, 'FaultRules')
    for rule in fault_rules:
      rule_el = ET.SubElement(frs_el, 'FaultRule', attrib={'name': rule.name})
      _populate_flow(rule_el, rule)
  if default_fault_rule is not None:
    dfr_el = ET.SubElement(
        parent, 'DefaultFaultRule', attrib={'name': default_fault_rule.name}
    )
    if default_fault_rule.always_enforce:
      _sub_text(dfr_el, 'AlwaysEnforce', 'true')
    _populate_flow(dfr_el, default_fault_rule)


# ---- XML serialization helpers ----


def _sub_text(parent: ET.Element, tag: str, text: Optional[str]):
  """Creates a child element with text content."""
  el = ET.SubElement(parent, tag)
  el.text = text if text is not None else ''
  return el


def _serialize(elem: ET.Element) -> bytes:
  """Serializes an Element to bytes with an XML declaration."""
  # `short_empty_elements=False` matches Apigee's preference for explicit
  # close tags on policy bodies.
  return ET.tostring(
      elem, encoding='utf-8', xml_declaration=True, short_empty_elements=False
  )


# ============================================================================
# Backward: {path: bytes} -> Proxy
# ============================================================================


def _files_to_proxy(files: dict[str, bytes]) -> models.Proxy:
  """Reconstructs a Proxy from a `{path: bytes}` file map."""
  # Locate the single root descriptor at apiproxy/*.xml (not in a subdir).
  root_paths = [
      p
      for p in files
      if p.startswith(_BUNDLE_PREFIX)
      and '/' not in p[len(_BUNDLE_PREFIX) :]
      and p.endswith('.xml')
  ]
  if not root_paths:
    raise InvalidBundleError(
        'No root descriptor found (expected exactly one apiproxy/*.xml; got '
        'none).'
    )
  if len(root_paths) > 1:
    root_paths.sort()
    raise InvalidBundleError(f'Multiple root descriptors found: {root_paths}')

  root_path = root_paths[0]
  root_el = _parse_xml(files[root_path], root_path)
  # The bundle has no slot for the authoring-metadata fields (gateway /
  # schemaVersion), so re-stamp the known values here. They must be supplied to
  # the constructor because Proxy.__post_init__ validates them; a
  # post-construction assignment would trip on the name-only construction.
  proxy = models.Proxy(
      name=root_el.get('name') or '',
      gateway='apigee',
      schema_version='1.0.0',
  )

  desc = root_el.find('Description')
  if desc is not None and desc.text:
    proxy.description = desc.text
  dn = root_el.find('DisplayName')
  if dn is not None and dn.text:
    proxy.display_name = dn.text

  # Parse policies (one per apiproxy/policies/*.xml).
  for path in sorted(files):
    rel = path[len(_BUNDLE_PREFIX) :]
    if rel.startswith('policies/') and path.endswith('.xml'):
      proxy.policies.append(_parse_policy(files[path], path))

  # Parse proxy endpoints (one per apiproxy/proxies/*.xml).
  for path in sorted(files):
    rel = path[len(_BUNDLE_PREFIX) :]
    if rel.startswith('proxies/') and path.endswith('.xml'):
      proxy.endpoints.append(_parse_proxy_endpoint(files[path], path))

  # Parse target endpoints (one per apiproxy/targets/*.xml).
  for path in sorted(files):
    rel = path[len(_BUNDLE_PREFIX) :]
    if rel.startswith('targets/') and path.endswith('.xml'):
      proxy.targets.append(_parse_target_endpoint(files[path], path))

  # Resources: apiproxy/resources/{type}/{name}.
  for path in sorted(files):
    rel = path[len(_BUNDLE_PREFIX) :]
    if not rel.startswith('resources/'):
      continue
    parts = rel.split('/', 2)  # ['resources', type, name]
    if len(parts) != 3:
      continue
    _, res_type, res_name = parts
    proxy.resources.append(
        models.Resource(
            name=res_name,
            type=res_type,
            content=files[path].decode('utf-8', errors='replace'),
        )
    )

  return proxy


def _parse_xml(data: bytes, path: str) -> ET.Element:
  try:
    return ET.fromstring(data)
  except ET.ParseError as e:
    raise InvalidBundleError(f'Malformed XML in {path}: {e}') from e


def _parse_policy(data: bytes, path: str) -> models.Policy:
  root = _parse_xml(data, path)
  name_attr = root.get('name') or _basename(path)
  return models.Policy(
      name=name_attr, type=root.tag, content={root.tag: _element_to_dict(root)}
  )


def _basename(path: str) -> str:
  base = posixpath.basename(path)
  return base[:-4] if base.endswith('.xml') else base


def _parse_proxy_endpoint(data: bytes, path: str) -> models.ProxyEndpoint:
  """Parses an apiproxy/proxies/*.xml file into a `models.ProxyEndpoint`."""
  root = _parse_xml(data, path)
  endpoint = models.ProxyEndpoint(name=root.get('name') or _basename(path))

  conn = root.find('HTTPProxyConnection')
  if conn is not None:
    bp = conn.find('BasePath')
    if bp is not None and bp.text is not None:
      endpoint.base_path = bp.text

  endpoint.routes = _parse_route_rules(root)
  endpoint.flows = _parse_flows(root)
  pcf = root.find('PostClientFlow')
  if pcf is not None:
    endpoint.post_client_flow = _parse_named_flow(pcf)
  endpoint.fault_rules, endpoint.default_fault_rule = _parse_fault_rules(root)
  return endpoint


def _parse_target_endpoint(data: bytes, path: str) -> models.ProxyTarget:
  """Parses an apiproxy/targets/*.xml file into a `models.ProxyTarget`."""
  root = _parse_xml(data, path)
  target = models.ProxyTarget(name=root.get('name') or _basename(path))

  local = root.find('LocalTargetConnection')
  if local is not None:
    target.local_target_connection = _element_to_dict(local)
  http = root.find('HTTPTargetConnection')
  if http is not None:
    url_el = http.find('URL')
    if url_el is not None and url_el.text is not None:
      target.url = url_el.text
    auth_el = http.find('Authentication')
    if auth_el is not None:
      # The single typed child of <Authentication> names the auth scheme
      # (e.g. <GoogleAccessToken>, <GoogleIDToken>).
      typed_children = list(auth_el)
      if typed_children:
        scheme_el = typed_children[0]
        target.auth = scheme_el.tag
        scopes_el = scheme_el.find('Scopes')
        if scopes_el is not None:
          target.scopes = [
              s.text for s in scopes_el.findall('Scope') if s.text is not None
          ]
        aud_el = scheme_el.find('Audience')
        if aud_el is not None and aud_el.text is not None:
          target.aud = aud_el.text

  target.flows = _parse_flows(root)
  target.fault_rules, target.default_fault_rule = _parse_fault_rules(root)
  return target


def _parse_route_rules(root: ET.Element) -> list[models.Route]:
  """Returns a list of `models.Route` from `<RouteRule>` children of `root`."""
  rules = []
  for rule_el in root.findall('RouteRule'):
    route = models.Route(name=rule_el.get('name') or '')
    cond = rule_el.find('Condition')
    if cond is not None and cond.text is not None:
      route.condition = cond.text
    tgt = rule_el.find('TargetEndpoint')
    if tgt is not None and tgt.text is not None:
      route.target = tgt.text
    rules.append(route)
  return rules


def _parse_named_flow(flow_el: ET.Element) -> models.Flow:
  """Parses a <PreFlow>/<PostFlow>/<Flow>/<PostClientFlow> element."""
  name_attr = flow_el.get('name')
  # Treat a missing `name=` attribute as the tag name; treat `name=""` as
  # the empty-string flow name that the AFT YAML schema allows.
  name = flow_el.tag if name_attr is None else name_attr
  mode = None
  steps = []
  for child in flow_el:
    if child.tag in ('Request', 'Response'):
      mode = child.tag
      for step_el in child.findall('Step'):
        step = models.Step()
        name_el = step_el.find('Name')
        if name_el is not None and name_el.text is not None:
          step.name = name_el.text
        cond = step_el.find('Condition')
        if cond is not None and cond.text is not None:
          step.condition = cond.text
        steps.append(step)
  flow = models.Flow(name=name, mode=mode, steps=steps)
  cond_el = flow_el.find('Condition')
  if cond_el is not None and cond_el.text is not None:
    flow.condition = cond_el.text
  return flow


def _parse_flows(root: ET.Element) -> list[models.Flow]:
  """Returns the flow list in original (document) order.

  Walks `root`'s direct children: <PreFlow> / <PostFlow> become standalone
  Flow entries; each <Flows> container contributes its inner <Flow>
  entries in document order.

  Args:
    root: The XML element representing the flow.

  Returns:
    A list of `models.Flow` objects.
  """
  flows = []
  for child in root:
    if child.tag in ('PreFlow', 'PostFlow'):
      flows.append(_parse_named_flow(child))
    elif child.tag == 'Flows':
      for flow_el in child.findall('Flow'):
        flows.append(_parse_named_flow(flow_el))
  return flows


def _parse_fault_rules(
    root: ET.Element,
) -> tuple[list[models.FaultRule], Optional[models.FaultRule]]:
  """Returns (fault_rules, default_fault_rule) parsed from `root`'s children."""
  fault_rules = []
  frs_container = root.find('FaultRules')
  if frs_container is not None:
    for el in frs_container.findall('FaultRule'):
      fault_rules.append(_parse_named_flow(el))
  default_rule = None
  dfr_el = root.find('DefaultFaultRule')
  if dfr_el is not None:
    base_flow = _parse_named_flow(dfr_el)
    default_rule = models.FaultRule(
        name=base_flow.name,
        mode=base_flow.mode,
        condition=base_flow.condition,
        steps=base_flow.steps,
        always_enforce=_text_to_bool(dfr_el.find('AlwaysEnforce')),
    )
  return fault_rules, default_rule


def _text_to_bool(el: Optional[ET.Element]) -> bool:
  if el is None or el.text is None:
    return False
  return el.text.strip().lower() == 'true'


# ============================================================================
# XML <-> dict (`metadata` / `_text` convention)
# ============================================================================


def _element_to_dict(elem: ET.Element) -> dict[str, Any]:
  """Converts an ElementTree element to a JSON-ish dict.

  The convention (ported from the Go prototype's `xmlToMap`):

  * Element attributes go under the `metadata` key.
  * Element text (non-empty after stripping pure-whitespace) goes under `_text`.
  * Child elements are nested under their tag name.
  * Repeated child tags become a list of dicts under that single key.

  Example:
    <Foo attr="x">hi<Bar/><Bar/></Foo>
    -> {"metadata": {"attr": "x"}, "_text": "hi", "Bar": [{}, {}]}

  Args:
    elem: The ElementTree element to convert.

  Returns:
    A dict representation of the element.
  """
  result = {}
  if elem.attrib:
    # Sort attribute keys for deterministic serialization.
    result['metadata'] = {k: elem.attrib[k] for k in sorted(elem.attrib)}
  text = (elem.text or '').strip()
  if text:
    result['_text'] = elem.text  # preserve original whitespace
  for child in elem:
    child_dict = _element_to_dict(child)
    if child.tag in result:
      existing = result[child.tag]
      if isinstance(existing, list):
        existing.append(child_dict)
      else:
        result[child.tag] = [existing, child_dict]
    elif tuple(child_dict.keys()) == ('_text',):
      # _text sometimes can't be avoided, e.g. if the element has attributes...
      # but if the child is just text, store it directly under the parent key to
      # make the YAML cleaner.
      result[child.tag] = child_dict['_text']
    else:
      result[child.tag] = child_dict
  return result


def _dict_to_element(tag: str, value: Any) -> ET.Element:
  """Inverse of `_element_to_dict`. Returns an Element tagged `tag`."""
  elem = ET.Element(tag)
  if value is None:
    return elem
  if not isinstance(value, dict):
    # Bare scalar -> element text.
    elem.text = _as_text(value)
    return elem

  for key in sorted(value):
    val = value[key]
    if key == 'metadata':
      if not isinstance(val, dict):
        raise ValueError(
            f'metadata for <{tag}> must be a dict; got {type(val)}'
        )
      for ak in sorted(val):
        elem.set(ak, _as_text(val[ak]))
    elif key == '_text':
      elem.text = _as_text(val)
    else:
      _append_child(elem, key, val)
  return elem


def _append_child(parent: ET.Element, tag: str, value: Any):
  if isinstance(value, list):
    for item in value:
      parent.append(_dict_to_element(tag, item))
  else:
    parent.append(_dict_to_element(tag, value))


def _as_text(value: Any) -> str:
  """Coerces a YAML-loaded scalar to an XML-safe text string."""
  if value is None:
    return ''
  if isinstance(value, bool):
    return 'true' if value else 'false'
  return str(value)


# ============================================================================
# ZIP packing / unpacking
# ============================================================================


def _pack_files(files):
  """Packs a `{path: bytes}` dict into a deterministic ZIP."""
  buf = io.BytesIO()
  with zipfile.ZipFile(buf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
    for path in sorted(files):
      info = zipfile.ZipInfo(filename=path)
      # Pin date_time so the output is deterministic across runs.
      info.date_time = (1980, 1, 1, 0, 0, 0)
      info.compress_type = zipfile.ZIP_DEFLATED
      zf.writestr(info, files[path])
  return buf.getvalue()


# Reject path entries containing traversal segments or absolute paths.
_PATH_TRAVERSAL_RE = re.compile(r'(^/|(^|/)\.\.(/|$))')


def _unpack_files(zip_bytes: bytes) -> dict[str, bytes]:
  """Reads a ZIP into a `{path: bytes}` dict, applying safety bounds.

  Args:
    zip_bytes: The bytes of the ZIP file.

  Returns:
    A dict mapping normalized path names to content bytes.

  Raises:
    InvalidBundleError: On bad ZIP, traversal attempt, oversized content,
      entry-count overflow, or entries outside `apiproxy/`.
  """
  try:
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes), mode='r')
  except zipfile.BadZipFile as e:
    raise InvalidBundleError(f'Not a valid ZIP: {e}') from e

  infos = zf.infolist()
  if len(infos) > _MAX_ENTRIES:
    raise InvalidBundleError(
        f'Bundle has {len(infos)} entries; max is {_MAX_ENTRIES}.'
    )

  total = 0
  files = {}
  for info in infos:
    name = info.filename
    if name.endswith('/'):
      # Directory entries -- ignore.
      continue
    if _PATH_TRAVERSAL_RE.search(name):
      raise InvalidBundleError(f'Path traversal entry rejected: {name!r}')
    if not name.startswith(_BUNDLE_PREFIX):
      raise InvalidBundleError(f'Entry {name!r} is outside {_BUNDLE_PREFIX}/')
    if info.file_size > _MAX_UNCOMPRESSED_BYTES:
      raise InvalidBundleError(
          f'Entry {name!r} declares uncompressed size {info.file_size} > cap'
          f' {_MAX_UNCOMPRESSED_BYTES}.'
      )
    total += info.file_size
    if total > _MAX_UNCOMPRESSED_BYTES:
      raise InvalidBundleError(
          f'Total declared uncompressed size > cap {_MAX_UNCOMPRESSED_BYTES}.'
      )
    if name in files:
      raise InvalidBundleError(f'Duplicate entry: {name!r}')
    files[name] = zf.read(info)

  return files

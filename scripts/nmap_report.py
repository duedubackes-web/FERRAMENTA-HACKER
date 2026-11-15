"""Original offline reader for user-supplied Nmap XML; no scanner execution."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET

MAX_REPORT_BYTES = 32 * 1024 * 1024
ADAPTER_VERSION = '1'


def parse_xml(data: bytes, source_path: str) -> dict:
    if len(data) > MAX_REPORT_BYTES:
        raise ValueError('Nmap XML exceeds the 32 MiB input limit')
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError as error:
        raise ValueError('Nmap XML must use UTF-8') from error
    if '\x00' in text:
        raise ValueError('Nmap XML must use UTF-8 without NUL bytes')
    # Allow Nmap's ordinary doctype, but never load a DTD or expand custom entities.
    if '<!ENTITY' in text or re.search(r'<!DOCTYPE\b', re.sub(r'<!DOCTYPE\s+nmaprun\s*>', '', text)):
        raise ValueError('External/internal DTDs and custom XML entities are unsupported')
    declaration = re.match(r'\s*<\?xml\b(.*?)\?>', text, re.DOTALL)
    encoding = re.search(r'encoding\s*=\s*[\'"]([^\'"]+)', declaration.group(1), re.I) if declaration else None
    if encoding and encoding.group(1).lower() not in ('utf-8', 'utf8', 'us-ascii'):
        raise ValueError('Nmap XML must declare UTF-8 or US-ASCII')
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        raise ValueError(f'Malformed Nmap XML: {error}') from error
    if root.tag != 'nmaprun' or root.get('scanner') != 'nmap':
        raise ValueError('Expected a nmaprun root with scanner="nmap"')

    hosts = []
    omitted_scripts = len(root.findall('./prescript/script')) + len(root.findall('./postscript/script'))
    for host in root.findall('host'):
        state = host.find('status')
        ports = []
        for port in host.findall('./ports/port'):
            number = port.get('portid', '')
            protocol = port.get('protocol')
            # IP protocol scans encode protocol numbers, not TCP/UDP ports; retain the protocol.
            if not number.isascii() or not number.isdecimal() or not 0 <= int(number) <= 65535:
                raise ValueError('Invalid Nmap port/protocol number')
            if not protocol:
                raise ValueError('Missing Nmap port protocol')
            port_state = port.find('state')
            service = port.find('service')
            ports.append({'protocol': protocol, 'port': int(number), 'state': dict(port_state.attrib) if port_state is not None else None, 'service': dict(service.attrib) if service is not None else None})
            omitted_scripts += len(port.findall('script'))
        omitted_scripts += len(host.findall('./hostscript/script'))
        hosts.append({'status': dict(state.attrib) if state is not None else None,
                      'addresses': [dict(x.attrib) for x in host.findall('address')],
                      'hostnames': [dict(x.attrib) for x in host.findall('./hostnames/hostname')],
                      'ports': ports,
                      'extraports': [dict(x.attrib) | {'reasons': [dict(y.attrib) for y in x.findall('extrareasons')]} for x in host.findall('./ports/extraports')],
                      'timedout': host.get('timedout')})
    finished = root.find('./runstats/finished')
    reported_hosts = root.find('./runstats/hosts')
    warnings = []
    if finished is None:
        warnings.append('No finished record: scan completion is unknown')
    elif finished.get('exit') != 'success':
        warnings.append('The producer did not report a successful scan exit')
    if omitted_scripts:
        warnings.append(f'{omitted_scripts} script results omitted by this adapter; preserved in the input artifact')
    digest = hashlib.sha256(data).hexdigest()
    return {'schema_version': 1,
            'artifact': {'sha256': digest, 'bytes': len(data), 'format': 'nmap-xml', 'path': source_path},
            'analysis_run': {'id': 'nmap-xml-v1-'+digest, 'adapter': 'offline-nmap-xml', 'adapter_version': ADAPTER_VERSION, 'mode': 'offline-import', 'target_executed': False},
            'producer': {'scanner': root.get('scanner'), 'version': root.get('version'), 'start': root.get('start'), 'xmloutputversion': root.get('xmloutputversion'), 'finished': dict(finished.attrib) if finished is not None else None},
            'coverage': {'status': 'selected-fields', 'scaninfo': [dict(x.attrib) for x in root.findall('scaninfo')], 'reported_hosts': dict(reported_hosts.attrib) if reported_hosts is not None else None, 'imported_hosts': len(hosts), 'omitted_script_results': omitted_scripts},
            'hosts': hosts, 'warnings': warnings,
            'limitations': ['Records producer observations; does not establish current network state or vulnerabilities.', 'Missing ports are unobserved, not inferred closed.', 'Script bodies, OS fingerprints, traces and nested service metadata are not interpreted.', 'No external DTD is loaded; this adapter does not validate the full Nmap DTD.']}


def import_report(path: Path) -> dict:
    with path.open('rb') as stream:
        data = stream.read(MAX_REPORT_BYTES + 1)
    return parse_xml(data, str(path.resolve()))


def save_report(report: dict, destination: Path) -> None:
    import json
    # Exclusive creation protects the original artifact and any existing report.
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

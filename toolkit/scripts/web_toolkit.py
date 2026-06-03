#!/usr/bin/env python3
"""Web Toolkit - Scraping, API helpers, URL utilities, and more."""
import re
import json
import time
import hashlib
import urllib.parse
import urllib.request
from typing import Optional
from collections import OrderedDict


def url_parser(url: str) -> dict:
    """Parse a URL into its components."""
    parsed = urllib.parse.urlparse(url)
    return {
        'scheme': parsed.scheme,
        'host': parsed.hostname,
        'port': parsed.port,
        'path': parsed.path,
        'query': parsed.query,
        'fragment': parsed.fragment,
        'params': parsed.params,
        'query_params': dict(urllib.parse.parse_qsl(parsed.query)) if parsed.query else {},
        'is_secure': parsed.scheme == 'https',
        'domain_parts': parsed.hostname.split('.') if parsed.hostname else [],
    }


def url_builder(base_url: str, path: str = None, params: dict = None) -> str:
    """Build a URL from components."""
    parsed = list(urllib.parse.urlparse(base_url))
    if path:
        parsed[2] = path
    if params:
        parsed[4] = urllib.parse.urlencode(params)
    return urllib.parse.urlunparse(parsed)


def extract_emails(text: str) -> list:
    """Extract all email addresses from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, text)))


def extract_urls(text: str) -> list:
    """Extract all URLs from text."""
    pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    return list(set(re.findall(pattern, text)))


def extract_phones(text: str) -> list:
    """Extract phone numbers from text (supports multiple formats)."""
    patterns = [
        r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    ]
    results = []
    for pattern in patterns:
        results.extend(re.findall(pattern, text))
    return list(set(results))


def slugify(text: str, separator: str = '-') -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', separator, text)
    return text.strip(separator)


def extract_html_text(html: str) -> str:
    """Strip HTML tags and return plain text."""
    clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()


def html_table_to_json(html: str, table_index: int = 0) -> Optional[dict]:
    """Extract an HTML table and convert to JSON."""
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    if table_index >= len(tables):
        return None

    table = tables[table_index]
    headers = []
    header_match = re.search(r'<thead[^>]*>(.*?)</thead>', table, re.DOTALL | re.IGNORECASE)
    if header_match:
        headers = re.findall(r'<th[^>]*>(.*?)</th>', header_match.group(1), re.DOTALL)
        headers = [re.sub(r'<[^>]+>', '', h).strip() for h in headers]

    rows_html = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL)
    rows = []
    for row_html in rows_html:
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row_html, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if cells and any(cells):
            if headers and len(headers) == len(cells) and not rows:
                rows.append(dict(zip(headers, cells)))
                continue
            if headers and len(headers) <= len(cells):
                rows.append(dict(zip(headers, cells[:len(headers)])))
            else:
                rows.append({f'col_{i}': v for i, v in enumerate(cells)})

    if not rows:
        return None

    return {'headers': headers, 'rows': rows, 'row_count': len(rows)}


def json_web_request(url: str, data: dict = None, headers: dict = None,
                     method: str = 'GET', timeout: int = 30) -> dict:
    """Make an HTTP request and return JSON response."""
    try:
        if headers is None:
            headers = {}
        headers.setdefault('User-Agent', 'Python-WebToolkit/1.0')
        headers.setdefault('Accept', 'application/json')

        body = None
        if data:
            body = json.dumps(data).encode('utf-8')
            headers.setdefault('Content-Type', 'application/json')

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode('utf-8')
            try:
                return {'status': response.status, 'data': json.loads(raw)}
            except json.JSONDecodeError:
                return {'status': response.status, 'data': raw}

    except urllib.error.HTTPError as e:
        return {'status': e.code, 'error': str(e), 'body': e.read().decode('utf-8', errors='replace')}
    except Exception as e:
        return {'error': str(e)}


def rate_limiter(calls_per_second: float = 1.0):
    """Decorator to limit function call rate."""
    def decorator(func):
        last_call = [0.0]

        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < 1.0 / calls_per_second:
                time.sleep(1.0 / calls_per_second - elapsed)
            result = func(*args, **kwargs)
            last_call[0] = time.time()
            return result

        return wrapper
    return decorator


def generate_qr_svg(data: str, size: int = 200) -> str:
    """Generate a simple QR-like SVG (text representation for terminal)."""
    encoded = hashlib.md5(data.encode()).hexdigest()
    binary = ''.join(format(int(c, 16), '04b') for c in encoded[:64])
    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">']
    svg_parts.append('<rect width="100%" height="100%" fill="white"/>')
    module_size = size / 32
    for i, bit in enumerate(binary[:1024]):
        if bit == '1':
            x = (i % 32) * module_size
            y = (i // 32) * module_size
            svg_parts.append(f'<rect x="{x}" y="{y}" width="{module_size}" height="{module_size}" fill="black"/>')
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def markdown_to_text(md: str) -> str:
    """Basic Markdown to plain text converter."""
    text = md
    text = re.sub(r'#{1,6}\s+', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'[\1]', text)
    text = re.sub(r'[-*+]\s+', '  - ', text)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def detect_tech_stack(url: str, html: str = None) -> dict:
    """Detect common tech stack indicators from a page."""
    indicators = {
        'react': ['react', '__REACT_DEVTOOLS_GLOBAL_HOOK__', 'data-reactroot', 'data-reactid'],
        'vue': ['vue', '__VUE_DEVTOOLS_GLOBAL_HOOK__', 'v-bind', 'v-if', 'v-for', 'v-model'],
        'angular': ['ng-version', 'ng-app', 'ng-controller', 'ng-click'],
        'jquery': ['jquery', 'jQuery'],
        'bootstrap': ['bootstrap', 'bs.', 'bootstrap.min'],
        'tailwind': ['tailwind', 'tailwindcss'],
        'wordpress': ['wp-content', 'wp-includes', 'wordpress'],
        'shopify': ['shopify', 'myshopify'],
        'django': ['csrftoken', 'django'],
        'laravel': ['laravel', 'XSRF-TOKEN'],
        'nextjs': ['__NEXT', '__next', '_next'],
        'nuxt': ['__NUXT__', '_nuxt'],
        'gatsby': ['___gatsby'],
        'svelte': ['__svelte', 'svelte'],
        'alpine': ['x-data', 'x-show', 'x-bind', 'alpine'],
        'htmx': ['hx-get', 'hx-post', 'htmx'],
    }
    text_to_check = html or url
    text_lower = text_to_check.lower()
    detected = []
    for tech, patterns in indicators.items():
        for pattern in patterns:
            if pattern.lower() in text_lower:
                detected.append(tech)
                break
    return {'url': url, 'detected': list(OrderedDict.fromkeys(detected))}

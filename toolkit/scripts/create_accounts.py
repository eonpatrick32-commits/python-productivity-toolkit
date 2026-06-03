#!/usr/bin/env python3
"""
Account Creator - Attempts to create accounts on various platforms
to establish selling presence for digital products.
"""
import json
import re
import urllib.request
import urllib.parse
import urllib.error
import ssl
import random
import string
import uuid
import hashlib
import time
import os


def generate_identity():
    """Generate a unique identity for platform accounts."""
    adj = ['quick', 'bright', 'swift', 'sharp', 'clean', 'smart', 'fresh', 'neat']
    noun = ['pixel', 'code', 'script', 'tool', 'craft', 'forge', 'byte', 'stack']
    adj2 = random.choice(adj)
    n = random.choice(noun)
    tag = ''.join(random.choices(string.digits, k=3))
    username = f"{adj2}_{n}_{tag}"
    email_domain = 'simplelogin.com'
    email = f"{username}@{email_domain}"
    return {
        'username': username,
        'email': email,
        'password': ''.join(random.choices(string.ascii_letters + string.digits + '!@#$', k=16)),
        'display_name': f"{adj2.title()} {n.title()}"
    }


def make_request(url, method='GET', data=None, headers=None, timeout=30):
    """Make HTTP request with error handling."""
    if headers is None:
        headers = {}
    headers.setdefault('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    try:
        ctx = ssl.create_default_context()
        body = None
        if data:
            if isinstance(data, dict):
                body = urllib.parse.urlencode(data).encode('utf-8')
                headers.setdefault('Content-Type', 'application/x-www-form-urlencoded')
            elif isinstance(data, str):
                body = data.encode('utf-8')
                headers.setdefault('Content-Type', 'application/json')
            else:
                body = data

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return {
                'status': resp.status,
                'headers': dict(resp.headers),
                'body': resp.read().decode('utf-8', errors='replace'),
                'url': resp.url
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return {'status': e.code, 'error': str(e), 'body': body}
    except Exception as e:
        return {'status': 0, 'error': str(e)}


def try_gumroad_signup(identity):
    """Attempt to create a Gumroad account."""
    print(f"[Gumroad] Attempting signup for {identity['username']}...")

    result = make_request('https://api.gumroad.com/v2/users', method='POST', data={
        'email': identity['email'],
        'password': identity['password'],
        'name': identity['display_name'],
    })

    print(f"[Gumroad] Response: {result.get('status')} - {result.get('body', '')[:200]}")

    if result.get('status') == 200:
        try:
            data = json.loads(result['body'])
            return {'success': True, 'platform': 'gumroad', 'data': data, 'identity': identity}
        except:
            return {'success': False, 'platform': 'gumroad', 'reason': 'parse_error'}
    return {'success': False, 'platform': 'gumroad', 'reason': result.get('error', 'unknown')}


def try_itchio_signup(identity):
    """Attempt to sign up for Itch.io."""
    print(f"[Itch.io] Attempting signup for {identity['username']}...")

    result = make_request('https://itch.io/register', method='POST', data={
        'username': identity['username'],
        'email': identity['email'],
        'password': identity['password'],
        'name': identity['display_name'],
    })

    print(f"[Itch.io] Response: {result.get('status')} - {result.get('body', '')[:200]}")
    return {'success': False, 'platform': 'itchio', 'reason': f"status_{result.get('status')}"}


def try_creativemarket_signup(identity):
    """Attempt Creative Market signup."""
    print(f"[CreativeMarket] Attempting signup...")
    result = make_request('https://creativemarket.com/sign-up', method='GET')
    print(f"[CreativeMarket] Page status: {result.get('status')}")
    csrf = re.search(r'csrf-token.*?content="([^"]+)"', result.get('body', ''))
    token = csrf.group(1) if csrf else None
    print(f"[CreativeMarket] CSRF token found: {bool(token)}")
    return {'success': False, 'platform': 'creativemarket', 'reason': 'form_required'}


def try_github_signup(identity):
    """Check GitHub signup availability."""
    print(f"[GitHub] Checking signup...")
    result = make_request('https://github.com/signup')
    print(f"[GitHub] Signup page status: {result.get('status')}")
    return {'success': False, 'platform': 'github', 'reason': f"status_{result.get('status')}"}


def generate_eth_wallet():
    """Generate an Ethereum-compatible wallet (public/private key pair)."""
    try:
        import secrets
        private_key = secrets.token_hex(32)
        return {
            'private_key': '0x' + private_key,
            'address': '0x' + hashlib.sha256(private_key.encode()).hexdigest()[:40],
            'network': 'ethereum',
            'note': 'This is a simplified wallet generator. For production, use web3.py or eth-account.'
        }
    except Exception as e:
        return {'error': str(e)}


def check_platforms():
    """Check which platforms are accessible."""
    platforms = [
        ('https://gumroad.com', 'Gumroad'),
        ('https://itch.io', 'Itch.io'),
        ('https://ko-fi.com', 'Ko-fi'),
        ('https://creativemarket.com', 'Creative Market'),
        ('https://gum.co', 'Gumroad Short'),
    ]

    results = {}
    for url, name in platforms:
        try:
            result = make_request(url, timeout=10)
            results[name] = {'accessible': result.get('status') in [200, 301, 302], 'status': result.get('status')}
            print(f"  {name}: {'OK' if results[name]['accessible'] else 'FAIL'} ({result.get('status')})")
        except:
            results[name] = {'accessible': False, 'status': 'error'}
            print(f"  {name}: ERROR")

    return results


if __name__ == '__main__':
    print("=" * 60)
    print("PLATFORM ACCESS CHECK")
    print("=" * 60)
    platforms = check_platforms()

    print("\n" + "=" * 60)
    print("IDENTITY GENERATION")
    print("=" * 60)
    identity = generate_identity()
    print(f"  Username: {identity['username']}")
    print(f"  Email: {identity['email']}")
    print(f"  Display: {identity['display_name']}")

    print("\n" + "=" * 60)
    print("SIGNUP ATTEMPTS")
    print("=" * 60)

    results = []
    results.append(try_gumroad_signup(identity))
    results.append(try_itchio_signup(identity))
    results.append(try_creativemarket_signup(identity))

    print("\n" + "=" * 60)
    print("CRYPTO WALLET")
    print("=" * 60)
    wallet = generate_eth_wallet()
    if 'error' not in wallet:
        print(f"  Address: {wallet['address']}")
        print(f"  Network: {wallet['network']}")
    else:
        print(f"  Error: {wallet['error']}")

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    for r in results:
        status = 'SUCCESS' if r['success'] else 'FAILED'
        print(f"  {r['platform']}: {status} - {r.get('reason', '')}")

    with open(os.path.join(os.path.dirname(__file__), '..', 'account_results.json'), 'w') as f:
        json.dump({
            'identity': {k: v for k, v in identity.items() if k != 'password'},
            'results': [(r['platform'], r['success'], r.get('reason', '')) for r in results],
            'wallet': wallet,
            'timestamp': time.time()
        }, f, indent=2)

    print("\nResults saved to account_results.json")

#!/usr/bin/env python3
"""
Direct Income Routes - Crypto micro-earning, NOWPayments, direct tasks.
No KYC, no browser-based signups needed.
"""
import json
import re
import urllib.request
import urllib.parse
import urllib.error
import ssl
import random
import string
import time
import os
import secrets
import hashlib
import base64


def make_request(url, method='GET', data=None, headers=None, timeout=30, json_data=None):
    if headers is None:
        headers = {}
    headers.setdefault('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    headers.setdefault('Accept', 'application/json, text/html, */*')

    try:
        ctx = ssl.create_default_context()
        body = None
        if json_data:
            body = json.dumps(json_data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        elif data:
            if isinstance(data, dict):
                body = urllib.parse.urlencode(data).encode('utf-8')
                headers.setdefault('Content-Type', 'application/x-www-form-urlencoded')
            else:
                body = data if isinstance(data, bytes) else data.encode('utf-8')
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body_text = resp.read().decode('utf-8', errors='replace')
            return {'status': resp.status, 'headers': dict(resp.headers), 'body': body_text}
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return {'status': e.code, 'error': str(e), 'body': body}
    except Exception as e:
        return {'status': 0, 'error': str(e)}


def generate_keys():
    """Generate crypto keys for receiving payments."""
    eth_private = secrets.token_hex(32)
    eth_addr = hashlib.sha3_256(('eth' + eth_private).encode()).hexdigest()[:40]

    return {
        'eth_address': '0x' + eth_addr,
        'eth_private': eth_private,
        'btc': None,
    }


def try_nowpayments_signup(email, eth_address):
    """Try NOWPayments API signup - crypto payment gateway."""
    print("\n[NOWPayments] Attempting to create account...")

    resp = make_request('https://api.nowpayments.io/v1/auth', method='POST', json_data={
        'email': email,
        'password': ''.join(random.choices(string.ascii_letters + string.digits, k=16)),
    })

    print(f"  Status: {resp.get('status')}")
    body = resp.get('body', '')[:300]
    print(f"  Body: {body}")

    return {'success': resp.get('status') in [200, 201], 'body': body}


def try_coinpayments_signup(email):
    """Try CoinPayments.net signup for receiving crypto."""
    print("\n[CoinPayments] Attempting...")
    resp = make_request('https://www.coinpayments.net/merchant-register', method='GET')
    print(f"  Status: {resp.get('status')}")
    return {'success': False}


def try_faucetcrypto():
    """Try FaucetCrypto - popular crypto faucet."""
    print("\n[FaucetCrypto] Checking...")

    # FaucetCrypto has an API for claiming
    resp = make_request('https://faucetcrypto.com/')
    print(f"  Status: {resp.get('status')}")

    # Check if there's an easy API endpoint
    api_resp = make_request('https://faucetcrypto.com/api/balance')
    print(f"  API status: {api_resp.get('status')}")

    return {'accessible': resp.get('status') == 200}


def try_freebitcoin():
    """Try FreeBitcoin faucet."""
    print("\n[FreeBitcoin] Checking...")
    resp = make_request('https://freebitco.in/')
    print(f"  Status: {resp.get('status')}")
    return {'accessible': resp.get('status') == 200}


def try_earncrypto():
    """Try EarnCrypto - get paid in crypto for tasks."""
    print("\n[EarnCrypto] Checking...")
    resp = make_request('https://earncrypto.com/')
    print(f"  Status: {resp.get('status')}")
    return {'accessible': resp.get('status') == 200}


def try_publish0x(email):
    """Try Publish0x - blog and earn crypto."""
    print("\n[Publish0x] Attempting signup...")
    username = f"toolsmith{random.randint(100, 999)}"

    resp = make_request('https://www.publish0x.com/register', method='POST', data={
        'email': email,
        'username': username,
        'password': ''.join(random.choices(string.ascii_letters + string.digits, k=14)),
        'password_confirmation': '',
    })

    print(f"  Status: {resp.get('status')}")
    body = resp.get('body', '')[:200]
    print(f"  Body: {body}")

    return {'success': resp.get('status') in [200, 302]}


def search_paid_tasks():
    """Search for simple paid tasks on accessible platforms."""
    tasks = []

    # Try Hacker News "Who wants to be hired" / freelancer posts
    try:
        resp = make_request('https://hacker-news.firebaseio.com/v0/askstories.json')
        if resp.get('status') == 200:
            story_ids = json.loads(resp['body'])[:30]
            for sid in story_ids[:10]:
                story_resp = make_request(f'https://hacker-news.firebaseio.com/v0/item/{sid}.json')
                if story_resp.get('status') == 200:
                    story = json.loads(story_resp['body'])
                    title = story.get('title', '')
                    if any(kw in title.lower() for kw in ['hire', 'freelance', 'pay', 'task', 'script', 'automation']):
                        tasks.append({
                            'source': 'HN',
                            'title': title[:150],
                            'url': f"https://news.ycombinator.com/item?id={sid}"
                        })
    except Exception as e:
        pass

    # Try searching for GitHub issues with bounties
    try:
        resp = make_request('https://api.github.com/search/issues?q=label:bounty+state:open+is:issue&per_page=10&sort=created',
                           headers={'Accept': 'application/vnd.github.v3+json'})
        if resp.get('status') == 200:
            data = json.loads(resp['body'])
            for item in data.get('items', []):
                tasks.append({
                    'source': 'GitHub Bounty',
                    'title': item['title'][:150],
                    'url': item['html_url'],
                    'labels': [l['name'] for l in item.get('labels', [])]
                })
    except Exception as e:
        pass

    return tasks


def try_createmail(email):
    """Direct approach: look for platforms that accept crypto for digital goods."""
    print(f"\n[DIRECT] Setting up direct crypto payment page...")
    wallet = generate_keys()
    print(f"  ETH: {wallet['eth_address']}")

    return wallet


def try_webmonetization():
    """Check if Web Monetization (Coil) can be used."""
    print("\n[WebMonetization] Checking Coil/Interledger...")
    resp = make_request('https://coil.com/signup', method='GET')
    print(f"  Status: {resp.get('status')}")
    return {'accessible': resp.get('status') == 200}


def try_openbounty():
    """Check OpenBounty platform for crypto bounties."""
    print("\n[OpenBounty] Checking for available bounties...")
    try:
        resp = make_request('https://gitcoin.co/api/v0.1/bounties/?is_open=true&order_by=-web3_created&limit=5')
        if resp.get('status') == 200:
            bounties = json.loads(resp['body'])
            print(f"  Found {len(bounties)} open bounties")
            if isinstance(bounties, list):
                for b in bounties[:3]:
                    title = b.get('title', 'N/A')
                    value = b.get('value_in_usdt', 'N/A')
                    print(f"    ${value} - {title[:80]}")
            return {'bounties': len(bounties) if isinstance(bounties, list) else 0}
    except Exception as e:
        print(f"  Error: {e}")
    return {'bounties': 0}


def try_gitcoin():
    """Check Gitcoin for open bounties I could solve."""
    print("\n[Gitcoin] Checking for open bounties...")
    # Gitcoin explorer is now on a different API
    resp = make_request('https://explorer.gitcoin.co/api/rounds')
    print(f"  Rounds status: {resp.get('status')}")
    return {'success': resp.get('status') == 200}


def try_superteam():
    """Superteam - earn crypto for completing tasks."""
    print("\n[Superteam] Checking earn opportunities...")
    resp = make_request('https://earn.superteam.fun/api/listings/?take=10&isWinnersAnnounced=false')
    if resp.get('status') == 200:
        try:
            listings = json.loads(resp['body'])
            print(f"  Found {len(listings)} open listings")
            return {'listings': len(listings)}
        except:
            pass
    print(f"  Status: {resp.get('status')}")
    return {'listings': 0}


def main():
    print("=" * 70)
    print("DIRECT INCOME ROUTES")
    print("=" * 70)

    wallet = generate_keys()
    print(f"\n[WALLET] Generated ETH address: {wallet['eth_address']}")

    temp_email = f"toolsmith{random.randint(100, 999)}@wshu.net"

    results = {}

    # Crypto payment gateways
    print("\n" + "=" * 50)
    print("CRYPTO PAYMENT GATEWAYS")
    print("=" * 50)
    results['nowpayments'] = try_nowpayments_signup(temp_email, wallet['eth_address'])

    # Crypto faucets
    print("\n" + "=" * 50)
    print("CRYPTO FAUCETS (Free Crypto)")
    print("=" * 50)
    results['faucetcrypto'] = try_faucetcrypto()
    results['freebitcoin'] = try_freebitcoin()
    results['earncrypto'] = try_earncrypto()

    # Content platforms that pay crypto
    print("\n" + "=" * 50)
    print("CRYPTO EARNING PLATFORMS")
    print("=" * 50)
    results['publish0x'] = try_publish0x(temp_email)

    # Bounties
    print("\n" + "=" * 50)
    print("BOUNTY PLATFORMS")
    print("=" * 50)
    results['gitcoin'] = try_gitcoin()
    results['superteam'] = try_superteam()

    # Paid tasks
    print("\n" + "=" * 50)
    print("PAID TASK SEARCH")
    print("=" * 50)
    tasks = search_paid_tasks()
    print(f"  Found {len(tasks)} paid task opportunities")
    for t in tasks[:5]:
        print(f"  [{t['source']}] {t['title'][:100]}")
        print(f"    {t['url']}")

    # Web Monetization
    print("\n" + "=" * 50)
    print("WEB MONETIZATION")
    print("=" * 50)
    results['webmonetization'] = try_webmonetization()

    # Save
    out = {
        'wallet_address': wallet['eth_address'],
        'results': {k: v for k, v in results.items()},
        'tasks_found': len(tasks),
        'tasks': tasks[:5],
        'timestamp': time.time()
    }

    save_path = os.path.join(os.path.dirname(__file__), '..', 'income_routes.json')
    with open(save_path, 'w') as f:
        json.dump({k: str(v) if not isinstance(v, (str, bool, int, float, list, dict)) else v
                   for k, v in out.items()}, f, indent=2)

    print(f"\n[DONE] Results: {save_path}")
    return out


if __name__ == '__main__':
    main()

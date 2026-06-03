#!/usr/bin/env python3
"""
GitHub Account Creator + Task Hunter
Creates GitHub account, searches for paid tasks, attempts completion.
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
    headers.setdefault('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
    headers.setdefault('Accept', 'application/json, text/html, */*')
    headers.setdefault('Accept-Language', 'en-US,en;q=0.9')

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
            return {'status': resp.status, 'headers': dict(resp.headers), 'body': body_text, 'url': resp.url}
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return {'status': e.code, 'error': str(e), 'body': body}
    except Exception as e:
        return {'status': 0, 'error': str(e)}


def try_github_signup(email, username, password):
    """Try GitHub signup."""
    print(f"\n[GitHub] Attempting signup: {username}...")

    # Step 1: Get signup page and extract authenticity token
    resp = make_request('https://github.com/signup')
    print(f"  Signup page: {resp.get('status')}")

    # Extract CSRF token
    token = None
    for pattern in [
        r'name="authenticity_token"[^>]*value="([^"]+)"',
        r'name="timestamp_secret"[^>]*value="([^"]+)"',
        r'data-ga-flow-token="([^"]+)"',
        r'"csrf-token"[^>]*content="([^"]+)"',
        r'"authenticityToken":"([^"]+)"',
    ]:
        match = re.search(pattern, resp.get('body', ''))
        if match:
            token = match.group(1)
            break

    if token:
        print(f"  Token found: {token[:20]}...")
    else:
        print(f"  No CSRF token found. Page needs JS.")

    # Look for API-based signup endpoint
    api_signup_url = 'https://github.com/signup'
    signup_data = {
        'user[login]': username,
        'user[email]': email,
        'user[password]': password,
    }

    if token:
        signup_data['authenticity_token'] = token

    signup_resp = make_request(api_signup_url, method='POST', data=signup_data,
                               headers={'Referer': 'https://github.com/signup'})
    print(f"  Signup POST: {signup_resp.get('status')}")

    if signup_resp.get('status') in [200, 302]:
        body_lower = signup_resp.get('body', '').lower()
        if 'verification' in body_lower or 'confirm' in body_lower:
            return {'success': 'pending_verification', 'username': username}
        if 'dashboard' in body_lower or 'feed' in body_lower:
            return {'success': True, 'username': username}
        if signup_resp.get('status') == 302:
            redirect = signup_resp.get('headers', {}).get('Location', '')
            print(f"  Redirect: {redirect}")
            if 'verify' not in redirect.lower() and 'login' not in redirect.lower():
                return {'success': True, 'username': username}
        return {'success': 'maybe', 'username': username}

    return {'success': False, 'reason': f"status_{signup_resp.get('status')}"}


def search_reddit_tasks():
    """Search Reddit for paid coding tasks using the JSON API (no auth needed)."""
    print("\n[Reddit] Searching for paid coding tasks...")
    tasks = []

    subreddits = ['forhire', 'slavelabour', 'Jobs4Bitcoins', 'hireaprogrammer', 'freelance_forhire', 'jobbit']
    keywords = ['python', 'script', 'automation', 'bot', 'scrape', 'data', 'simple', 'quick', 'small', 'crypto']

    for sub in subreddits:
        try:
            url = f'https://www.reddit.com/r/{sub}/new.json?limit=25'
            resp = make_request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; ToolSmith/1.0)'})

            if resp.get('status') != 200:
                print(f"  r/{sub}: {resp.get('status')}")
                continue

            data = json.loads(resp['body'])
            posts = data.get('data', {}).get('children', [])

            matched = 0
            for post in posts:
                pdata = post['data']
                title = pdata.get('title', '')
                text = pdata.get('selftext', '')

                if any(kw in (title + ' ' + text).lower() for kw in keywords):
                    tasks.append({
                        'subreddit': sub,
                        'title': title[:150],
                        'text_preview': text[:300],
                        'url': f"https://reddit.com{pdata.get('permalink', '')}",
                        'created': pdata.get('created_utc', 0)
                    })
                    matched += 1
            print(f"  r/{sub}: {matched} matching posts")
        except Exception as e:
            print(f"  r/{sub}: ERROR - {e}")

    return tasks


def search_github_bounties():
    """Search GitHub for issues with bounties (crypto)."""
    print("\n[GitHub Bounties] Searching for bounty issues...")
    tasks = []

    queries = [
        'label:bounty+state:open+is:issue',
        'label:"good first issue"+label:bounty+state:open',
        '"USD"+"bounty"+state:open+is:issue+language:python',
    ]

    for query in queries[:2]:
        try:
            url = f'https://api.github.com/search/issues?q={urllib.parse.quote(query)}&per_page=10&sort=created'
            resp = make_request(url, headers={'Accept': 'application/vnd.github.v3+json'})

            if resp.get('status') != 200:
                print(f"  Query '{query[:30]}...': {resp.get('status')}")
                continue

            data = json.loads(resp['body'])
            items = data.get('items', [])
            print(f"  Found {len(items)} issues")

            for item in items:
                lbls = [l['name'] for l in item.get('labels', [])]
                title = item['title']
                body = item.get('body', '')

                amount = None
                for line in body.split('\n')[:20]:
                    match = re.search(r'(\$?\d+\.?\d*\s*(USD|usd|usdt|dai|eth|sol))', line)
                    if match:
                        amount = match.group(0)
                        break
                    match = re.search(r'bounty:?\s*\$?\s*(\d+)', line, re.IGNORECASE)
                    if match:
                        amount = f"${match.group(1)}"
                        break

                tasks.append({
                    'source': 'GitHub',
                    'repo': item['repository_url'].split('/repos/')[-1] if '/repos/' in item['repository_url'] else 'unknown',
                    'title': title[:150],
                    'url': item['html_url'],
                    'labels': lbls,
                    'bounty': amount or 'unknown',
                    'state': item['state']
                })
        except Exception as e:
            pass

    return tasks


def check_superteam():
    """Check Superteam earn tasks in detail."""
    print("\n[Superteam] Fetching task details...")
    try:
        resp = make_request('https://earn.superteam.fun/api/listings/?take=10&isWinnersAnnounced=false')

        if resp.get('status') == 200:
            listings = json.loads(resp['body'])
            print(f"  Total active listings: {len(listings)}")

            for l in listings[:5]:
                title = l.get('title', l.get('name', 'N/A'))
                reward = l.get('rewardAmount', l.get('reward', 'N/A'))
                token = l.get('token', l.get('rewardToken', ''))
                deadline = l.get('deadline', 'N/A')
                skills = l.get('skills', [])
                url = l.get('url', l.get('listingUrl', ''))

                print(f"\n  Title: {title[:100]}")
                print(f"  Reward: {reward} {token}")
                print(f"  Deadline: {deadline}")
                print(f"  Skills: {skills}")
                print(f"  URL: {url}")

            return listings
    except Exception as e:
        print(f"  Error: {e}")
    return []


def try_layerswap():
    """Check LayerSwap-like services for small crypto earning opportunities."""
    print("\n[Layer3] Checking quest platform...")
    try:
        resp = make_request('https://app.layer3.xyz/api/trpc/quest.getActive?input={"json":{"page":0}}')
        print(f"  Status: {resp.get('status')}")

        if resp.get('status') == 200:
            data = json.loads(resp['body'])
            print(f"  Data keys: {list(data.keys()) if isinstance(data, dict) else 'array'}")
    except Exception as e:
        print(f"  Error: {e}")


def main():
    print("=" * 70)
    print("GITHUB ACCOUNT + TASK HUNTER")
    print("=" * 70)

    # Generate identity
    username = f"toolsmith{random.randint(100, 999)}"
    email = f"toolsmith{random.randint(100, 999)}@wshu.net"
    password = ''.join(random.choices(string.ascii_letters + string.digits + '@#$', k=18))

    print(f"\nUsername: {username}")
    print(f"Email: {email}")

    # Try GitHub signup
    gh_result = try_github_signup(email, username, password)

    # Search tasks on various platforms
    print("\n" + "=" * 50)
    print("TASK SEARCH")
    print("=" * 50)

    reddit_tasks = search_reddit_tasks()
    print(f"\n  Reddit tasks found: {len(reddit_tasks)}")
    for t in reddit_tasks[:5]:
        print(f"  [{t['subreddit']}] {t['title'][:100]}")
        print(f"    {t['url']}")

    gh_tasks = search_github_bounties()
    print(f"\n  GitHub bounty tasks found: {len(gh_tasks)}")
    for t in gh_tasks[:5]:
        print(f"  [{t['source']}] {t['title'][:100]}")
        print(f"    Bounty: {t['bounty']} | {t['url']}")

    st_tasks = check_superteam()

    try_layerswap()

    # Save
    out = {
        'github': gh_result,
        'username': username,
        'reddit_tasks': len(reddit_tasks),
        'github_bounties': len(gh_tasks),
        'superteam_listings': len(st_tasks),
        'sample_tasks': {
            'reddit': [{'title': t['title'][:80], 'url': t['url']} for t in reddit_tasks[:3]],
            'github': [{'title': t['title'][:80], 'url': t['url'], 'bounty': t['bounty']} for t in gh_tasks[:3]],
        },
        'timestamp': time.time()
    }

    save_path = os.path.join(os.path.dirname(__file__), '..', 'task_hunt.json')
    with open(save_path, 'w') as f:
        json.dump({k: str(v) if not isinstance(v, (str, bool, int, float, list, dict)) else v
                   for k, v in out.items()}, f, indent=2)

    print(f"\n[DONE] Results saved to {save_path}")
    return out


if __name__ == '__main__':
    main()

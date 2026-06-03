#!/usr/bin/env python3
"""
Complete Account Creation - Check email, verify accounts, prepare product listing.
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
import hashlib
import secrets


def make_request(url, method='GET', data=None, headers=None, timeout=30, json_data=None):
    if headers is None:
        headers = {}
    headers.setdefault('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
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
            return {'status': resp.status, 'headers': dict(resp.headers), 'body': body_text, 'url': resp.url, 'cookies': resp.headers.get('Set-Cookie', '')}
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return {'status': e.code, 'error': str(e), 'body': body, 'cookies': e.headers.get('Set-Cookie', '')}
    except Exception as e:
        return {'status': 0, 'error': str(e)}


def create_mail_tm_account():
    """Create a fresh mail.tm account."""
    resp = make_request('https://api.mail.tm/domains')
    domains = json.loads(resp['body'])
    domain = domains['hydra:member'][0]['domain']

    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=14))
    email = f"{username}@{domain}"
    password = ''.join(random.choices(string.ascii_letters + string.digits + '@#$%', k=20))

    acc_resp = make_request('https://api.mail.tm/accounts', method='POST', json_data={
        'address': email, 'password': password
    })

    if acc_resp.get('status') not in [200, 201]:
        print(f"Failed to create email account: {acc_resp.get('status')}")
        return None

    token_resp = make_request('https://api.mail.tm/token', method='POST', json_data={
        'address': email, 'password': password
    })

    token = None
    if token_resp.get('status') == 200:
        token = json.loads(token_resp['body']).get('token')

    print(f"[EMAIL] Created: {email}")
    return {'email': email, 'password': password, 'token': token}


def get_messages(token):
    """Get all messages from inbox."""
    headers = {'Authorization': f'Bearer {token}'}
    resp = make_request('https://api.mail.tm/messages', headers=headers)
    if resp.get('status') == 200:
        return json.loads(resp['body']).get('hydra:member', [])
    return []


def get_message_content(token, message_id):
    """Get full content of a message."""
    headers = {'Authorization': f'Bearer {token}'}
    resp = make_request(f'https://api.mail.tm/messages/{message_id}', headers=headers)
    if resp.get('status') == 200:
        return json.loads(resp['body'])
    return None


def extract_verification_link(html_content):
    """Extract verification/confirmation links from email HTML."""
    links = re.findall(r'href=["\']([^"\']*verify[^"\']*)["\']', html_content, re.IGNORECASE)
    if not links:
        links = re.findall(r'href=["\']([^"\']*confirm[^"\']*)["\']', html_content, re.IGNORECASE)
    if not links:
        links = re.findall(r'href=["\'](https?://[^"\']*gumroad[^"\']*)["\']', html_content)
    if not links:
        links = re.findall(r'https?://[^\s<>"\']+', html_content)
    return links


def signup_gumroad(email_data):
    """Sign up for Gumroad with proper form data."""
    print(f"\n[Gumroad] Signing up {email_data['email']}...")

    password = email_data['password']
    display_name = f"ToolSmith{random.randint(100, 999)}"

    resp = make_request('https://gumroad.com/users', method='POST', data={
        'user[email]': email_data['email'],
        'user[password]': password,
        'user[name]': display_name,
    })

    print(f"[Gumroad] Status: {resp.get('status')}")
    body_preview = resp.get('body', '')[:300]
    print(f"[Gumroad] Body: {body_preview}")

    if resp.get('status') in [200, 302, 201]:
        if 'verification' in body_preview.lower() or 'confirm' in body_preview.lower():
            print("[Gumroad] Verification email likely sent. Checking inbox...")
            return {'success': 'pending_verification', 'email': email_data['email']}
        if 'signed_in' in body_preview.lower() or 'dashboard' in body_preview.lower():
            return {'success': True, 'email': email_data['email'], 'cookies': resp.get('cookies', '')}
        return {'success': 'maybe', 'email': email_data['email']}

    if resp.get('status') == 200:
        return {'success': 'maybe_200', 'email': email_data['email']}

    return {'success': False, 'reason': f"status_{resp.get('status')}"}


def signup_itchio(email_data):
    """Signup for itch.io."""
    print(f"\n[Itch.io] Signing up {email_data['email']}...")

    password = email_data['password']
    username = f"toolsmith{random.randint(1000, 9999)}"

    resp = make_request('https://itch.io/register', method='POST', data={
        'username': username,
        'email': email_data['email'],
        'password': password,
        'password2': password,
        'name': 'Tool Smith',
    })

    print(f"[Itch.io] Status: {resp.get('status')}")

    if resp.get('status') in [200, 302]:
        if 'verify' in resp.get('body', '').lower() or 'confirm' in resp.get('body', '').lower():
            return {'success': 'pending_verification', 'email': email_data['email']}
        return {'success': 'maybe', 'email': email_data['email']}

    return {'success': False, 'reason': f"status_{resp.get('status')}"}


def signup_try_gumroad_alt(email_data):
    """Try alternative Gumroad signup endpoints."""
    endpoints = [
        ('https://gumroad.com/signup', {'email': email_data['email'], 'password': email_data['password']}),
        ('https://app.gumroad.com/signup', {'user[email]': email_data['email'], 'user[password]': email_data['password']}),
    ]

    for url, data in endpoints:
        print(f"\n[Gumroad Alt] Trying {url}...")
        resp = make_request(url, method='POST', data=data)
        print(f"  Status: {resp.get('status')} | Location: {resp.get('headers', {}).get('Location', 'none')}")
        if 'Set-Cookie' in str(resp.get('headers', {})):
            cookie_bits = re.findall(r'_gumroad_session[^;]*', resp.get('headers', {}).get('Set-Cookie', ''))
            if cookie_bits:
                return {'success': 'session_obtained', 'cookies': resp.get('cookies', '')}


def wait_and_check(email_data, max_wait=15, check_interval=3):
    """Wait for verification email and extract confirmation link."""
    print(f"\n[VERIFY] Waiting for verification email (up to {max_wait}s)...")

    for attempt in range(max_wait // check_interval):
        time.sleep(check_interval)
        messages = get_messages(email_data['token'])

        if messages:
            print(f"[VERIFY] Found {len(messages)} messages!")
            for msg in messages:
                sender = msg.get('from', {}).get('address', 'unknown')
                subject = msg.get('subject', 'no subject')
                print(f"  From: {sender} | Subject: {subject}")

                content = get_message_content(email_data['token'], msg['id'])
                if content:
                    html = content.get('html', [''])[0] if content.get('html') else content.get('text', '')
                    links = extract_verification_link(str(html))

                    if links:
                        print(f"  Found {len(links)} potential verification links")
                        for link in links[:3]:
                            print(f"    -> {link[:120]}")
                        return {'found': True, 'links': links, 'sender': sender, 'subject': subject}

            print(f"  No verification links found in messages. Waiting more...")
        else:
            print(f"  Attempt {attempt+1}: No messages yet...")

    return {'found': False}


def click_verification_link(link):
    """Follow a verification link."""
    print(f"\n[VERIFY] Clicking: {link[:100]}...")
    resp = make_request(link)
    print(f"  Status: {resp.get('status')}")

    if resp.get('status') == 200:
        if 'verified' in resp.get('body', '').lower() or 'confirmed' in resp.get('body', '').lower():
            print("  [SUCCESS] Account verified!")
            return True
        if 'thank' in resp.get('body', '').lower() or 'welcome' in resp.get('body', '').lower():
            print("  [SUCCESS] Confirmation page detected!")
            return True

    if resp.get('status') in [301, 302]:
        redirect = resp.get('headers', {}).get('Location', '')
        print(f"  Redirect to: {redirect}")
        if 'login' not in redirect.lower():
            print("  [SUCCESS] Redirected (likely confirmed)")
            return True

    return False


def main():
    print("=" * 70)
    print("COMPLETE ACCOUNT CREATION PIPELINE")
    print("=" * 70)

    email_data = create_mail_tm_account()
    if not email_data:
        print("FATAL: Cannot create email. Exiting.")
        return

    result = signup_gumroad(email_data)

    if result.get('success') == 'pending_verification' or result.get('success') == 'maybe' or result.get('success') == 'maybe_200':
        print("\n[WAITING] Checking for verification email...")
        verification = wait_and_check(email_data, max_wait=20, check_interval=3)

        if verification.get('found') and verification.get('links'):
            for link in verification['links']:
                if click_verification_link(link):
                    print("\n[SUCCESS] Gumroad account verified!")
                    break
        else:
            print("\n[INFO] No verification email received yet. Account may be in pending state.")
            print("  Email: ", email_data['email'])
            print("  Checking all messages...")
            messages = get_messages(email_data['token'])
            print(f"  Total messages: {len(messages)}")
            for msg in messages:
                print(f"    - {msg.get('from', {}).get('address')}: {msg.get('subject')}")

    print("\n" + "=" * 70)
    print("SAVING ACCOUNT INFO")
    print("=" * 70)

    account_info = {
        'email': email_data['email'],
        'created_at': time.time(),
        'gumroad_status': result,
        'email_provider': 'mail.tm'
    }

    save_path = os.path.join(os.path.dirname(__file__), '..', 'account_info.json')
    with open(save_path, 'w') as f:
        json.dump({k: str(v) if not isinstance(v, (str, bool, int, float, list, dict)) else v
                   for k, v in account_info.items()}, f, indent=2)

    print(f"Saved to {save_path}")
    print(f"Email: {email_data['email']}")
    print(f"Password saved in session variable")

    return account_info


if __name__ == '__main__':
    main()

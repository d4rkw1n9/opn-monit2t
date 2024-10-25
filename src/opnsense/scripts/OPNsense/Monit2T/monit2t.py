#!/usr/bin/env python3

import sys
import os
import syslog
import requests
import json
import re
import ipaddress  # for IP address validation
from configparser import ConfigParser


def t_send(token, chat_id, message):
    t_url = f'https://api.telegram.org/bot{token}/sendMessage'
    syslog.openlog('monit')
    try:
        resp = requests.post(t_url, json={'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'})
    except requests.exceptions.Timeout:
        syslog.syslog(syslog.LOG_ERR, 'Telegram API endpoint request timeout')
        sys.exit('Telegram API endpoint request timeout')
    except requests.exceptions.TooManyRedirects:
        syslog.syslog(syslog.LOG_ERR, 'Telegram API endpoint returned error: ' + resp.text)
        sys.exit(resp.text)
    except requests.exceptions.RequestException as e:
        syslog.syslog(syslog.LOG_ERR, 'Telegram API endpoint returned error: ' + resp.text)
        sys.exit(resp.text)
    if resp.status_code == 200:
        syslog.syslog(syslog.LOG_NOTICE, 'Telegram message sent.')
        return resp.text
    else:
        syslog.syslog(syslog.LOG_ERR, 'Telegram API endpoint returned error: ' + resp.text)
        sys.exit(resp.text)


def ip_lookup(ip, token_ip):
    # Query ipinfo.io API to get details about the IP address
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json?token={token_ip}")
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Failed to lookup IP"}
    except requests.RequestException:
        return {"error": "Failed to reach ipinfo.io"}


def is_public_ip(ip):
    # Check if an IP address is public
    try:
        ip_obj = ipaddress.ip_address(ip)
        return not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_multicast or ip_obj.is_link_local)
    except ValueError:
        return False


def extract_ips_from_json(message_json):
    """Extract src_ip and dest_ip from the JSON object if present."""
    try:
        json_obj = json.loads(message_json)
        src_ip = json_obj.get("src_ip", None)
        dest_ip = json_obj.get("dest_ip", None)
        return src_ip, dest_ip
    except json.JSONDecodeError:
        return None, None


def extract_ips_from_text(message):
    """Extract any IP addresses from a regular text message."""
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    return re.findall(ip_pattern, message)


def parse_and_lookup(message, token_ip, token, chat_id):
    # Set to keep track of unique public IPs
    unique_ips = set()

    # Check if the message is JSON format and extract src_ip, dest_ip if applicable
    src_ip, dest_ip = extract_ips_from_json(message)
    
    # If no JSON format IPs were found, extract from plain text
    if not src_ip and not dest_ip:
        ips = extract_ips_from_text(message)
    else:
        ips = [src_ip, dest_ip]

    # Filter out non-public IP addresses and avoid duplicates
    for ip in ips:
        if ip and is_public_ip(ip):
            unique_ips.add(ip)

    if unique_ips:
        ip_details = []
        for ip in unique_ips:
            details = ip_lookup(ip, token_ip)
            ip_details.append(f"IP: {ip}, Details: {details}")
        
        # Prepare the second message with IP details
        lookup_message = "Public IP Information:\n" + "\n".join(ip_details)
        t_send(token, chat_id, lookup_message)


t_conf = '/usr/local/opnsense/scripts/OPNsense/Monit2T/monit2t.conf'
if os.path.exists(t_conf):
    cnf = ConfigParser()
    cnf.read(t_conf)
    token = str(cnf['api_settings']['token'])
    chat_id = str(cnf['api_settings']['chat_id'])
    token_ip = cnf['api_settings'].get('token_ip', None)
    message = str(cnf['alert_settings']['message'])

    if len(sys.argv) == 1:
        # Detect environment variables (for templated messages)
        msg_vars = re.findall(r"{([^{]*?)}", message)
        env_vars = {}
        for msg_var in msg_vars:
            env_vars[msg_var] = os.getenv(msg_var, "null").replace('<', '&lt').replace('>', '&gt')

        formatted_message = message.format(**env_vars)
        
        # Send the original message as it is
        t_send(token, chat_id, formatted_message)
        
        # Send the second message with IP information (if public IPs are found)
        parse_and_lookup(formatted_message, token_ip, token, chat_id)
    else:
        # Handle test message
        message = 'This is a test telegram message\nAlerts will be sent in the following format: \n\n' + message
        t_send(token, chat_id, message)

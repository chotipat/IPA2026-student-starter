"""Part 4 student implementation."""

import json

import logging

import os

from concurrent.futures import ThreadPoolExecutor

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pathlib import Path

from tempfile import TemporaryDirectory

from app.integration import process_request

from app.webex_client import WEBEX_API_BASE, WebexClient

class WebexEventHandler:
    def __init__(self, client, bot_person_id, processor=None):
        # TODO: implement according to Part 4 specification
        raise NotImplementedError

    def handle_event(self, event):
        # TODO: implement according to Part 4 specification
        raise NotImplementedError

def make_http_handler(submit_event):
    # TODO: implement according to Part 4 specification
    raise NotImplementedError

def main():
    # TODO: implement according to Part 4 specification
    raise NotImplementedError

if __name__ == "__main__":
    main()

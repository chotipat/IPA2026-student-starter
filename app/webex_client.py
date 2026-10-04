"""Part 4 student implementation."""

import os

import requests

WEBEX_API_BASE = 'https://webexapis.com/v1'

class WebexClient:
    def __init__(self, token=None, session=None):
        # TODO: implement according to Part 4 specification
        raise NotImplementedError

    @property
    def headers(self):
        # TODO: implement according to Part 4 specification
        raise NotImplementedError

    def get_message(self, message_id):
        # TODO: implement according to Part 4 specification
        raise NotImplementedError

    def download_file(self, file_url):
        # TODO: implement according to Part 4 specification
        raise NotImplementedError

    def send_message(self, room_id, text):
        # TODO: implement according to Part 4 specification
        raise NotImplementedError

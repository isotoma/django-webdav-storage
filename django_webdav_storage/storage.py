# coding: utf-8

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from django.core.files.storage import Storage as StorageBase
from django.core.files.base import ContentFile
from django.conf import settings
import requests


def setting(name, default=None):
    return getattr(settings, name, default)


class WebDavStorage(StorageBase):
    def __init__(self, **kwargs):
        self.requests = self.get_requests_instance(**kwargs)
        self.webdav_url = self.set_webdav_url(**kwargs)
        self.public_url = self.set_public_url(**kwargs)

        if not self.webdav_url:
            raise NotImplementedError('Please define webdav url')
        if not self.public_url:
            self.public_url = self.webdav_url

    def set_webdav_url(self, **kwargs):
        return kwargs.get('webdav_url') or setting('WEBDAV_URL')

    def set_public_url(self, **kwargs):
        return kwargs.get('public_url') or setting('WEBDAV_PUBLIC_URL')

    def get_requests_instance(self, **kwargs):
        return requests.Session()

    def webdav(self, method, name, *args, **kwargs):
        url = self.get_webdav_url(name)
        method = method.lower()
        response = getattr(self.requests, method)(url, *args, **kwargs)
        response.raise_for_status()
        return response

    def get_public_url(self, name):
        return self.public_url.rstrip('/') + '/' + name.lstrip('/')

    def get_webdav_url(self, name):
        return self.webdav_url.rstrip('/') + '/' + name.lstrip('/')

    def _open(self, name, mode='rb'):
        return ContentFile(self.webdav('GET', name).content)

    def _save(self, name, content):
        self.webdav('PUT', name, data=content)
        return name

    def delete(self, name):
        try:
            self.webdav('DELETE', name)
        except requests.HTTPError:
            pass

    def exists(self, name):
        try:
            self.webdav('HEAD', name)
        except requests.exceptions.HTTPError:
            return False
        else:
            return True

    def size(self, name):
        try:
            return int(self.webdav('HEAD', name).headers['content-length'])
        except (ValueError, requests.exceptions.HTTPError):
            raise IOError('Unable get size for %s' % name)

    def url(self, name):
        return self.get_public_url(name)

    def get_base_url(self):
        return self.url('').rstrip('/')


class WebDavStaticStorage(WebDavStorage):
    container_name = setting('WEBDAV_STATIC_CONTAINER_NAME')
    base_url = setting('WEBDAV_STATIC_BASE_URL')

import ssl
import sys
import base64
from urllib import urlencode
import json
import httplib


class TinyClient(object):
    # For single thread use only, no sync inside.
    DEFAULT_VERSION = 'v1'

    def __init__(self, ip, username=str, password=str, port=int):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.content_type = "application/json"
        self.accept_type = "application/json"
        self.response = None
        self.url_prefix = "/api/" + self.DEFAULT_VERSION
        self.auth = base64.urlsafe_b64encode(self.username + ':' +
                                             self.password).decode('ascii')
        self.headers = {'Authorization': 'Basic %s' % self.auth,
                        'content-type': self.content_type}
        self.url = None
        self.create_url = None
        self.read_url = None
        self.update_url = None
        self.delete_url = None
        self._connect()

    def _connect(self):
        if sys.version_info >= (2, 7, 9):
            ctx = ssl._create_unverified_context()
            self.connection = httplib.HTTPSConnection(self.ip, self.port,
                                                      context=ctx, timeout=30000)
        else:
            self.connection = httplib.HTTPSConnection(self.ip, self.port,
                                                      timeout=30000)

    def _close(self):
        self.connection.close()

    def _request(self, method, endpoint, payload="", url_parameters=None):
        url_params_string = ""
        if url_parameters:
            if "?" in endpoint:
                url_params_string = "&%s" % urlencode(url_parameters)
            else:
                url_params_string = "?%s" % urlencode(url_parameters)
        request = "%s%s%s" % (self.url_prefix, endpoint, url_params_string)
        print("DEBUG _request: %s %s" % (method, request))
        if payload:
            print("DEBUG _payload: %s" % payload)
        self.connection.request(method, request, payload, self.headers)
        self.response = self.connection.getresponse()
        return self.response

    def request(self, method, endpoint, payload="", params={}):
        if type(payload) is not str:
            payload = json.dumps(payload)
        response = self._request(method, endpoint, payload, url_parameters=params)
        print("DEBUG: http status code %s" % response.status)
        # object not found
        if method == 'GET' and response.status == 404:
            return None
        result_string = response.read()
        # DELETE response body is empty
        py_dict = json.loads(result_string) if result_string else {}
        if response.status < 200 or response.status >= 300 or "error_code" in py_dict:
            raise Exception(py_dict)
        else:
            return py_dict

    def create(self, py_dict, params={}):
        if not self.create_url:
            self.create_url = self.url
        return self.request('POST', self.create_url, payload=py_dict, params=params)

    def read(self, object_id=None, params={}):
        if not self.read_url:
            self.read_url = self.url
        if object_id:
            return self.request('GET', "%s/%s" % (self.read_url, object_id), params=params)
        else:
            return self.request('GET', self.read_url, params=params)

    def update(self, object_id, py_dict, params={}):
        if not self.update_url:
            self.update_url = self.url
        return self.request('PUT', "%s/%s" % (self.update_url, object_id), py_dict, params=params)

    def delete(self, object_id, params={}):
        if not self.delete_url:
            self.delete_url = self.url
        return self.request("DELETE", "%s/%s" % (self.delete_url, object_id), params=params)

    def set_url(self, url, create_url=None, read_url=None, update_url=None, delete_url=None):
        self.url = url
        self.create_url = None
        self.read_url = None
        self.update_url = None
        self.delete_url = None

    def get_all(self, params={}):
        res = self.read(params=params)
        if res:
            return res['results']
        else:
            return []

    def get_one_id(self, name, params={}):
        res = None
        all_obj = self.get_all(params=params)
        for r in all_obj:
            if r['display_name'] == name:
                res = r['id']
                break
        return res

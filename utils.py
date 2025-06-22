# hikvision_analyzer/utils.py

import base64
import io
from PIL import Image
import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import xml.etree.ElementTree as ET
import urllib3

# Desativa warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_device_info(ip, username, password, port=80, timeout=5):
    try:
        url = f"http://{ip}:{port}/ISAPI/System/deviceInfo"
        auth = HTTPDigestAuth(username, password)
        response = requests.get(url, auth=auth, timeout=timeout, verify=False)

        if response.status_code != 200:
            auth = HTTPBasicAuth(username, password)
            response = requests.get(url, auth=auth, timeout=timeout, verify=False)

        if response.status_code == 200:
            try:
                xml_str = response.content.decode('utf-8').replace(
                    'xmlns="http://www.hikvision.com/ver20/XMLSchema"', ''
                )
                root = ET.fromstring(xml_str)
                return root.findtext("deviceName", default="N/A")
            except Exception:
                return "N/A"
        else:
            return "N/A"
    except Exception:
        return "N/A"


def capture_snapshot(ip, username, password, port=80, timeout=3):
    try:
        url = f"http://{ip}:{port}/ISAPI/Streaming/channels/101/picture"
        response = requests.get(url, auth=HTTPDigestAuth(username, password), timeout=timeout, verify=False, stream=True)
        if response.status_code != 200:
            response = requests.get(url, auth=HTTPBasicAuth(username, password), timeout=timeout, verify=False, stream=True)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        return None
    except Exception:
        return None
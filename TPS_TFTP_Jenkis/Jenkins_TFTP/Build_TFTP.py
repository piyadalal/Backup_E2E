import requests
from requests.auth import HTTPBasicAuth
import time
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
JENKINS_URL = "http://172.20.117.198:8080"
JOB_PATH = "job/STB_Update_TFTP"
USERNAME = os.getenv("JENKINS_USER")
API_TOKEN = os.getenv("JENKINS_TOKEN")

if not USERNAME or not API_TOKEN:
    raise ValueError("Missing JENKINS_USER or JENKINS_TOKEN in .env file")

auth = HTTPBasicAuth(USERNAME, API_TOKEN)

# List of MAC addresses for Q_MAC
Q_MAC_LIST = [
    "2C:08:8C:95:15:FD",
    "2C:08:8C:95:15:A6",
    "2C:08:8C:95:17:74",
    "2C:08:8C:95:18:D9",
    "2C:08:8C:95:17:62",
    "2C:08:8C:95:17:26",
    "2C:08:8C:95:16:2A",
    "CC:4E:EC:FE:13:30",
    "2C:08:8C:95:17:5C",
    "2C:08:8C:95:16:C3",
    "2C:08:8C:95:16:54",
    "2C:08:8C:95:16:D2"
]

# Shared build version
Q_BUILD = "Q330.000.11.00C"


def trigger_build(q_mac, q_build):
    build_url = "{}/{}/buildWithParameters".format(JENKINS_URL, JOB_PATH)

    params = {"Q_MAC": q_mac, "Q_Build": q_build}

    resp = requests.post(build_url, auth=auth, params=params)

    if resp.status_code != 201:
        print("Failed to trigger build for Q_MAC={}: {} {}".format(
            q_mac, resp.status_code, resp.text))
        return None

    print("Build triggered for Q_MAC={}".format(q_mac))
    queue_url = "{}api/json".format(resp.headers["Location"])
    while True:
        q = requests.get(queue_url, auth=auth).json()
        if "executable" in q:
            build_number = q["executable"]["number"]
            print("Build #{} started for Q_MAC={}".format(build_number, q_mac))
            break
        time.sleep(2)

    build_status_url = "{}/{}/{}/api/json".format(JENKINS_URL, JOB_PATH, build_number)
    while True:
        b = requests.get(build_status_url, auth=auth).json()
        if b["building"]:
            print("Build #{} (Q_MAC={}) still running...".format(build_number, q_mac))
        else:
            print("Build #{} finished with result: {}".format(build_number, b["result"]))
            return b["result"]
        time.sleep(5)


for mac in Q_MAC_LIST:
    result = trigger_build(mac, Q_BUILD)
    if result != "SUCCESS":
        print("Build with Q_MAC={} failed or unstable. Stopping further runs.".format(mac))
        break

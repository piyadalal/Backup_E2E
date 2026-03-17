# encoding: utf-8

import os
import sys
import json
import time
import datetime
"""
import traceback
from conversionutil import epoch_to_time
from pa_events import process_event, BaseAction
from timingsutil import Timeout
from tableutil import Table, HEADING
from pa_logging_mixin import ProductAnalyticsLoggingMixin

# Imports the Google Cloud client library
from google.cloud import logging_v2
# from google.protobuf.json_format import MessageToDict
from google.api_core.exceptions import ResourceExhausted as GCPResourceExhausted
from google.api_core.exceptions import Unknown as GCPUnknown


"""

# gcloud config set project skyuk-uk-pa-tds-int

USERNAME = "PRDA5207"
CREDENTIALS_FILE = "C:\\Users\\PRDA5207\\AppData\\Roaming\\gcloud\\application_default_credentials.json"
ANALYTICS_TEST_PROJECT_ID = "skyuk-uk-pa-tds-int"
#C:\Users\PRDA5207\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin
RESOURCE_EXHAUSTED_WAIT_TIME = 60
GCP_UNKNOWN_EXCEPTION_WAIT_TIME = 10

UPDATE_PERIOD = 10
LOG_FILTER = False
LOG_PAYLOAD = True

TZ_ADJUST = (datetime.datetime.now()-datetime.datetime.utcnow()).seconds

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_FILE


"""
request body for list:entries API

{
  "projectIds": [
    "skyuk-uk-pa-tds-int"
  ],
  "resourceNames": [
    "projects/skyuk-uk-pa-tds-int"
  ],
  "filter": "timestamp>=\"2020-01-08T10:49:00Z\" AND timestamp<=\"2020-01-08T10:49:59Z\" AND jsonPayload.payload.source.serialNumber=\"32B20304809648850\" AND resource.type=cloud_function ",
  "orderBy": "timestamp desc"
}



class ProductAnalyticsGoogleCloudLoggingReader(ProductAnalyticsLoggingMixin):

    OVERLAP = 20

    RESOURCE_NAME = "projects/{project_id}"

    FILTER = ("timestamp>\"{start_time}\""
              " AND timestamp<=\"{end_time}\""
              " AND jsonPayload.payload.source.serialNumber=\"{serial_number}\""
              " AND resource.type=cloud_function"
              " AND severity>=INFO")

    @property
    def log_files(self):
        return [u"logs/{name}_{serial}_gcp.log".format(name=self.stb_name,
                                                       serial=self.stb_serial_number)]

    def __init__(self,
                 project_id,
                 stb_name,
                 stb_serial_number,
                 update_period=10,
                 log_filter=False,
                 log_payload=True):

        self.start_time = time.time()
        self.project_id = project_id
        self.resource_name = self.RESOURCE_NAME.format(project_id=project_id)
        self.stb_name = stb_name
        self.stb_serial_number = stb_serial_number
        self.timeout = Timeout(update_period,
                               start_in_an_expired_state=True)
        self.log_filter = log_filter
        self.log_payload = log_payload
        self.gcp_logging_client = logging_v2.Client(project=self.project_id)
        self.last_event = None
        self.processed_events = []

        super(ProductAnalyticsGoogleCloudLoggingReader, self).__init__()

    def fetch_events(self,
                     start_time,
                     end_time):
        events = []

        entries_list_params = {'resource_names': [self.resource_name],
                               'filter_':        self.FILTER.format(start_time=start_time,
                                                                    end_time=end_time,
                                                                    serial_number=self.stb_serial_number),
                               'order_by': "timestamp asc"}

        if self.log_filter:
            self.log('Filter: "{filter}"'.format(filter=entries_list_params['filter_'].replace('"', '\\"')))

        entries = list(self.gcp_logging_client.list_entries(**entries_list_params))
        for entry in entries:
            try:
                pa_payload = entry.payload['payload']
            except KeyError:
                self.log('Entry.payload does not have payload key')
                continue
            except AttributeError:
                self.log('Entry does not have payload attribute')
                continue
            # ap_payload = entry_dict.get('jsonPayload', {}).get('payload', {})

            if len(pa_payload.get('eventLog', [{}])) > 1:
                self.log('*********************************\n'
                         'Warning. Multiple events detected\n'
                         '*********************************')
            try:
                event = process_event(payload=pa_payload,
                                      device_name=self.stb_name)
                events.append(event)
            except Exception as e:
                ex_type, ex, tb = sys.exc_info()

                self.log(text=["Exception",
                               '-' * 80,
                               json.dumps(pa_payload),
                               '-' * 80,
                               str(e),
                               ''.join(traceback.format_tb(tb)),
                               '-' * 80],
                         format_all_lines=False)
        return events

    def check_for_new_events(self):
        self.timeout.wait_and_restart()

        now = time.time()
        start_time = epoch_to_time(ep=self.start_time - TZ_ADJUST,
                                   time_format=u'%Y-%m-%dT%H:%M:%SZ')

        end_time = epoch_to_time(ep=now - TZ_ADJUST,
                                 time_format=u'%Y-%m-%dT%H:%M:%SZ')

        try:
            events = self.fetch_events(start_time=start_time,
                                       end_time=end_time)
        except GCPUnknown as e:
            self.log("Exception: {es}".format(es=str(e)))
            self.log('Waiting for {s}s before retrying'.format(s=GCP_UNKNOWN_EXCEPTION_WAIT_TIME))
            Timeout(GCP_UNKNOWN_EXCEPTION_WAIT_TIME).wait()
            return
        except GCPResourceExhausted as e:
            self.log("Exception: {es}".format(es=str(e)))
            self.log('Waiting for {s}s before retrying'.format(s=RESOURCE_EXHAUSTED_WAIT_TIME))
            Timeout(RESOURCE_EXHAUSTED_WAIT_TIME).wait()
            return

        self.start_time = now - self.OVERLAP  # adds a bit of tolerance for latency

        if events:
            self.log('...')

        for event in events:
            if event.message_number not in self.processed_events:
                self.processed_events.append(event.message_number)
                if self.log_payload or type(event) is BaseAction:
                    self.log(text=json.dumps(event.payload,
                                             indent=4,
                                             ensure_ascii=False),  # .encode('utf8'),
                             format_all_lines=False)
                self.log(event.summary)
            else:
                pass
                # self.log('Duplicate: {mn}'.format(mn=event.message_number))

    def run(self):
        self.log('starting')

        while True:
            try:
                self.check_for_new_events()
            except Exception as e:
                ex_type, ex, tb = sys.exc_info()
                self.log(text=["Exception",
                               '-' * 80,
                               str(e),
                               ''.join(traceback.format_tb(tb)),
                               '-' * 80,
                               'Waiting for {s}s before retrying'.format(s=RESOURCE_EXHAUSTED_WAIT_TIME),
                               '-' * 80],
                         format_all_lines=False)


def select_device():
    with open('config.json') as json_file:
        devices = [device
                   for device in json.load(json_file)
                   if 'AWS' not in device]

    if len(devices) == 1:
        return devices[0]
    elif len(devices) == 0:
        raise ValueError('No GCP devices configured')

    device_table = Table(headings=[{HEADING: heading}
                                   for heading in devices[0].keys()],
                         rows=devices)

    while True:
        print(device_table.text())
        ans = input("\nChoose a device by number "
                    "(q to quit) > ")

        if ans.strip().lower().startswith('q'):
            exit()

        if ans.strip() == "":
            break

        try:
            ans = int(ans) - 1
        except ValueError:
            print("Needs to be a number!")
        else:
            if ans not in range(len(devices)):
                print("No such device")
                continue
            break

    return devices[ans]


def main():
    device = select_device()
    try:
        ProductAnalyticsGoogleCloudLoggingReader(project_id=ANALYTICS_TEST_PROJECT_ID,
                                                 # credentials_file=CREDENTIALS_FILE,
                                                 stb_name=device['Description'],
                                                 stb_serial_number=device['Serial Number'],
                                                 update_period=UPDATE_PERIOD,
                                                 log_filter=LOG_FILTER,
                                                 log_payload=LOG_PAYLOAD).run()
    except KeyboardInterrupt:
        print('keyboard interrupt')

"""
if __name__ == "__main__":
    pass

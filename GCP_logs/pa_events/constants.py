# encoding: utf-8

"""
Constants used to define JSONPath queries to extract
fields from PA messages.

If you need a new JSONPath that isn't in this file,
it's a good idea to add it here for future use.

If the current values aren't enough, you can read up
on JSONPath here: https://github.com/h2non/jsonpath-ng/blob/master/README.rst
"""

# EventLog
# Fields common to all PA messages in the EventLog

ACTION_ID = '$.eventLog.[*].action.id'
TIME_MS = '$.eventLog.[*].timems'
DETAILS_VERSION = '$.eventLog.[*].details.version'

# Source
# Fields common to all PA messages in the EventLog
MESSAGE_NUMBER = '$.source.msgNumber'
SOURCE_REGION = '$.source.region'
SERIAL_NUMBER ='$.source.serialNumber'
SOFTWARE_VERSION = '$.source.softwareVersion'
UI_VERSION = '$.source.UIVersion'
CLIENT_DEVICE ='$.source.clientDetails.device'
CLIENT_PLATFORM = '$.source.clientDetails.platform'
CLIENT_PROPOSITION = '$.source.clientDetails.proposition'
CLIENT_PROVIDER = '$.source.clientDetails.provider'

# Fields expected in specific PA messages

# 1400, and others?
TRIGGER_ID = '$.eventLog.[*].trigger.id'
TRIGGER_INPUT = '$.eventLog.[*].trigger.input'
ORIG = '$.eventLog.[*].action.orig'
ORIG_PATH = '$.eventLog.[*].action.orig.path'
DEST = '$.eventLog.[*].action.dest'
DEST_PATH = '$.eventLog.[*].action.dest.path'
LCN = '$.eventLog.[*].action.lcn'
REF_ID = '$.eventLog.[*].action.ref.id'
TYPE= '$.eventLog.[*].action.asset.type'

"""
{
    "eventLog": [
        {
            "action": {
                "id": "01400",
                "dest": {
                    "focusDepth": "1",:except
                    "interimDetailPageFlag": "false",
                    "path": "guide://qms/sections/SHOWPAGE-SERIES",
                    "screenname": "SP-Funny Woman",
                    "tilePositionX": "10",
                    "tilePositionY": "1"
                },
                "orig": {
                    "focusDepth": "0",
                    "interimDetailPageFlag": "false",
                    "menuPath": "homemenu",
                    "path": "guide://qms/sections/HOME_TILES",
                    "screenname": "Home"
                }
            },
            "details": {
                "version": "1.0"
            },
            "timems": "1676491418100",
            "trigger": {
                "id": "userInput",
                "input": "KeyEvent:Key_SelectKeyReleased",
                "remote": {
                    "batterylevel": 80,
                    "conntype": "",
                    "deviceid": 71,
                    "hwrev": "103.1.0.0",
                    "make": "Remote Solution",
                    "model": "LC103",
                    "name": "P215 SkyQ LC103",
                    "swrev": "5103.2.4"
                }
            }
        }
    ],
    "source": {
        "clientDetails": {
            "device": "TV",
            "hardware": "LT043-f1-ant",
            "platform": "Llama",
            "proposition": "SKYQ",
            "provider": "SKY"
        },
        "customerID": "",
        "locationInHome": "Living Room",
        "msgNumber": 8,
        "region": "UK",
        "serialNumber": "LT01SK02052001704",
        "softwareVersion": "QS015.003.00U",
        "territory": "GBR",
        "trial": "D12",
        "trialSegments": "D12",
        "UIVersion": "20.255.015.02"
    }
}
"""

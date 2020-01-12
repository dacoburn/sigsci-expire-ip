# encoding = utf-8
import time
from datetime import datetime, timedelta
import json
import requests
import os
import argparse
from timeit import default_timer as timer
from sigsci_api.events import sigsci_events

start = timer()
parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(description="Example script to expire " +
                                 "events from Signal Sciences")
parser.add_argument("--config", type=str, required=True,
                    help="Specify the file with the configuration options")

opts = parser.parse_args()

# Initial setup

if "config" in opts and not(opts.config is None):
    confFile = open(opts.config, "r")
    confJson = json.load(confFile)
else:
    confJson = ""

# Logfile for the script
logFile = "sigsci-expire.log"

try:
    os.remove(logFile)
except OSError as e:
    # print("Failed to remove %s with: %s" % (logFile,e.strerror))
    pass


# Simple logout function for saving log file
def logOut(msg):
    log = open(logFile, 'a')
    data = "%s: %s" % (datetime.now(), msg)
    log.write(data)
    log.write("\n")
    log.close
    print(msg)


sigsci_email = os.environ.get('SIGSCI_EMAIL')
sigsci_corp_name = os.environ.get('SIGSCI_CORP')
sigsci_password = os.environ.get('SIGSCI_PASSWORD')
sigsci_apitoken = os.environ.get('SIGSCI_TOKEN')
sigsci_dash_sites = os.environ.get('SIGSCI_SITES')

# This is requried and is used for all API requests.
if "email" in confJson and confJson["email"] is not None:
    sigsci_email = confJson["email"]

if "corp_name" in confJson and confJson["corp_name"] is not None:
    sigsci_corp_name = confJson["corp_name"]

if "password" in confJson and confJson["password"] is not None:
    sigsci_password = confJson["password"]

if "apitoken" in confJson and confJson["apitoken"] is not None:
    sigsci_apitoken = confJson["apitoken"]

if "dash_sites" in confJson and confJson["dash_sites"] is not None:
    sigsci_dash_sites = confJson["dash_sites"]

if "from" not in confJson:
    sigsci_fromTime = "-30d"
else:
    sigsci_fromTime = confJson["from"]

if "until" not in confJson:
    sigsci_untilTime = None
else:
    sigsci_untilTime = confJson["until"]


logOut("email: %s" % sigsci_email)
logOut("corp: %s" % sigsci_corp_name)
if sigsci_apitoken is not None:
    logOut("Using API TOKEN")
else:
    logOut("Using Password Auth")

pythonRequestsVersion = requests.__version__
userAgentVersion = "1.0.2"
userAgentString = "SigSci-Expire-Events/%s (PythonRequests %s)" \
    % (userAgentVersion, pythonRequestsVersion)


# Handy function for pretty printing JSON
def prettyJson(data):
    return(json.dumps(data, indent=4, separators=(',', ': ')))

# Loop across all the data and output it in one big JSON object

if sigsci_apitoken is not None and sigsci_apitoken != "":
    authMode = "apitoken"
    logOut("AuthMode: API Token")
    sigsci_headers = {
            'Content-type': 'application/json',
            'x-api-user': sigsci_email,
            'x-api-token': sigsci_apitoken,
            'User-Agent': userAgentString
    }
else:
    authMode = "password"
    logOut("AuthMode: Password")
    sigsciToken = sigsciAuth()
    sigsci_headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer %s' % token,
            'User-Agent': userAgentString
    }

sigsci = sigsci_events(sigsci_email, sigsci_corp_name, sigsci_headers)

for activeInput in sigsci_dash_sites:
    site = activeInput
    logOut("site: %s" % site)
    if authMode == "apitoken":
        totalCounter = 0
        siteEvents = sigsci.pullEvents(key=activeInput, curSite=site,
                                         curFrom=sigsci_fromTime, curUntil=sigsci_untilTime)
        sigsci.expireEvents(siteEvents, site)
        totalEvents = len(siteEvents)
        while totalEvents >= 1000:
            logOut("Total Events 1,000 likely hit API limit, trying again: %s" % \
                    totalCounter)
            siteEvents = sigsci.pullEvents(key=activeInput, curSite=site,
                                         curFrom=sigsci_fromTime, curUntil=sigsci_untilTime)
            sigsci.expireEvents(siteEvents, site)
            totalEvents = len(siteEvents)
            newTotal = totalCounter + totalEvents
            logOut("Current total of expired events: %s" % newTotal)
        else:
            logOut("Finished pulling all requests, final total: %s" % \
                    totalCounter)
    else:
        siteEvents = sigsci.pullEvents(key=activeInput, curSite=site,
                                         curFrom=sigsci_fromTime, curUntil=sigsci_untilTime)
        sigsci.expireEvents(siteEvents, site)
    logOut("Finished Expiring Events for %s" % site)

end = timer()
totalTime = end - start
timeResult = round(totalTime, 2)
logOut("Total Script Time: %s seconds" % timeResult)
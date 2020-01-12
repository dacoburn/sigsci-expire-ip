import time
from datetime import datetime, timedelta
import json
import requests
import os
from timeit import default_timer as timer
import re

api_host = 'https://dashboard.signalsciences.net'

class sigsci_events:

    def __init__(self, email, corp_name, headers, logFile=None):
        self.email = email
        self.corp_name = corp_name
        self.headers = headers
        self.logFile = logFile
        self.last_error = None

    def logOut(self, msg):
        logFile = self.logFile
        data = "%s: %s" % (datetime.now(), msg)
        if logFile is None:
            print(msg)
        else:
            log = open(logFile, 'a')
            log.write(data)
            log.write("\n")
            log.close
            print(msg)

    def determine_time(self, from_time, until_time=None):
        regex = re.compile("-(\d+)(\w)")
        result = regex.match(from_time)
        timeIntervals = []
        if result is not None:
            interval = result.group(0)
            unit = lower(result.group(1))
            if unit == "d":
                interval = interval * 1440
            elif unit == "s" :
                interval = interval
            elif unit == "min":
                interval = interval * 60
        else:
            msg = {"error": "Unknown from type"}
            self.last_error = msg
            return(msg)


    # Definition for error handling on the response code
    def checkResponse(self, code, responseText, curSite=None,
                      from_time=None, until_time=None):
        site_name = curSite
        if code == 400:
            if "Rate limit exceeded" in responseText:
                return("rate-limit")
            else:
                self.logOut("Bad API Request (ResponseCode: %s)" % (code))
                self.logOut("ResponseError: %s" % responseText)
                self.logOut('from: %s' % from_time)
                self.logOut('until: %s' % until_time)
                self.logOut('email: %s' % email)
                self.logOut('Corp: %s' % corp_name)
                self.logOut('SiteName: %s' % site_name)
                return("bad-request")
        elif code == 500:
            self.logOut(
                "Caused an Internal Server error (ResponseCode: %s)" % (code))
            self.logOut("ResponseError: %s" % responseText)
            self.logOut('from: %s' % from_time)
            self.logOut('until: %s' % until_time)
            self.logOut('email: %s' % email)
            self.logOut('Corp: %s' % corp_name)
            self.logOut('SiteName: %s' % site_name)
            return("internal-error")
        elif code == 401:
            logOut(
                "Unauthorized, likely bad credentials or site configuration," +
                " or lack of permissions (ResponseCode: %s)" % (code))
            self.logOut("ResponseError: %s" % responseText)
            self.logOut('email: %s' % email)
            self.logOut('Corp: %s' % corp_name)
            self.logOut('SiteName: %s' % site_name)
            return("unauthorized")
        elif code >= 400 and code <= 599 and code != 400 \
                and code != 500 and code != 401:
            self.logOut("ResponseError: %s" % responseText)
            self.logOut('from: %s' % from_time)
            self.logOut('until: %s' % until_time)
            self.logOut('email: %s' % email)
            self.logOut('Corp: %s' % corp_name)
            self.logOut('SiteName: %s' % site_name)
            return("other-error")
        else:
            return("success")


    # If Password auth, perform Auth
    def sigsciAuth(self, userAgentString, email, password):
        self.logOut("Authenticating to SigSci API")
        # Authenticate
        authUrl = api_host + '/api/v0/auth'
        authHeader = {
            "User-Agent": userAgentString
        }
        auth = requests.post(
            authUrl,
            data={"email": email, "password": password},
            headers=authHeader
        )

        authCode = auth.status_code
        authError = auth.text

        authResult = self.checkResponse(authCode, authError)
        if authResult is None or authResult != "success":
            self.logOut("API Auth Failed")
            logOut(authResult)
            exit()
        elif authResult is not None and authResult == "rate-limit":
            self.logOut("SigSci Rate Limit hit")
            self.logOut("Retrying in 10 seconds")
            time.sleep(10)
            sigsciAuth()
        else:
            parsed_response = auth.json()
            token = parsed_response['token']
            self.logOut("Authenticated")
            return(token)


    # Actually call the Requests function
    def getRequestData(self, url, method="GET"):
        response_raw = requests.request(method, url, headers=self.headers)
        responseCode = response_raw.status_code
        responseError = response_raw.text
        return(response_raw, responseCode, responseError)


    # Pull Event data from the API
    def pullEvents(self, curSite, key=None,
                     curFrom=None, curUntil=None):
        site_name = curSite
        from_time = curFrom
        until_time = curUntil

        self.logOut("SiteName: %s" % site_name)
        self.logOut("From: %s" % (from_time))
        self.logOut("Until: %s" % (until_time))

        url = api_host + \
            ('/api/v0/corps/%s/sites/%s/events?status=active&from=%s&until=%s'
                % (self.corp_name, site_name, from_time, until_time))
        loop = True

        counter = 1
        self.logOut("Pulling events from events API")
        allRequests = []
        # If there is a next page need to make sure we get through
        # all of the event pages
        while loop:
            self.logOut("Processing page %s" % counter)
            startPage = timer()
            responseResult, responseCode, ResponseError = \
                self.getRequestData(url)

            sigSciRequestCheck = \
                self.checkResponse(responseCode, ResponseError, curSite=site_name,
                              from_time=from_time, until_time=until_time)

            if sigSciRequestCheck is None or sigSciRequestCheck != "success":
                self.logOut("Failed to pull events")
                logOut(sigSciRequestCheck)
                exit()
            elif sigSciRequestCheck is not None and \
                    sigSciRequestCheck == "rate-limit":
                self.logOut("SigSci Rate Limit hit")
                self.logOut("Retrying in 10 seconds")
                time.sleep(10)
                break
            else:
                response = json.loads(responseResult.text)

            curPageNumRequests = len(response['data'])
            self.logOut("Number of Events for Page: %s" % curPageNumRequests)

            # Look for the next page URL in the data
            for request in response['data']:
                # data = json.dumps(request)
                allRequests.append(request)

            if "next" in response and "uri" in response['next']:
                next_url = response['next']['uri']
                if next_url == '':
                    self.logOut("Finished Page %s" % counter)
                    counter += 1
                    endPage = timer()
                    pageTime = endPage - startPage
                    pageTimeResult = round(pageTime, 2)
                    self.logOut("Total Page Time: %s seconds" % pageTimeResult)
                    loop = False
                else:
                    url = api_host + next_url
                    self.logOut("Finished Page %s" % counter)
                    counter += 1
                    endPage = timer()
                    pageTime = endPage - startPage
                    pageTimeResult = round(pageTime, 2)
                    self.logOut("Total Page Time: %s seconds" % pageTimeResult)
            else:
                loop = False

        # Size of all the Events found
        totalRequests = len(allRequests)
        self.logOut("Total Events Pulled: %s" % totalRequests)
        return(allRequests)
    

    def expireEvents(self, events, site_name):

        writeStart = timer()
        # Loop through all the saved Events
        for curEvent in events:
            if "reasons" in curEvent:
                # Save off some data for each event
                for curReason in curEvent["reasons"]:
                    curEventID = curEvent["id"]
                    curPath = curEvent["exampleRequest"]["path"]
                    curMethod = curEvent["exampleRequest"]["method"]

                    eventPath = "/api/v0/corps/%s/sites/%s/events/%s/expire" % \
                        (self.corp_name, site_name, curEventID)
                    expireURL = api_host + eventPath
                    # print(expireURL)
                    # exit()
                    # Actually make the call to expire the event
                    expireEvent, expireCode, expireError = self.getRequestData(expireURL, method="POST")
                    if expireCode == 200:
                        self.logOut("Expired event %s" % curEventID)
                        time.sleep(0.7)
                    else:
                        self.logOut("Error expiring %s" % curEventID)
                        self.logOut(expireError)

        writeEnd = timer()
        writeTime = writeEnd - writeStart
        writeTimeResult = round(writeTime, 2)
        self.logOut("Total Event Output Time: %s seconds" % writeTimeResult)
# bulk-unflag-ip

## Description

Simple script that will pull events for a delta period. It will then compare the exampleRequests of those Events to criteria to determine if it should unflag those IPs.

## Usage

python  unflag_ips.py --config conf.json

## Conf File Settings

| Key Name | Description |
|----------|-------------|
| email    | This is the e-mail of your Signal Sciences user |
| password | This is the password of your Signal Sciences user. If this is not provided you will need to use the API Token |
| apitoken | If this is provided it will be used INSTEAD of your password. If set you can leave password empty |
| corp_name | This is the API name of your corp. You can find it in one of the dashboard URLS |
| dash_sites | This is the array of API Names of your dashboard sites. You can put 1 or more in this list to pull data from multiple sites |
| from | The time to start from |
| until | The time to go to |

## Finding your Signal Sciences API Info

**CORP Name & Site Name**
You can find your Corp API Name and Site API Name in the dashboard URL. The `EXAMPLECORPNAME` would be the api name of your corp and and the `EXAMPLESITENAME` would be the api name of your site.

https://dashboard.signalsciences.net/corps/EXAMPLECORPNAME/sites/EXAMPLESITENAME/

So lets say my corp API name is `foocorp` and my Dashboard Site API Name is `barsite` then the URL woudl look like:

https://dashboard.signalsciences.net/corps/foocorp/sites/barsite/

**API Tokens**

Information on getting your API Token can be found at https://docs.signalsciences.net/using-signal-sciences/using-our-api/


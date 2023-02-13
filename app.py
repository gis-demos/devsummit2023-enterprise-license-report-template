import sys
import arcgis
from arcgis.gis import GIS
from pprint import pprint
import datetime as dt

# Create the datetime representing current time
now = dt.datetime.now()

def expires_in_30_days_or_expired(datetime_obj):
    """Return a boolean value to represent whether a datetime is within 30 
    days from now."""
    days_30 = dt.timedelta(days=30) # timedelta object representing a 30 day time period
    if datetime_obj < now:
        return True
    else:
        if datetime_obj - now <= days_30:
            return True
        else:
            return False

def datetime_of_timestamp(timestamp_value) -> dt.datetime:
    """Esri stores dates as timestamps in milliseconds. Use this 
    function to return a datetime object from a timestamp value."""
    timestamp_epoch = int(timestamp_value/1000)
    dt_value = dt.datetime.fromtimestamp(timestamp_epoch)
    return dt_value

def get_server_licenses(gis):
    gis_server_mgr = gis.admin.servers
    # is there a better way to get the hosting server? can't just index, it varies
    hosting_server_urls = [f'{s["url"]}/admin' for s in gis_server_mgr.properties["servers"] if s["serverRole"] == "HOSTING_SERVER"]
    if len(hosting_server_urls) == 0:
        return {} # no federated hosting servers
    gis_servers_by_url = {s.url: s for s in gis_server_mgr.list()}
    hosting_server = gis_servers_by_url[hosting_server_urls[0]]
    return hosting_server.system.licenses

def get_license_status(gis):
    days_30 = dt.timedelta(days=30) # timedelta object representing a 30 day time period
    server_license_status = {}
    for feature_license in get_server_licenses(gis).get('features', []):
        date_of_expiration = datetime_of_timestamp(feature_license['expiration'])
        if date_of_expiration - now <= days_30:
            server_license_status[feature_license['displayName']] = expires_in_30_days_or_expired(date_of_expiration)
    return server_license_status

def get_main_args():
    args = sys.argv[-3:] # last 3 args
    # validate args
    try:
        url, username, password = args
        if not url.startswith('http'): raise ValueError('first parameter must be Url')
    except ValueError:
        print('Usage: python app.py <url> <username> <password>')
        print('Please pass url, username, password as ordered args')
        sys.exit(1)
    return args

def main():
    url, username, password = get_main_args()
    gis:GIS = GIS(url=url, username=username, password=password)
    license_status = get_license_status(gis)
    expiring_features = [feature for feature in license_status if license_status[feature] == True]
    if len(expiring_features) > 0:
        # print features expiring
        print('Features expiring soon or expired:')
        pprint(expiring_features)
        # exit with non-success exit code to fail build
        sys.exit(1)
    else:
        print('All Licenses Ok!')

if __name__ == '__main__':
    main()
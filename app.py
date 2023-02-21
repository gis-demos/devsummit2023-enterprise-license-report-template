import os
import sys
import arcgis
from arcgis.gis import GIS
from pprint import pprint
import datetime as dt
import smtplib

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
    hosting_servers = gis.admin.servers.get(role="HOSTING_SERVER")
    if not hosting_servers:
        # no hosting server configured for gis instance
        return {}
    return hosting_servers[0].system.licenses

def get_license_status(gis):
    """
    Returns a dict of feature name keys
    with values of True if license is expiring/expired,
    or False if the license is valid through the threshold
    """
    server_license_status = {}
    for feature_license in get_server_licenses(gis).get('features', []):
        date_of_expiration = datetime_of_timestamp(feature_license['expiration'])
        is_expiring_concern = expires_in_30_days_or_expired(date_of_expiration)
        server_license_status[feature_license['displayName']] = is_expiring_concern
    return server_license_status

def send_report_email(license_status):
    license_summary = "\r\n".join([f"{i[0]}: {'Requires Attention' if i[1] else 'Valid'}" for i in license_status.items()])
    message = f"""
ArcGIS Licenses Report:

{license_summary}
    """
    send_smtp(["jroebuck@esri.com", "ssong@esri.com"], message)

def send_smtp(recipients, message,
                    subject="ArcGIS Licensing Report"):
    """Sends the `message` string to all of the emails in the 
    `recipients` using the configured SMTP email server."""
    smtp_config = get_smtp_config()
    smtp_server_url = smtp_config.get('server')
    sender= smtp_config.get('username')
    username = smtp_config.get('username')
    password = smtp_config.get('password')

    # Instantiate our server, configure the necessary security
    server = smtplib.SMTP(smtp_server_url, 587)
    server.ehlo()
    server.starttls() # Needed if TLS is required for the SMTP server
    server.login(username, password)

    # For each recipient, construct the message and attempt to send
    did_succeed = True
    for recipient in recipients:
        try:
            message_body = '\r\n'.join(['To: {}'.format(recipient),
                                        'From: {}'.format(sender),
                                        'Subject: {}'.format(subject),
                                        "",
                                        '{}'.format(message)])
            server.sendmail(sender, [recipient], message_body)
            print(f"Report sent to {recipient}")
        except:
            did_succeed = False
    
    # Cleanup and return
    server.quit()
    return did_succeed

def get_smtp_config():
    return {
        "server": os.environ.get("SMTP_SERVER"),
        "username": os.environ.get("SMTP_USERNAME"),
        "password": os.environ.get("SMTP_PASSWORD"),
    }

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
    send_report_email(license_status)
    
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
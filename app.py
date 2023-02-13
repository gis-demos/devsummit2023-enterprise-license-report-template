import sys
import arcgis
from arcgis.gis import GIS
from pprint import pprint

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
    print(f'Hello from arcgis {arcgis.__version__}, connected to {gis}')

if __name__ == '__main__':
    main()
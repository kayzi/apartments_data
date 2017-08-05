import csv
import json
import re
import sys
import datetime
import requests
import configparser
import RentalPropertyClass
from pathlib import Path
from bs4 import BeautifulSoup

def populate_csv(search_url, map_info, fname):
    """ Open and populate the CSV file. Create new file if none exist. """
    if Path(fname).is_file():
        access = 'a'
    else:
        access = 'w'

    # avoid the issue on Windows where there's an extra space every other line
    if sys.version_info[0] == 2:  # Not named on 2.6
        access += 'b'
        kwargs = {}
    else:
        access += 't'
        kwargs = {'newline': ''}
        
    # open file for writing
    csv_file = open(fname, access, **kwargs)

    # write to CSV
    try:
        writer = csv.writer(csv_file)
        if access[0] == 'w':
            header = ['Name', 'Address', 'Bedrooms', 'Bathrooms', 'Size', 'Rent',
                   'Available']
            writer.writerow(header)

        # parse current entire apartment list including pagination
        write_parsed_to_csv(search_url, map_info, writer)
    finally:
        csv_file.close()

def write_parsed_to_csv(page_url, map_info, writer):
    """Given the current page URL, extract the information from each apartment
       in the list."""

    # read the current page
    page = requests.get(page_url)
 
    # soupify the current page
    soup = BeautifulSoup(page.content, 'html.parser')
    soup.prettify()
    # only look in this region
    soup = soup.find('div', class_='placardContainer')

    # append the current apartments to the list
    for item in soup.find_all('article', class_='placard'):
        basicInfo = item.find('a', class_='placardTitle')
        
        # weird placards with no data
        if basicInfo is None: continue
        
        url = basicInfo.get('href')
        name = (basicInfo.string).strip()

        # get the address of the property
        address = getPropertyAddress(item)

        unitsDict = loadUnitsData(url)
        for unitKey in unitsDict:
            unit = RentalProperty(name, address, unitKey['Beds'], unitKey['Baths'],
                                  unitKey['SquareFootDisplay'], unitKey['RentDisplay'],
                                  unitKey['DateAvailableDisplay'])
            unit.exportToCSV(writer)
            
    return 

def getPropertyAddress(soup):
    # create the address from parts connected by comma (except zip code)
    address = ''

    # this can be either inside the tags or as a value for "content"
    obj = soup.find(itemprop='streetAddress')
    text = obj.get('content')
    if text is None:
        text = obj.getText()
    address += text

    obj = soup.find(itemprop='addressLocality')
    text = obj.get('content')
    if text is None:
        text = obj.getText()
    address += ', ' + text

    obj = soup.find(itemprop='addressRegion')
    text = obj.get('content')
    if text is None:
        text = obj.getText()
    address += ', ' + text

    obj = soup.find(itemprop='postalCode')
    text = obj.get('content')
    if text is None:
        text = obj.getText()
    # put the zip with a space before it
    address += ' ' + text
    
    return address


def loadUnitsData(url):
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')
    soupTags = soup.find_all('script', type='text/javascript')
    finalString = ''
    
    for aSoup in soupTags:
        code = str(aSoup.string)
        if 'rentals: ' in code:
            startInd = code.find('rentals: ')
            endInd = code.find('}],',startInd)
            finalString = code[startInd + 9:endInd + 2]
    info = json.loads(finalString)
    return info
    

def main():
    conf = configparser.ConfigParser()
    conf.read('config.ini')

    apartments_url = conf.get('all', 'apartmentsURL')
    fname = conf.get('all', 'fname') + '.csv'
    
    map_info = {}
    map_info['maps_url'] = conf.get('all', 'mapsURL')
    units = conf.get('all', 'mapsUnits')
    mode = conf.get('all', 'mapsMode')
    routing = conf.get('all', 'mapsTransitRouting')
    api_key = conf.get('all', 'mapsAPIKey')
    map_info['target_address'] = conf.get('all', 'targetAddress')

    # get the times for going to / coming back from work
    # and convert these to seconds since epoch, EST tomorrow
    """ map_info['morning'] = parse_config_times(conf.get('all', 'morning'))
    map_info['evening'] = parse_config_times(conf.get('all', 'evening'))
    map_info['maps_url'] += 'units=' + units + '&mode=' + mode + \
        '&transit_routing_preference=' + routing + '&key=' + api_key
    """

    populate_csv(apartments_url, map_info, fname)


class RentalProperty:
    """
    This is the rental property class. Each rental property contains
        the following information:
            - name of property
            - address
            - number of beds
            - number of baths
            - size in square feet
            - rent in US dollars
            - when that property is available
            - distance in miles from target set in config file
            - duration of travel from target set in config file
            - crime stats for that neighborhood
    """

    # Constructor
    def __init__(self, name, address, beds, baths, size, rent, available):
        self.data = ['']*7
        self.data[0] = name
        self.data[1] = address
        self.data[2] = beds
        self.data[3] = baths
        self.data[4] = size
        self.data[5] = rent
        self.data[6] = available
        #distanceStats = getDistance(self)
        #self.distance = distanceStats[0]
        #self.duration = distanceStats[1]

    # Returns array [distance, duration] calculated from Google Maps
    def getDistance(self):
        self.distance = self.address
        return

    # Returns neighborhood
    def getNeighborhood(self):
        return

    # Finds crime data for neighborhood from dictionary
    def getCrimeRate(self, crimeMap):
        return

    # Prints rental to console
    def printProperty(self):
        return

    # Appends rental to open CSV file
    def exportToCSV(self, writer):
        writer.writerow(self.data)
        return


if __name__ == '__main__':
    main()
    

#!/usr/bin/python
import argparse
import re
import urllib
import xml.etree.ElementTree as ElementTree

url = 'https://www.capmetro.org/planner/s_nextbus2.asp?stopid={}&route={}'

def main():
    parser = argparse.ArgumentParser(
        description='Display Capital Metro bus stop departures')
    parser.add_argument('route', type=int, help='the bus route number')
    parser.add_argument('stop', type=int, help='the bus stop id')
    parser.add_argument(dest='num_results', metavar='N', type=int, default=3,
        nargs='?', help='the number of departures to display (default: 3)')
    args = parser.parse_args()

    url_str = url.format(args.stop, args.route)
    xml_str = urllib.urlopen(url_str).read()
    xml_str = re.sub(' xmlns="[^"]+"', '', xml_str, count=1)
    root = ElementTree.fromstring(xml_str)

    stop = root.iter('Stop').next()
    print stop.find('Description').text

    departures = root.iter('Realtime')
    for i in range(args.num_results):
        try:
            departure = departures.next()
            print departure.find('Estimatedtime').text,
            print departure.find('Estimatedminutes').text.lstrip()
        except StopIteration:
            break

if __name__ == '__main__':
    main()

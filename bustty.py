#!/usr/bin/python
import argparse
import re
import urllib
import xml.etree.ElementTree as ElementTree

def get_nextbus_url(stop, route):
    base_url = 'https://www.capmetro.org/planner/s_nextbus2.asp?stopid={}'
    if route:
        return (base_url + '&route={}').format(stop, route)
    return base_url.format(stop)

def main():
    parser = argparse.ArgumentParser(
        description='Display Capital Metro bus stop departures')
    parser.add_argument('stop', type=int, help='the bus stop id')
    parser.add_argument('route', type=int, nargs='?',
        help='the bus route number')
    parser.add_argument('--n', metavar='N', dest='num_results', type=int,
        default=3, help='the number of departures to display (default: 3)')
    args = parser.parse_args()

    url_str = get_nextbus_url(args.stop, args.route)
    xml_str = urllib.urlopen(url_str).read()
    xml_str = re.sub(' xmlns="[^"]+"', '', xml_str, count=1)
    root = ElementTree.fromstring(xml_str)

    try:
        stop = root.iter('Stop').next()
        print stop.find('Description').text
    except StopIteration:
        print 'Invalid stop id:', args.stop
        exit(1)

    departures = root.iter('Run')
    for i in range(args.num_results):
        try:
            departure = departures.next()
            sign = departure.find('Sign').text
            realtime = departure.find('Realtime')
            time = realtime.find('Estimatedtime').text
            minutes = realtime.find('Estimatedminutes').text.lstrip()
            if minutes:
                print sign, minutes, 'min'
            else:
                print sign, time
        except StopIteration:
            break

if __name__ == '__main__':
    main()

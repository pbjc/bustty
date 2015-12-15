#!/usr/bin/python
import argparse
import re
import urllib
import xml.etree.ElementTree as ElementTree

class Departure:
    def __init__(self, sign, time, minutes):
        self.sign = sign
        self.time = time
        self.minutes = minutes

    def __str__(self):
        if self.minutes:
            return '{} {} min'.format(self.sign, self.minutes)
        else:
            return '{} {}'.format(self.sign, self.time)

class Stop:
    def __init__(self, stop, route=None, num_results=3):
        base_url = 'https://www.capmetro.org/planner/s_nextbus2.asp?stopid={}'
        self.nextbus_url = ''
        if route:
            self.nextbus_url = (base_url + '&route={}').format(stop, route)
        else:
            self.nextbus_url = base_url.format(stop)
        self.num_results = num_results
        self.description = ''
        self.departures = []

    def update(self):
        xml_str = urllib.urlopen(self.nextbus_url).read()
        xml_str = re.sub(' xmlns="[^"]+"', '', xml_str, count=1)
        root = ElementTree.fromstring(xml_str)

        try:
            stop_info = root.iter('Stop').next()
            self.description = stop_info.find('Description').text
        except:
            raise InvalidStopIdException

        self.departures = []
        runs = root.iter('Run')
        for i in range(self.num_results):
            try:
                run = runs.next()
                sign = run.find('Sign').text
                realtime = run.find('Realtime')
                time = realtime.find('Estimatedtime').text
                minutes = realtime.find('Estimatedminutes').text.lstrip()
                self.departures.append(Departure(sign, time, minutes))
            except StopIteration:
                break

    def __str__(self):
        lines = []
        lines.append(self.description)
        for departure in self.departures:
            lines.append(str(departure))
        return '\n'.join(lines)

class InvalidStopIdException(Exception):
    pass

def main():
    parser = argparse.ArgumentParser(
        description='Display Capital Metro bus stop departures')
    parser.add_argument('stop', type=int, help='the bus stop id')
    parser.add_argument('route', type=int, nargs='?',
        help='the bus route number')
    parser.add_argument('--n', metavar='N', dest='num_results', type=int,
        default=3, help='the number of departures to display (default: 3)')
    args = parser.parse_args()

    stop = Stop(args.stop, args.route, args.num_results)
    try:
        stop.update()
    except InvalidStopIdException:
        print 'Invalid stop id:', args.stop
        exit(1)
    print stop

if __name__ == '__main__':
    main()

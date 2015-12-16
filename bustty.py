#!/usr/bin/python
import argparse
import curses
import re
import time
import urllib
import xml.etree.ElementTree as ElementTree

def main():
    parser = argparse.ArgumentParser(
        description='Display Capital Metro bus stop departures')
    parser.add_argument('stop', type=int, help='the bus stop id')
    parser.add_argument('route', type=int, nargs='?',
        help='the bus route number, to show a single route')
    parser.add_argument('--n', metavar='N', dest='num_results', type=int,
        default=3, help='the number of departures to display (default: 3)')
    args = parser.parse_args()

    if not Stop.valid_stop_id(args.stop):
        print 'Invalid stop id:', args.stop
        exit(1)

    stop = Stop(args.stop, args.route, args.num_results)

    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    curses.mousemask(1)
    stdscr.keypad(1)
    stdscr.nodelay(1)

    secs = 0
    while True:
        if secs % 30 == 0:
            stop.update()
            stdscr.clear()
            stdscr.addstr(str(stop), curses.A_BOLD)
            stdscr.refresh()
            secs = 0

        time.sleep(1)
        secs += 1
        if stdscr.getch() != -1: break

    curses.curs_set(1)
    curses.nocbreak()
    curses.echo()
    curses.endwin()

class Stop:
    base_url = 'https://www.capmetro.org/planner/s_nextbus2.asp?stopid={}'

    def __init__(self, stop_id, route=None, num_results=3):
        if route:
            self.nextbus_url = (Stop.base_url + '&route={}').format(
                stop_id, route)
        else:
            self.nextbus_url = Stop.base_url.format(stop_id)
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

    @staticmethod
    def valid_stop_id(stop_id):
        xml_str = urllib.urlopen(Stop.base_url.format(stop_id)).read()
        return ElementTree.fromstring(xml_str)[0][0].find('faultcode') is None

    def __str__(self):
        lines = []
        lines.append(self.description)
        for departure in self.departures:
            lines.append(str(departure))
        return '\n'.join(lines)

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

class InvalidStopIdException(Exception):
    pass

if __name__ == '__main__':
    main()

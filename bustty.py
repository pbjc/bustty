#!/usr/bin/python
import argparse
import curses
import datetime
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
    parser.add_argument('--digital', action='store_true', dest='pretty_print',
        help='use a blocky font reminiscent of your microwave')
    parser.set_defaults(pretty_print=False)
    args = parser.parse_args()

    if not Stop.valid_stop_id(args.stop):
        print 'Invalid stop id:', args.stop
        exit(1)

    stop = Stop(args.stop, args.route, args.num_results)
    display = Display()
    display.begin()

    last_update = datetime.datetime.now() - datetime.timedelta(0, 30)
    while True:
        now = datetime.datetime.now()
        if (now - last_update).total_seconds() >= 30:
            stop.update()
            display.stdscr.clear()
            draw_method = display.stdscr.addstr
            if args.pretty_print:
                draw_method = display.draw_text
            try:
                draw_method(stop.description)
                draw_method('\n')
                for departure in stop.departures:
                    draw_method(departure.sign,
                        curses.color_pair(1) | curses.A_STANDOUT)
                    draw_method(' ')
                    draw_method(departure.time_notification(),
                        curses.color_pair(2) | curses.A_STANDOUT)
                    draw_method('\n')
            except:
                pass
            display.stdscr.refresh()
            last_update = now

        if display.any_input(): break

    display.end_session()

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
        [lines.append(str(departure)) for departure in self.departures]
        return '\n'.join(lines)

class InvalidStopIdException(Exception):
    pass

class Departure:
    def __init__(self, sign, time, minutes):
        self.sign = sign
        self.time = time
        self.minutes = minutes

    def time_notification(self):
        if self.minutes:
            return self.minutes + ' min'
        return self.time

    def __str__(self):
        return '{} {}'.format(self.sign, self.time_notification())

class Display:
    FONT_WIDTH = 3
    FONT_HEIGHT = 5
    font = {}

    def begin(self):
        self.stdscr = curses.initscr()
        self.addstr = self.stdscr.addstr
        self.stdscr.keypad(1)
        self.stdscr.nodelay(1)
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        curses.mousemask(1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

    def end_session(self):
        curses.mousemask(0)
        curses.curs_set(1)
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def draw_char(self, char, attribute=curses.A_STANDOUT):
        assert len(char) == 1
        orig_pos = self.stdscr.getyx()

        if char == '\n':
            self.stdscr.move(orig_pos[0] + Display.FONT_HEIGHT + 1, 0)
            return

        char = char.upper()
        bitmap = Display.font[char]
        for i in xrange(Display.FONT_HEIGHT):
            for j in xrange(Display.FONT_WIDTH):
                offset = i * Display.FONT_WIDTH + j
                self.stdscr.addstr(' ', attribute if bitmap[offset] else 0)
            self.stdscr.move(orig_pos[0] + i + 1, orig_pos[1])

        self.stdscr.move(orig_pos[0], orig_pos[1] + Display.FONT_WIDTH + 1)

    def draw_text(self, text, attribute=curses.A_STANDOUT):
        for char in text:
            self.draw_char(char, attribute)

    def any_input(self):
        return self.stdscr.getch() != -1

    font[' '] = [0] * 15
    font['-'] = [0,0,0,0,0,0,1,1,1,0,0,0,0,0,0]
    font['('] = [0,1,1,1,0,0,1,0,0,1,0,0,0,1,1]
    font[')'] = [1,1,0,0,0,1,0,0,1,0,0,1,1,1,0]
    font['/'] = [0,0,1,0,0,1,0,1,0,0,1,0,1,0,0]
    font[':'] = [0,0,0,0,1,0,0,0,0,0,1,0,0,0,0]
    font['0'] = [1,1,1,1,0,1,1,0,1,1,0,1,1,1,1]
    font['1'] = [0,1,0,1,1,0,0,1,0,0,1,0,1,1,1]
    font['2'] = [1,1,1,0,0,1,1,1,1,1,0,0,1,1,1]
    font['3'] = [1,1,1,0,0,1,1,1,1,0,0,1,1,1,1]
    font['4'] = [1,0,1,1,0,1,1,1,1,0,0,1,0,0,1]
    font['5'] = [1,1,1,1,0,0,1,1,1,0,0,1,1,1,0]
    font['6'] = [1,1,1,1,0,0,1,1,1,1,0,1,1,1,1]
    font['7'] = [1,1,1,0,0,1,0,0,1,0,1,0,0,1,0]
    font['8'] = [1,1,1,1,0,1,1,1,1,1,0,1,1,1,1]
    font['9'] = [1,1,1,1,0,1,1,1,1,0,0,1,1,1,1]
    font['A'] = [1,1,1,1,0,1,1,1,1,1,0,1,1,0,1]
    font['B'] = [1,1,1,1,0,1,1,1,0,1,0,1,1,1,1]
    font['C'] = [1,1,1,1,0,0,1,0,0,1,0,0,1,1,1]
    font['D'] = [1,1,0,1,0,1,1,0,1,1,0,1,1,1,0]
    font['E'] = [1,1,1,1,0,0,1,1,0,1,0,0,1,1,1]
    font['F'] = [1,1,1,1,0,0,1,1,0,1,0,0,1,0,0]
    font['G'] = [1,1,1,1,0,0,1,0,1,1,0,1,1,1,1]
    font['H'] = [1,0,1,1,0,1,1,1,1,1,0,1,1,0,1]
    font['I'] = [1,1,1,0,1,0,0,1,0,0,1,0,1,1,1]
    font['J'] = [0,0,1,0,0,1,0,0,1,1,0,1,1,1,1]
    font['K'] = [1,0,1,1,0,1,1,1,0,1,0,1,1,0,1]
    font['L'] = [1,0,0,1,0,0,1,0,0,1,0,0,1,1,1]
    font['M'] = [1,0,1,1,1,1,1,0,1,1,0,1,1,0,1]
    font['N'] = [1,1,1,1,0,1,1,0,1,1,0,1,1,0,1]
    font['O'] = [1,1,1,1,0,1,1,0,1,1,0,1,1,1,1]
    font['P'] = [1,1,1,1,0,1,1,1,1,1,0,0,1,0,0]
    font['Q'] = [1,1,1,1,0,1,1,0,1,1,1,1,0,0,1]
    font['R'] = [1,1,1,1,0,1,1,1,0,1,0,1,1,0,1]
    font['S'] = [1,1,1,1,0,0,1,1,1,0,0,1,1,1,1]
    font['T'] = [1,1,1,0,1,0,0,1,0,0,1,0,0,1,0]
    font['U'] = [1,0,1,1,0,1,1,0,1,1,0,1,1,1,1]
    font['V'] = [1,0,1,1,0,1,1,0,1,1,0,1,0,1,0]
    font['W'] = [1,0,1,1,0,1,1,0,1,1,1,1,1,0,1]
    font['X'] = [1,0,1,1,0,1,0,1,0,1,0,1,1,0,1]
    font['Y'] = [1,0,1,1,0,1,0,1,0,0,1,0,0,1,0]
    font['Z'] = [1,1,1,0,0,1,0,1,0,1,0,0,1,1,1]

if __name__ == '__main__':
    main()

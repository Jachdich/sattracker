#!/usr/bin/python

NOAA_18 = 28654
NOAA_15 = 25338
NOAA_19 = 33591
METEOR_M2_2 = 44387
METEOR_M2 = 40069

SATS = {"noaa 19": NOAA_19,
        "noaa 18": NOAA_18,
        "noaa 15": NOAA_15,
        "meteor m2-2": METEOR_M2_2,
        "meteor m2": METEOR_M2}

LAT = "56.026706451127"
LONG = "-5.7731581771188"
API_KEY = "E3VFDJ-UWRTXU-WX5PNC-4740"

import urllib.request
import io, json, datetime, sys, curses, time, traceback, threading

if sys.version_info[0] < 3:
    print("Error: this program requires python >2. Please make python3 the default python")

with open("debug.log", "w") as f:
    pass

def debug(message):
    with open("debug.log", "a") as f:
        f.write(message + "\n")

def pad(string, spaces, char, end="end"):
    characters = char * (spaces - len(string))
    if end == "end":
        return string + characters
    elif end == "start":
        return characters + string
    else:
        raise Exception("IllegalArgumentException: Expected 'start' or 'end', got '{}'".format(end))

def get_datetime(number):
    time = datetime.datetime.fromtimestamp(number)
    minute = pad(str(time.minute), 2, "0", end="start")
    hour =   pad(str(time.hour), 2, "0", end="start")
    day =    pad(str(time.day), 2, "0", end="start")
    month =  pad(str(time.month), 2, "0", end="start")

    if int(day) == datetime.datetime.now().day:
        return "{}:{}, today".format(hour, minute)
    elif int(day) - 1 == datetime.datetime.now().day:
        return "{}:{}, tomorrow".format(hour, minute)
    else:
        return "{}:{}, {}/{}".format(hour, minute, day, month)

class Passes:
    def __init__(self, days, degrees_min):
        self.data = {}
        self.days = days
        self.min_pass = degrees_min
        
        for sat in SATS:
            self.data[sat] = [None, -1]
    
    def getURL(self, SAT_ID, LAT, LONG, ALT, DAYS, MIN_PASS, API_KEY):
        return "https://www.n2yo.com/rest/v1/satellite/radiopasses/{sat_id}/{lat}/{long}/{alt}/{days}/{min_pass}/&apiKey={api_key}".format(
            sat_id = SAT_ID, lat = LAT, long = LONG, alt = ALT, days = DAYS, min_pass = MIN_PASS, api_key = API_KEY)
    
    def get_data(self, sat, fetch_new=False):
        if not fetch_new:
            if self.data[sat][1] > time.time() - 60 * 5 and self.data[sat][0] != None: #valid for 5 mins after fetch, otherwise fetch new
                return self.data[sat][0]
        
        url = self.getURL(SATS[sat], LAT, LONG, 0, self.days, self.min_pass, API_KEY)

        u = urllib.request.urlopen(url, data = None)
        f = io.TextIOWrapper(u,encoding='utf-8')
        text = f.read()
        
        data = json.loads(text)
        self.data[sat] = [data, time.time()]
        return data

def format_data(table):
    out = []
    out.append("Time             | Max elevation | Start heading | Mid heading | End heading")
    out.append("-----------------|---------------|---------------|-------------|------------")
    for p in table["passes"]:
        elevation = str(p["maxEl"])
        start_time = p["startUTC"]
        start_heading = str(p["startAzCompass"])
        mid_heading = str(p["maxAzCompass"])
        end_heading = str(p["endAzCompass"])

        out.append(pad(get_datetime(start_time), 17, " ") + "|" +
                pad(" " + elevation + "°", 15, " ") + "|" +
                pad(" " + start_heading, 15, " ") + "|" +
                pad(" " + mid_heading, 13, " ") + "|" +
                   " " + end_heading)
    return out

class UI:
    def __init__(self):
        self.exiting = False
        self.inputting = False
        self.input_function = None
        self.looping = True
        self.input_prompt = ""
        self.next_good_pass = "Downloading..."

        self.input_buffer = ""
        
        self.content = []
        
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)

        self.defaultbar_bottom = "f - simple frocast ║ p - specific predictions ║ q - quit"
        self.bottom_bar = self.defaultbar_bottom

        self.passes = Passes(20, 20)

    def centred(self, text, line):
        width = self.stdscr.getmaxyx()[1]
        size_text = len(text)
        total_spaces_len = width - size_text + 1
        side_spaces_len = total_spaces_len // 2
        self.stdscr.addstr(line, side_spaces_len, text)

    def init_initial_gui(self):
        self.draw_top_bar()
        self.draw_content()
        self.draw_bottom_bar()
        self.stdscr.move(self.stdscr.getmaxyx()[0] - 1, 0)
        self.stdscr.refresh()

    def draw_top_bar(self):
        self.centred("╚════NEXT GOOD PASS: {}════╝".format(self.next_good_pass), 0)

    def draw_content(self):
        for i, line in enumerate(self.content):
            if i + 2 > self.stdscr.getmaxyx()[0] - 5:
                break
            self.stdscr.move(i + 2, 0)
            self.stdscr.addstr(line)
        
    def draw_bottom_bar(self):
        if not self.inputting or self.exiting:
            self.stdscr.hline(self.stdscr.getmaxyx()[0] - 1, 0, " ", self.stdscr.getmaxyx()[1])
            self.stdscr.addstr(self.stdscr.getmaxyx()[0] - 2, 0, "━" * (self.stdscr.getmaxyx()[1]))
            self.centred(self.bottom_bar, self.stdscr.getmaxyx()[0] - 1)
        else:
            self.stdscr.move(self.stdscr.getmaxyx()[0] - 1, 0)
            self.stdscr.addstr(self.input_prompt)

    def update_next_good_pass(self):
        current_soonest_time = sys.maxsize
        current_best_pass = None
        for sat in SATS:
            sat_data = self.passes.get_data(sat)
            if not self.looping:
                return
            for sat_pass_data in sat_data["passes"]:
                sat_time = int(sat_pass_data["startUTC"])
                sat_el   = int(sat_pass_data["maxEl"])
                time_diff = sat_time - time.time()
                if time_diff < current_soonest_time and sat_el > 50:
                    current_soonest_time = time_diff
                    current_best_pass = [sat, sat_pass_data]
                    
        self.next_good_pass = ""
        p = current_best_pass[1]
        name = current_best_pass[0]
        elevation = str(p["maxEl"])
        start_time = p["startUTC"]
        start_heading = str(p["startAzCompass"])
        mid_heading = str(p["maxAzCompass"])
        end_heading = str(p["endAzCompass"])
        self.next_good_pass = name + ": " + (get_datetime(start_time) + " | " +
                               "In " + str(int((start_time - time.time()) // 60)) + " minutes | " +
                               elevation + "°" + " | " +
                               start_heading + " -> " +
                               mid_heading + " -> " +
                               end_heading)
                
    def forcast(self, name):
        self.content = format_data(self.passes.get_data(name.lower()))

    def event_thread(self):
        while self.looping:
            char = self.stdscr.getch()
            if char == ord("q"):
                self.exiting = True
                
            if self.exiting:
                if char == ord("y"):
                    self.shutdown()
                    
                elif char == ord("n"):
                    self.exiting = False
                    self.bottom_bar = self.defaultbar_bottom
                else:
                    self.bottom_bar = " Do you really want to exit? (Y/N) "

            if self.inputting:
                if char == curses.KEY_ENTER or char == 10 or char == 13:
                    self.inputting = False
                    self.bottom_bar = self.defaultbar_bottom
                    self.input_function(self.input_buffer)
                    debug(self.input_buffer)
                    self.input_buffer = ""
                    self.bottom_bar = self.defaultbar_bottom

                elif char == curses.KEY_BACKSPACE:
                    if len(self.input_buffer) > 0:
                        self.input_buffer = self.input_buffer[:-1]
                        self.stdscr.move(self.stdscr.getmaxyx()[0] - 1, self.stdscr.getyx()[1] - 1)

                else:
                    self.input_buffer += chr(char)
                    self.stdscr.addch(char)
                    self.stdscr.move(self.stdscr.getmaxyx()[0] - 1, self.stdscr.getyx()[1])

            if char == ord("f"):
                self.inputting = True
                self.input_function = self.forcast
                self.input_prompt = "Enter satellite name: "
                self.stdscr.move(self.stdscr.getmaxyx()[0] - 1, len(self.input_prompt))

            self.redraw()
    
    def mainloop(self):
        self.init_initial_gui()
        self.thread = threading.Thread(target=self.event_thread)
        self.thread.start()
        self.graphics_thread()
       
    def graphics_thread(self):
        while self.looping:
            self.update_next_good_pass()
            if not self.looping:
                return
            self.redraw()
            time.sleep(1)

    def redraw(self):
        if not self.looping:
            return
        y, x = self.stdscr.getyx()
        self.draw_top_bar()
        self.draw_content()
        self.draw_bottom_bar()
        self.stdscr.move(y, x)
        self.stdscr.refresh()
        
    def shutdown(self):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()
        self.looping = False
        sys.exit(0)
            

def main():
    ui = UI()
    try:
        ui.mainloop()
    except Exception as e:
        with open("error.txt", "w") as f:
            f.write(str(e) + "\n" + "".join("".join(traceback.format_tb(e.__traceback__))))
        ui.shutdown()
        

main()

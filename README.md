# SatTracker

Simple (And buggy currently, working on it!) command-line tool for predicting satellite passes. Currently supports NOAA 15, 18 and 19, METEOR m2 and m2-2.

## Installation

 - Go to https://www.n2yo.com/ and register an account
 - Follow the instructions on https://www.n2yo.com/api/ to get your API key
 - Edit the `main.py` file with your latitude, longitude and API key (TODO: make it less annoying)
 - Run `./install.sh` (`chmod +x install.sh` may be needed)
   - Alternatively, just run `main.py` in this directory

## Usage
```
$ sattrack --help
usage: sattrack [-h] [-s {noaa19,noaa18,noaa15,meteorm2-2,meteorm2}] [-d DAYS] [-a ANGLE] [-A]

Commandline interface to https://n2yo.com/

options:
  -h, --help            show this help message and exit
  -s {noaa19,noaa18,noaa15,meteorm2-2,meteorm2}, --satellite {noaa19,noaa18,noaa15,meteorm2-2,meteorm2}
                        Satellite name.
  -d DAYS, --days DAYS  Number of days to find predictions for. Default: 5
  -a ANGLE, --angle ANGLE
                        Minimum elevation required. Default: 40
  -A, --all-passes      Show all satellite passes
```

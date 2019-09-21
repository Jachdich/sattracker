# SatTracker

Simple (And buggy currently, working on it!) command-line tool for predicting satellite passes. Currently supports NOAA 15, 18 and 19, METEOR m2 and m2-2.

## Installation

 - Go to https://www.n2yo.com/ and register an account
 - Follow the instructions on https://www.n2yo.com/api/ to get your API key
 - Run `./install.sh` (`chmod +x install.sh` may be needed)
 - Run `sattrack --config api-key INSERT API KEY HERE`
 - Done! Run `sattrack` from the commandline to, um, run.

## Configuring

### Change threshhold for a 'good pass'

`sattrack --config min-pass DEGREES`

### Change your location

`sattrack --config lat <latetude>`
`sattrack --config long <longetude>`
`sattrack --config alt <altitude>`

### Add satellites

`sattrack --config addsat SATNAME <number>`

Number can be found by finding the satellite on https://n2yo.com/ and copying the number (i.e. https://www.n2yo.com/passes/?s=XXXXX&a=1 where XXXXX is the number)

## NOTES: actually none of the above features work yet, you'll have the source to change the API key or your location. I'm working on it!

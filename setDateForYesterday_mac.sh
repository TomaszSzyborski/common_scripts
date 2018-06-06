#!/bin/bash

#MMddhhmmyy format
yesterdayDate=$(date -jn -v -1d +'%m%d%H%M')
year=$(date -jn +'%Y')
string="$year"
lastTwoDigitsOfYear=${string: -2}

echo $yesterdayDate$lastTwoDigitsOfYear

sudo date $yesterdayDate$lastTwoDigitsOfYear
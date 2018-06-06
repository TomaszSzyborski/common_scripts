#!/bin/bash

#MMddhhmmyy format
tomorrowDate=$(date -jn -v +1d +'%m%d%H%M')
year=$(date -jn +'%Y')
string="$year"
lastTwoDigitsOfYear=${string: -2}

echo $tomorrowDate$lastTwoDigitsOfYear

sudo date $tomorrowDate$lastTwoDigitsOfYear
#!/bin/sh

cd openboxlogout/

for file in ./pofiles/*.po; do
    lang=`echo $file | cut -d "-" -f 2 - | cut -d "." -f 1`
    
    mkdir -p locale/$lang/LC_MESSAGES
    msgfmt --output-file="locale/$lang/LC_MESSAGES/oblogout.mo" "$file"
done

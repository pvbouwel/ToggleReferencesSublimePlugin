#!/bin/bash

if [ "`uname -s`" = "Darwin" ]
then
  echo "Processing on a Mac"
  SUBLIME_USER_PLUGIN_DIR="/Users/${USER}/Library/Application Support/Sublime Text 3/Packages/User/"
elif [ "`uname -s`" = "Linux" ]
then
  echo "Processing on a Linux"
  SUBLIME_USER_PLUGIN_DIR="$HOME/.config/sublime-text-3/Packages/User/"
else
  echo "Processing on an unknown OS -> aborting"
  exit -1
fi


if [ -d "${SUBLIME_USER_PLUGIN_DIR}" ]
then
  cp -v toggle_references.py "${SUBLIME_USER_PLUGIN_DIR}"
  echo "Script should be put in its place"
  echo "Read README.md to get instructions on usage"
else
  echo "This install script is only valid for Sublime 3 and for Mac OS X/Linux"
  echo "Seems like the right directories are not setup."
fi


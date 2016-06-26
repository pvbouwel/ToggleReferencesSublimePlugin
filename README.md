# Toggle References for Sublime v1.0.0

## Goal
Automatically build a reference list for a correspondence.  If you write a
correspondence in Sublime it can build a references list built from all URLS
from the text within square brackets ([]) for you and place it at
 the end of the correspondence.  You can toggle so in case you need to insert
 references you have no need to do the re-numbering manually.

## Version history
 * 1.0.0 First released version this version will replace only URLs from the text

## Development
Since the plugin needs to be triggered from Sublime itself debugging is mostly
done by logging to a file and building a trace that shows the program execution
path.  For this a simple FileLogger has been created.  If it is initialized with
 a filename of an existing file then the log will be appended to that file.  If
no such file exists then no logging will take place and executions will be
without logging (and thus slightly faster).

So to start debugging you can just touch the file and make sure it is writable.

## Installation

### Mac/Linux
By following these installation instructions you will put the plugin code in the
 plugin directory and therefore activate the plugin.

```
cd /tmp
git clone https://github.com/pvbouwel/ToggleReferencesSublimePlugin
cd ToggleReferencesSublimePlugin/
bash install.sh
```

### Make key binding
The advantage of key-bindings is that you can execute the key-binding to trigger
 toggle_references.py.  This allows to quickly toggle references.

#### Mac
Go to `Sublime Text` -> `Preferences` -> `Keybindings - user`
Enter a keymap like (watch out as there are a lot of key bindings already so do
not override another one:
`[{ "keys": ["alt+r"], "command": "toggle_references" }]`

## Run manually
Open the sublime console `` ctrl + ` `` and run the command using
`view.run_command('toggle_references')`.


## script file
`toggle_references.py`


## Contributors
 * https://github.com/pvbouwel



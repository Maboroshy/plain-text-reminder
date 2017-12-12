# Plain text reminder (!R)
Reminders in your plain text notes and to-do lists

**This application is at prototype stage. It doesn't yet has a GUI, so it's usability is limited. It hasn't been thoughtfully tested and should not be used on any valuable data. Bug reports and feature suggestions are welcome.**

!R continuously scans plain text files and makes specifically composed text (reminder tags) to show you show a pop-up reminder.

`@!10:00 Star Plain text reminder` somewhere in plain text file will remind you with text "Star Plain text reminder" next time it's 10 o'clock. 

Reminder tags can set time as absolute or as delta to current time. Support for recurring reminders is planned. There are many ways to compose a reminder tag. Read more about reminder tag syntax [here](docs/reminder-tag-syntax.md).

!R tries to be: 
- Minimalistic 
- Customizable
- Expandable
- Plain text

## Installation
!R requires [Python Interpreter 3.3+](https://www.python.org/downloads/), [watchdog](https://pypi.python.org/pypi/watchdog) and [dateutil](https://pypi.python.org/pypi/python-dateutil/) modules.

Install them by the package manager of your OS or: 
1. Download and install latest [Python Interpreter distribution](https://www.python.org/downloads/). 
2. Open cmd/terminal and run `pip install watchdog python-dateutil`.

Easier installation bundles will appear at the next stages of development.

## Usage
Currently there's only a limited CLI interface available.

You can practice with reminder tags syntax by running 
`python3 run.py -d` for Mac OS and GNU/Linux distributions or 
`python run.py -d` for Windows

You can test !R by running 
`python3 run.py -s path/to/folder_with_text_files/` for Mac OS and GNU/Linux distributions or 
`python run.py -s C:\path\to\folder_with_text_files\` for Windows

At the first run !R will create reminder.cfg file for its settings

!R will start parsing text files in provided path (relative or absolute). 
List of found reminders, messages for triggered reminders and available user actions will appear in cmd/terminal.


What !R really do: 
1. Parses plain text files in set folder for reminder tags. 
2. Watches set folder and reparses changed files. 
3. Replaces found reminder tags with ones that are independent of current time. Otherwise `@!10:00` will always be next 10 o'clock, rather than a single tomorrow 10'clock. 
4. Waits for a time of set reminders. 
5. Shows a pop-up with ability to reset or dismiss a reminder. 
6. Changes reminder tags in text files accordingly. 


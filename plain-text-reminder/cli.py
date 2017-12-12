import logging
import datetime

import model
import event_bus as ev


class CliInterface:
    __slots__ = ['event_q']

    def __init__(self):
        self.event_q = ev.get_event_queue('lists', 'alarm', 'invalid r tag')

    def run(self):
        broken_r_list = []
        got_list = None

        while True:
            if not got_list and self.event_q.empty():  # Show list once, after resolving all reminders
                ev.send('schedule', request='lists')

            got_list = False

            event = self.event_q.get()

            if event.type == 'timer started':
                print('\nTimer started. Next reminder at {}.'.format(event.r_obj.time_dt))
            elif event.type == 'invalid r tag':
                broken_r_list.append(event.data)
            elif event.type == 'lists':
                print_r_list(event.data, broken_r_list)
                broken_r_list = []
                got_list = True
            elif event.type == 'alarm':
                handle_alarm(event.r_obj)


class ParseDemo:
    __slots__ = ['cfg']

    def __init__(self, cfg):
        self.cfg = cfg

    def run(self):
        print('Enter tags without tag marker to see parse results. Enter "q" to quit.',
              '\nMind that time string with spaces should be put to brackets.')
        while True:
            cmd = input()
            if cmd == 'q' or cmd == 'Q':
                exit(0)
            try:
                r_obj = model.Reminder(cmd, None, self.cfg, datetime.datetime.today())
                print('Time:', str(r_obj.time_dt).partition('.')[0])
                if r_obj.view_text:
                    print('Text:', r_obj.view_text)
                if r_obj.time_dt < datetime.datetime.today():
                    print('Is past')
                if r_obj.is_recurring:
                    print('Is recurring')
            except ValueError:
                print("That doesn't look like anything")
            print('\n')


def print_r_list(r_list, broken_r_list):
    print('\nNext 10 reminders:')
    for r_obj in r_list:
        print(r_obj)

    if broken_r_list:
        print('\nFailed to parse:')
        for r_tag in broken_r_list:
            print(r_tag.strip())


def handle_alarm(alarmed_r_obj):
    print('\n!!! Reminder:')
    print('Time: {}'.format(alarmed_r_obj.time_dt))
    if alarmed_r_obj.view_text:
        print('Text: {}'.format(alarmed_r_obj.view_text))
    print('\nType "d" to dismiss or enter new date and time or time delta to reset reminder.',
          '\nExamples: "01.02 12:30", "9:00am", "+2m". Empty for default time.')

    logging.disable(logging.DEBUG)  # Disables logging, so it would not interrupt user input

    cmd_accepted = False
    while not cmd_accepted:
        cmd = input()
        if cmd == 'd' or cmd == 'D':
            alarmed_r_obj.dismiss()
            cmd_accepted = True
        else:
            try:
                alarmed_r_obj.set_with_other_time_str(cmd, datetime.datetime.today())
                cmd_accepted = True
            except ValueError:
                print('Incorrect date and time. Please, enter date and time that is later than now.')

    logging.disable(logging.NOTSET)  # Enables logging back

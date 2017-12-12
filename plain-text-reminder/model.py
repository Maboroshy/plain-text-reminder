import os
import re
import time
import logging
import datetime
import threading

import watchdog.events
import watchdog.observers

import event_bus as ev
import r_tag_parser

known_file_dict = {}  # Dict of all File objects with path as key
pending_file_list = []  # List of File objects, that were subject of FS events, waiting to be processed


class File:
    __slots__ = ['path', 'reminders', 'last_mtime', 'pending_parse', 'pending_remove', 'cfg']

    def __init__(self, path, cfg):
        self.path = path
        self.reminders = None
        self.last_mtime = None
        self.pending_parse = None
        self.pending_remove = None
        known_file_dict[self.path] = self
        self.cfg = cfg

    def put_to_pending(self, fs_event_type):
        pending_file_list.append(self)
        if fs_event_type == 'deleted':
            self.pending_remove = self.cfg.delay_parse
            known_file_dict.pop(self.path)
        elif self.last_mtime != os.path.getmtime(self.path) and self.last_mtime != 'now':
            if fs_event_type == 'created' and os.path.getsize(self.path) < self.cfg.file_size_limit:
                self.pending_parse = self.cfg.delay_parse
            elif fs_event_type == 'modified' and \
                    (self.path in known_file_dict.keys() or os.path.getsize(self.path) < self.cfg.file_size_limit):
                self.pending_remove = self.cfg.delay_parse
                self.pending_parse = self.cfg.delay_parse

                logging.debug('{} last parsed at:  {}'.format(os.path.basename(self.path), self.last_mtime))
                logging.debug('{} was modified at: {}'.format(os.path.basename(self.path), os.path.getmtime(self.path)))

    def process_pending(self):
        if self.pending_remove == 0:
            self.unschedule_all_r()
            self.pending_remove = None
        else:
            if self.pending_remove:
                self.pending_remove = self.pending_remove - 1

        if self.pending_parse == 0:
            self.parse(datetime.datetime.today())
            self.pending_parse = None
        else:
            if self.pending_parse:
                self.pending_parse = self.pending_parse - 1

        if self.pending_remove is None and self.pending_parse is None:
            pending_file_list.remove(self)
            logging.debug('{} moved out of pending'.format(os.path.basename(self.path)))

    def parse(self, now_dt):
        self.reminders = []
        new_lines_list = []
        text_is_altered = False
        in_r_block = False
        logging.info('Adding reminders of {}'.format(os.path.basename(self.path)))

        with open(self.path, 'r') as file:
            for line in file:
                if line[0:len(self.cfg.r_block_start_marker)] == self.cfg.r_block_start_marker:
                    in_r_block = True
                    new_lines_list.append(line)
                    continue
                elif in_r_block and not self.cfg.allow_empty_r_tags_in_r_block and not line.strip():
                    new_lines_list.append(line)
                    continue
                elif line[0:len(self.cfg.r_block_end_marker)] == self.cfg.r_block_end_marker:
                    in_r_block = False
                    new_lines_list.append(line)
                    continue
                elif not in_r_block and self.cfg.r_tag_marker not in line:
                    new_lines_list.append(line)
                    continue

                if in_r_block:
                    r_tags = line,  # creates a tuple
                else:
                    r_tags = [''.join((self.cfg.r_tag_marker, tag)) for tag in line.split(self.cfg.r_tag_marker)[1:]]

                for r_tag in r_tags:
                    try:
                        r_tag = ' '.join(r_tag.split(' ')[:self.cfg.max_words_in_r_tag])
                        r_obj = Reminder(r_tag, self, self.cfg, now_dt, in_r_block)
                        self.reminders.append(r_obj)

                        if r_tag != r_obj.r_tag:
                            line = line.replace(r_tag, r_obj.r_tag, 1)
                            text_is_altered = True

                    except ValueError:
                        ev.send('invalid r tag', data=r_tag)

                new_lines_list.append(line)

        logging.info(os.path.basename(self.path) + ' parsed')

        if text_is_altered:
            self.last_mtime = 'now'
            with open(self.path, 'w') as file:
                file.write(''.join(new_lines_list))
                logging.info(os.path.basename(self.path) + ' reminder tags stabilized')
            self.last_mtime = os.path.getmtime(self.path)

    def replace_r_tag_in_text(self, tag_to_replace, new_tag):
        with open(self.path, 'r') as file:
            text = re.sub('{}({}|{}|$)'.format(re.escape(tag_to_replace.strip('\r\n')),
                                               re.escape(self.cfg.r_tag_marker),
                                               re.escape(self.cfg.disabled_r_tag_marker)),
                          new_tag.strip('\r\n'), file.read(), flags=re.MULTILINE)

        self.last_mtime = 'now'
        with open(self.path, 'w') as file:
            file.write(text)
        self.last_mtime = os.path.getmtime(self.path)

    def unschedule_all_r(self):
        logging.info('Removing reminders of {}'.format(os.path.basename(self.path)))
        if self.reminders:
            for r_obj in self.reminders:
                logging.debug('    ' + str(r_obj))
                ev.send('schedule', request='remove', r_obj=r_obj)

    def __repr__(self):
        return self.path

    def __str__(self):
        return self.path


class RFile(File):
    def __init__(self, path, cfg):
        super().__init__(path, cfg)
        if not os.path.isfile(path):
            self.last_mtime = 'now'
            with open(path, 'w') as file:
                file.write(self.cfg.r_block_start_marker)
            self.last_mtime = os.path.getmtime(self.path)

    def add_r_to_file_text(self, r_obj):  # TODO
        self.last_mtime = 'now'
        with open(self.path, 'a') as file_text:
            file_text.write('\n' + r_obj.r_tag)
        self.last_mtime = os.path.getmtime(self.path)


class Reminder:
    __slots__ = ['r_tag', 'cfg', 'is_in_rblock', 'time_dt', 'is_recurring',
                 'raw_text', 'view_text', 'in_sec', 'in_file_obj']

    def __init__(self, r_tag, in_file_obj, cfg, now_dt, is_in_rblock=False):
        self.r_tag = r_tag
        self.cfg = cfg
        self.is_in_rblock = is_in_rblock
        self.time_dt, self.is_recurring, self.raw_text = r_tag_parser.parse(r_tag, self.cfg, now_dt)
        self.stabilize_r_tag()
        self.view_text = None
        self.update_view_text()
        self.in_sec = self.time_dt.timestamp()
        self.in_file_obj = in_file_obj
        self.schedule()

    def schedule(self):
        ev.send('schedule', request='add', r_obj=self)

    def unschedule(self):
        ev.send('schedule', request='remove', r_obj=self)

    def alarm(self):
        ev.send('alarm', r_obj=self)

    def stabilize_r_tag(self):
        """Change tag format to freeze reminder time for future parses."""
        stable_time_tag = self.time_dt.strftime(self.cfg.stable_r_tag_format)
        if self.is_recurring:
            stable_time_tag = stable_time_tag + '*'
        if self.cfg.spaces_in_stable_r_tag_format:
            stable_time_tag = stable_time_tag.join((self.cfg.r_tag_l_bracket, self.cfg.r_tag_r_bracket))

        if self.is_in_rblock:
            stable_r_tag = ''.join((stable_time_tag, self.raw_text))
        else:
            stable_r_tag = ''.join((self.cfg.r_tag_marker, stable_time_tag, self.raw_text))

        self.r_tag = stable_r_tag

    def update_view_text(self):
        limited_text = self.raw_text
        for char in self.cfg.r_text_ends_with_list:
            if char in limited_text:
                limited_text = limited_text.partition(char)[0]
        self.view_text = limited_text.strip()

    def set_with_other_time_str(self, time_str, now_dt):
        self.unschedule()
        self.time_dt, self.is_recurring = r_tag_parser.get_dt_from_str(time_str, self.cfg, now_dt)
        old_r_tag = self.r_tag
        self.stabilize_r_tag()
        self.in_file_obj.replace_r_tag_in_text(old_r_tag, self.r_tag)
        self.in_sec = self.time_dt.timestamp()
        self.schedule()

    def dismiss(self, remove_from_file=False):
        self.unschedule()

        if remove_from_file or self.is_in_rblock:
            replace_with = self.raw_text.lstrip()
        else:
            replace_with = self.r_tag.replace(self.cfg.r_tag_marker, self.cfg.disabled_r_tag_marker)

        self.in_file_obj.replace_r_tag_in_text(self.r_tag, replace_with)

    def __repr__(self):
        return ''.join((str(self.time_dt).partition('.')[0] + ' ' + self.view_text))

    def __lt__(self, other): return self.in_sec < other

    def __le__(self, other): return self.in_sec <= other

    def __eq__(self, other): return self.in_sec == other

    def __ne__(self, other): return self.in_sec != other

    def __gt__(self, other): return self.in_sec > other

    def __ge__(self, other): return self.in_sec >= other


class FsEventHandler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self, patterns=None, ignore_patterns=None, ignore_directories=False, case_sensitive=False, cfg=None):
        super().__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)
        self.cfg = cfg

    def on_any_event(self, event):
        if event.event_type == 'moved':
            new_file(event.src_path, self.cfg).put_to_pending('deleted')
            new_file(event.dest_path, self.cfg).put_to_pending('created')
        else:
            new_file(event.src_path, self.cfg).put_to_pending(event.event_type)


def new_file(path, cfg):
    if path in known_file_dict.keys():
        file = known_file_dict[path]
        logging.debug('"{}" is known.'.format(os.path.basename(path)))
    else:
        file = File(path, cfg)
        logging.debug('"{}" is new.'.format(os.path.basename(path)))

    return file


def scan_fs(scan_path, cfg):
    now_dt = datetime.datetime.today()
    if os.path.isfile(scan_path):
        File(scan_path, cfg).parse(now_dt)
    else:
        for root, subdirs, files in os.walk(scan_path):
            for file_path in files:
                if file_path.endswith(cfg.text_files_ext_list) and \
                        os.path.getsize(root + os.sep + file_path) < cfg.file_size_limit:
                    file = new_file(root + os.sep + file_path, cfg)
                    file.parse(now_dt)

    ev.send('scan complete')


def watch_fs_events(scan_path, cfg):

    observer = watchdog.observers.Observer()

    if os.path.isdir(scan_path):  # TODO Watch all provided paths simultaneously
        event_handler = FsEventHandler(patterns=[''.join(('*', ext)) for ext in cfg.text_files_ext_list],
                                       ignore_patterns=[os.sep + '.'], ignore_directories=True, cfg=cfg)
        observer.schedule(event_handler, scan_path, recursive=cfg.recursive_scan)
    else:
        event_handler = FsEventHandler(patterns=[scan_path])
        observer.schedule(event_handler, os.path.dirname(scan_path), recursive=False)

    observer.start()

    try:
        while True:
            for file_obj in pending_file_list:
                file_obj.process_pending()
            time.sleep(1)
    except Exception as err:
        logging.error('FS watcher stopped!{}'.format(err))
        observer.stop()
        observer.join()


def run(scan_path, cfg):
    scan_fs(scan_path, cfg)
    threading.Thread(target=watch_fs_events, args=(scan_path, cfg), daemon=True).start()

import os
import configparser

defaults = {
    'scan_path': '',  # used if not provided by command line argument
    'recursive_scan': 1,  # 1 for True, 0 for False
    'delay_parse': 2,  # seconds
    'text_files_ext_list': '.md .txt',  # spaces separate items
    'file_size_limit': 100000,  # bytes
    'r_tag_marker': '@!',
    'disabled_r_tag_marker': '@/',
    'r_tag_l_bracket': '(',
    'r_tag_r_bracket': ')',
    'r_text_ends_with_list': '! .',  # spaces separate items
    'max_words_in_r_tag': 20,
    'r_block_start_marker': '@!(((',
    'r_block_end_marker': ')))',
    'allow_empty_r_tags_in_r_block': 0,  # 1 for True, 0 for False
    'stable_r_tag_format': '%y-%m-%d/%H:%M',  # must include everything up to year
    'single_digit_tag_attr': 'hour',  # year, month, day, hour, minute
    'default_r_hour': '9',  # Used when reminder set by date only, 24H-format
    'default_r_min': '00',
    'last_day_r_can_jump_to_next_month': '1',  # When month is set and day is not, next reminder can jump to next month.
                                               # 1 for True, 0 for False
    }


class Cfg:  # TODO Update cfg file with settings added by updates

    delta_tag_attrs_begin_with = {'years': '(y|Y)', 'months': '(M|mo)', 'weeks': '(w|W)',
                                  'days': '(d|D)', 'hours': '(h|H)', 'minutes': '(m|mi)'}  # TODO Move to localization

    def __init__(self, file_path='reminder.cfg', cfg_section_name='DEFAULT'):
        self.name = cfg_section_name
        self.file_path = file_path

        if not os.path.isfile(file_path):
            cfg_parser_obj = self.make_default()
        else:
            cfg_parser_obj = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=None)
            cfg_parser_obj.read(self.file_path)

        for attr in cfg_parser_obj[cfg_section_name]:
            if attr[-4:] == 'list':
                value = tuple(cfg_parser_obj[cfg_section_name][attr].split(' '))
            elif cfg_parser_obj[cfg_section_name][attr].isdecimal():
                value = int(cfg_parser_obj[cfg_section_name][attr])
            else:
                value = cfg_parser_obj[cfg_section_name][attr]

            setattr(self, attr, value)

        self.prepare_constants_and_computed_settings()

    def make_default(self):
        cfg_parser_obj = configparser.ConfigParser(interpolation=None)
        cfg_parser_obj['DEFAULT'] = defaults

        with open(self.file_path, 'w') as cfg_file:
            cfg_parser_obj.write(cfg_file)

        return cfg_parser_obj

    def prepare_constants_and_computed_settings(self):
        self.r_text_ends_with_list = self.r_text_ends_with_list + (self.disabled_r_tag_marker,)

        self.len_r_tag_marker = len(self.r_tag_marker)
        self.len_r_tag_l_bracket = len(self.r_tag_l_bracket)
        self.len_r_tag_r_bracket = len(self.r_tag_r_bracket)

        if ' ' in self.stable_r_tag_format or '\t' in self.stable_r_tag_format:
            self.spaces_in_stable_r_tag_format = True
        else:
            self.spaces_in_stable_r_tag_format = False

        self.delta_tag_attrs_begin_with['seconds'] = '(s)'  # For testing only! stable_r_tag_format doesn't have secs!


if __name__ == '__main__':
    Cfg().make_default()
    print('Configuration file is reset to default. Please, start the program by "run.py".')

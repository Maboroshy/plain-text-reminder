import re
import logging
import datetime
import dateutil.parser
import dateutil.relativedelta


def get_items_from_time_str_with_text(r_tag, cfg):
    """Get time string and text string from reminder tag string"""
    if r_tag[:cfg.len_r_tag_marker] == cfg.r_tag_marker:
        r_tag = r_tag[cfg.len_r_tag_marker:]

    if r_tag[0:cfg.len_r_tag_l_bracket] == cfg.r_tag_l_bracket and cfg.r_tag_r_bracket in r_tag:
        tag_items = r_tag.partition(cfg.r_tag_r_bracket)
        time_str = tag_items[0][cfg.len_r_tag_l_bracket:]
        text = tag_items[2]
    else:
        for space in ' \t\n\r':
            tag_items = r_tag.partition(space)
            time_str = tag_items[0]
            text = tag_items[1] + tag_items[2]
            if tag_items[1]:
                break

    return time_str, text


def predict_missing(parse_result_dt, present_attrs, cfg, now_dt):
    r_dt = parse_result_dt
    got = present_attrs

    if not got.minute and not got.hour:
        r_dt = r_dt.replace(hour=cfg.default_r_hour, minute=cfg.default_r_min)
    elif not got.minute:
        r_dt = r_dt.replace(minute=0)

    if now_dt > r_dt:
        if got.minute and not got.hour and now_dt.date() == r_dt.date():
            r_dt = r_dt + datetime.timedelta(hours=1)

        if not got.year or got.year == now_dt.year:

            if not got.month or got.month == now_dt.month:

                if not got.day:
                    old_r_dt = r_dt
                    r_dt = r_dt + datetime.timedelta(days=1)

                    if not cfg.last_day_r_can_jump_to_next_month and got.month and r_dt.month != got.month:  # TODO TEST
                        r_dt = old_r_dt

            if not got.month and got.day:
                r_dt = r_dt + dateutil.relativedelta.relativedelta(months=1)

        if not got.year and got.month and got.day:
            r_dt = r_dt + dateutil.relativedelta.relativedelta(years=1)

    if got.year and not got.month and not got.day:
        raise ValueError

    return r_dt


def get_dt_from_str(time_str, cfg, now_dt):
    # Parse all attributes from tag's time string
    if time_str:
        if '*' in time_str:
            is_recurring = True  # TODO
            time_str = time_str.replace('*', ' ')
        else:
            is_recurring = False

        if '+' in time_str:
            is_delta = True
            time_str = time_str.replace('+', ' ')
        else:
            is_delta = False
    else:
        is_recurring = False
        is_delta = False

    # Parse time based on given format
    if not is_delta:
        now_dt = now_dt.replace(second=0, microsecond=0)

        if not time_str:
            kw_arg_dict = {'hour': cfg.default_r_hour, 'minute': cfg.default_r_min}
            parse_result_dt = now_dt.replace(**kw_arg_dict)
            present_attrs = dateutil.relativedelta.relativedelta(**kw_arg_dict)
        elif time_str.isdecimal():
            kw_arg_dict = {cfg.single_digit_tag_attr: int(time_str)}
            parse_result_dt = now_dt.replace(**kw_arg_dict)
            present_attrs = dateutil.relativedelta.relativedelta(**kw_arg_dict)
        else:
            parse_result_dt = dateutil.parser.parse(time_str, yearfirst=True, default=now_dt)
            # A hack to get incomplete parse results, alternative is comparing two complete results.
            present_attrs = dateutil.parser.parser()._parse(time_str, yearfirst=True)[0]

        time_dt = predict_missing(parse_result_dt, present_attrs, cfg, now_dt)
        logging.debug('Parsed "{}" as {}.'.format(time_str, time_dt))

    else:
        delta_rd = dateutil.relativedelta.relativedelta()

        if time_str.isdecimal():
            setattr(delta_rd, cfg.single_digit_tag_attr + 's', int(time_str))
        else:
            for attr in cfg.delta_tag_attrs_begin_with:
                result = re.search('(\d+)\s*?{}'.format(cfg.delta_tag_attrs_begin_with[attr]), time_str)
                if result:
                    try:
                        result = int(result.group(1))
                        setattr(delta_rd, attr, result)
                    except TypeError:
                        pass

        time_dt = now_dt + delta_rd
        logging.debug('Parsed "{}" as {} which is {}.'.format(time_str, delta_rd, time_dt))

    return time_dt, is_recurring


def parse(r_tag, cfg, now_dt):
    time_str, text = get_items_from_time_str_with_text(r_tag, cfg)
    time_dt, is_recurring = get_dt_from_str(time_str, cfg, now_dt)

    return time_dt, is_recurring, text

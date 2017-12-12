import time
import sched
import logging
import threading

import event_bus as ev


scheduler = sched.scheduler()
event_q = None
past_r = []


def test():
    logging.debug('Alarm')


def process_events():
    while True:
        event = event_q.get()
        if event.request == 'add':
            if event.r_obj.in_sec > time.time():
                event.r_obj.sched_obj = scheduler.enterabs(event.r_obj.in_sec, 0, test)
                logging.debug(event.r_obj.sched_obj)
                logging.debug('Scheduled {}'.format(event.r_obj))
                logging.debug('Scheduler queue: '.format(scheduler.queue))
            else:
                past_r.append(event.r_obj)
        elif event.request == 'remove':
            scheduler.cancel(event.r_obj.sched_obj)
        elif event.request == 'clear':
            scheduler.empty()
        elif event.request == 'lists':
            ev.send('lists', data=([item for item in scheduler.queue], past_r))


def init():
    global event_q
    event_q = ev.get_event_queue('schedule')


def start():
    threading.Thread(target=process_events, daemon=True).start()
    time.sleep(1)
    threading.Thread(target=scheduler.run, daemon=True).start()
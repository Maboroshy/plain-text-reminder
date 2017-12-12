import queue
import logging

queue_dict = {}


class Event:
    __slots__ = ['type', 'request', 'r_obj', 'data']

    def __init__(self, type, **kwargs):
        self.type = type
        for attr in kwargs:
            setattr(self, attr, kwargs[attr])


def get_event_queue(*event_types):
    new_queue = queue.Queue()

    if not event_types:
        event_types = 'all',

    for event_type in event_types:
        if event_type not in queue_dict:
            queue_dict[event_type] = set()

        queue_dict[event_type].add(new_queue)

    logging.debug('Created an event queue for event types: {}'.format(', '.join(event_types)))
    return new_queue


def send(event_type, **kwargs):
    logging.debug('Sending event: {}'.format(event_type))
    for key in queue_dict:
        if key == 'all' or key == event_type:
            for q in queue_dict[key]:
                q.put(Event(event_type, **kwargs))

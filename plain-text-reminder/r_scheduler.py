import time
import heapq
import logging
import threading

import event_bus as ev


class RScheduler:
    __slots__ = ['event_q', 'lock', 'r_heap']

    def __init__(self):
        self.event_q = ev.get_event_queue('schedule')
        self.lock = threading.Lock()
        self.r_heap = []

    def process_events(self):
        while True:
            event = self.event_q.get()
            with self.lock:
                if event.request == 'add':
                    heapq.heappush(self.r_heap, event.r_obj)
                    logging.debug('Scheduled {}'.format(event.r_obj))
                elif event.request == 'remove':
                    try:
                        self.r_heap.remove(event.r_obj)
                    except ValueError:
                        pass
                elif event.request == 'lists':
                    ev.send('lists', data=heapq.nsmallest(10, self.r_heap))

    def timer(self):
        while True:
            while not self.r_heap:
                time.sleep(1)
                logging.debug('Waiting for upcoming reminders.')

            next_r_obj = self.r_heap[0]
            till = next_r_obj.in_sec
            ev.send('timer started', r_obj=next_r_obj)
            logging.debug('Next reminder at {}.'.format(next_r_obj.time_dt))

            while True:
                if not self.r_heap or next_r_obj is not self.r_heap[0]:
                    logging.debug('Next reminder changed. Restarting timer.')
                    break

                logging.debug('Time until reminder: {}'.format(till - time.time()))

                if till - time.time() > 0:
                    time.sleep(1)
                else:
                    with self.lock:
                        heapq.heappop(self.r_heap)
                    ev.send('alarm', r_obj=next_r_obj)
                    if next_r_obj.is_recurring:
                        pass  # TODO
                    break

    def run(self):
        threading.Thread(target=self.process_events, daemon=True).start()
        threading.Thread(target=self.timer, daemon=True).start()

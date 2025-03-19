import time
import logging


class Timer(object):

    def __init__(self, msg, warnThreshold=60): # the warnThreshold input should follows configure's unit.
        self._t0 = None
        self._t1 = None
        self._currentTimeElapsed = None
        self._msg = msg
        self._configure = 'sec' # seconds default
        self._warnThreshold = warnThreshold

    '''
    Context manager
    '''

    def __enter__(self):
        self._t0 = time.time()
        return self

    def __exit__(self, *args):
        self._t1 = time.time()
        unit = {'sec': (1, 'seconds'),
                'min': (60, 'minutes'),
                'hrs': (60 * 60, 'hours')}
        self._currentTimeElapsed = (self._t1 - self._t0) / unit[self._configure][0]

        # long run time warning
        if self._currentTimeElapsed > self._warnThreshold:
            logging.warn(f'{self._msg}: {self._currentTimeElapsed:.4f} {unit[self._configure][1]}')
        else:
            logging.info(f'{self._msg}: {self._currentTimeElapsed:.4f} {unit[self._configure][1]}')

    def configureTimerDisplay(self, configure='sec'):
        self._configure = configure


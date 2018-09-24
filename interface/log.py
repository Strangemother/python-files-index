
import logging

logging.basicConfig(format='... %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

def log(level=1, *a):
    '''A standard log() function to print string to stdout using logger.info.
    One or more elements can be given. Each argument is converted to a str.

    You can provide a logging level sensative to the "-v" cli argument. By
    default the level=1.

    log('a message')
    log('many messages', { 'dict': 1 }, 'quick', 1, 'fox')
    log(1, 'one setting')
    log(2, 'two setting')
    '''
    if isinstance(level, int) is False:
        a = (level, ) + a
        level = 1

    log_info(*a)


def log_info(*prints):
    '''log the given argments to logger.nfo as strings. If _ALLOW_LOG is False,
    nothing is printed'''

    logger.info(' '.join(map(str, prints)))

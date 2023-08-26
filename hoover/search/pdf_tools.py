from threading import Thread
from subprocess import Popen, PIPE
import logging

log = logging.getLogger(__name__)


def split_pdf_file(streaming_content, _range):
    """Middleware streaming wrapper to split pdf file into a page range using pdftk."""
    log.warning('SPLIT PDF FILE')
    for chunk in streaming_content:
        yield chunk


def write_content_to_handle(content, handle):
    log.warning('writing content to handle %s', handle)
    try:
        for chunk in content:
            log.warning('write %s', len(chunk))
            handle.write(chunk)
    except Exception as e:
        log.exception(e)
        return
    finally:
        handle.close()
        log.warning('done writing - handle closed.')


def get_pdf_info(streaming_content):
    """Middleware streaming wrapper to extract pdf info using PDFTK and return it as json content"""
    log.warning('GET PDF INFO')
    proc = Popen("pdftk - dump_data", shell=True, stdin=PIPE, stdout=PIPE)
    writer = Thread(target=write_content_to_handle, args=(streaming_content, proc.stdin))
    writer.start()

    for line in proc.stdout.readlines():
        log.warning('line %s', line)
        yield line
        if proc.poll() is not None:
            # process closed
            proc.stdin.close()
            proc.stdout.close()
            break

    proc.join()
    writer.join()


def pdf_extract_text(streaming_content):
    """Middleware streaming wrapper to extract pdf text using PDF.js (for parity with frontend)"""
    log.warning('EXTRACT PDF TEXT')
    for chunk in streaming_content:
        yield chunk

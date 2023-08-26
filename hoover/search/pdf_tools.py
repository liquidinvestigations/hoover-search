import contextlib
import json
from threading import Thread
from subprocess import Popen, PIPE
import logging

log = logging.getLogger(__name__)


def write_content_to_handle(content, handle):
    log.warning('writing content to handle %s', handle)
    try:
        for chunk in content:
            if handle.closed:
                break
            handle.write(chunk)
    except Exception as e:
        log.exception(e)
        return
    finally:
        handle.close()


@contextlib.contextmanager
def run_script(script, content):
    proc = Popen(script, shell=True, stdin=PIPE, stdout=PIPE)
    writer = Thread(target=write_content_to_handle, args=(content, proc.stdin))
    writer.start()
    try:
        yield proc
    except Exception as e:
        log.exception(e)
    finally:
        proc.stdin.close()
        proc.stdout.close()
        if proc.poll():
            proc.terminate()
        proc.join()
        writer.join()


# def stream_script(script, content):
#     with run_script(script, content) as proc

def stream_script(script, content, chunk_size=16 * 1024):
    with run_script(script, content) as proc:
        while chunk := proc.stdout.read(chunk_size):
            yield chunk


def get_pdf_info(streaming_content):
    """Middleware streaming wrapper to extract pdf info using PDFTK and return it as json content"""
    script = "set -ex; timeout 120s pdftk - dump_data | grep NumberOfPages"

    with run_script(script, streaming_content) as proc:
        for line in proc.stdout.readlines():
            log.warning('line %s', line)
            key, val = tuple(map(str.strip, line.decode('ascii', errors='replace').split(':')))
            yield json.dumps({key: val}).encode('ascii', errors='replace')
            break


def split_pdf_file(streaming_content, _range):
    """Middleware streaming wrapper to split pdf file into a page range using pdftk."""
    script = f"set -ex; timeout 120s pdftk - cat '{_range}' output -"
    yield from stream_script(script, streaming_content)


def pdf_extract_text(streaming_content, method):
    """Middleware streaming wrapper to extract pdf text using PDF.js (for parity with frontend)"""
    script = "set -ex; timeout 120s pdftotext -"
    yield from stream_script(script, streaming_content)

def split_pdf_file(streaming_content, _range):
    """Middleware streaming wrapper to split pdf file into a page range using pdftk."""
    yield b'1'
    # for chunk in streaming_content:
    #     yield chunk


def get_pdf_info(streaming_content):
    """Middleware streaming wrapper to extract pdf info using PDFTK and return it as json content"""
    yield b'2'
    # for chunk in streaming_content:
    #     yield chunk


def pdf_extract_text(streaming_content):
    """Middleware streaming wrapper to extract pdf text using PDF.js (for parity with frontend)"""
    yield b'3'
    # for chunk in streaming_content:
    #     yield chunk

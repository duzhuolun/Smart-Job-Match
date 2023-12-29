import PyPDF2


def extract_text_from_pdf(pdf_file):
    """
    Extracts text from a PDF file using PyPDF2.

    :param pdf_file: A file object or file path representing a PDF.
    :return: Extracted text as a string.
    """
    # Create a PDF reader object from the file
    pdf_reader = PyPDF2.PdfReader(pdf_file)

    # Iterate over each page and extract text
    text_content = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text_content += page.extract_text()

    return text_content

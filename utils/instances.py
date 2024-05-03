import re

def str_is_number(input):
    try:
        float(input)
        return True
    except ValueError:
        return False
    
def is_numeric(input):
    """
    Check if the input is a numeric value.
    Parameters:
        input (int or float): The value to be checked.
    Returns:
        bool: True if the input is numeric (int or float), False otherwise.
    """
    if isinstance(input, (int, float)):
        return True
    else:
        return False

def is_stream_url(url):
    """
    Check if a given URL is a streaming URL.
    Parameters:
        url (str): The URL to be checked.
    Returns:
        bool: True if the URL matches the RTSP pattern ('rtsp://.*'), False otherwise.
    """
    rtsp_pattern = r'rtsp://.*'

    match = re.match(rtsp_pattern, url)
    if match:
        return True
    else:
        return False

def check_format(input):
    """
    Check the format of a given input and extract components.

    The expected format is 'x1:x2:x3' or 'x1 x2 x3',
    where 'x1', 'x2', and 'x3' are separated by a colon (':') or a space (' ').

    Parameters:
        input (str): The input to be checked and parsed.

    Returns:
        False: If the input does not match the expected format.
        list: A list containing the three components extracted from the input if the format is correct.
    """
    separators = [':', ' ']
    separator = None
    for sep in separators:
        if sep in input:
            separator = sep
            break

    if separator is None:
        return False

    components = input.split(separator)

    # Check for correct format
    if len(components) != 3:
        return False
    else:
        return components

def verify_coord_format(string):
    """
    Verify if a string matches any of the predefined coordinate formats.

    Parameters:
        string (str): The string to be checked for coordinate format.

    Returns:
        bool: True if the string matches any of the predefined coordinate formats, False otherwise.
    """
    if "+" or "-" in string:
        string = string.replace("+","")
        string = string.replace("-","")
        
    formats = [
        r"\b\w{3} \w{2} \w{2}\.\w{2}\b", 
        r"\b\w{1} \w{2} \w{2}\.\w{2}\b",  
        r"\b\w{2} \w{2}\b",
        r"\b\w{1} \w{2}\b",  
        r"\b\w{2} \w{2} \w{2}\b",  
        r"\b\w{1} \w{2} \w{2}\b",
        r"\b\w{2} \w{2} \w{2}\.\w\b" 
        r"\b\w{1} \w{2} \w{2}\.\w\b" 
    ]
    
    for pattern in formats:
        if re.match(pattern, string):
            return True
    
    return False

def check_exists(path):
    """
    Check if a file or directory exists at the given path.
    Parameters:
        path (str): The path to check for existence.
    Returns:
        bool: True if a file or directory exists at the given path, False otherwise.
    """
    import os
    if os.path.exists(path):
        return True
    else:
        return False
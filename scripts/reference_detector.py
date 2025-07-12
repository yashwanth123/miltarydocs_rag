import re

def detect_references(text):
    pattern = r'MIL-[A-Z]+-\d+'
    return list(set(re.findall(pattern, text)))

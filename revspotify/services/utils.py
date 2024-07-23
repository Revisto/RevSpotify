import re
import unidecode


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def clean_filename(filename):
    # Transliterate to closest ASCII representation
    ascii_str = unidecode.unidecode(filename)
    # Replace any remaining non-alphanumeric characters (excluding spaces) with underscores
    cleaned_filename = re.sub(r"[^a-zA-Z0-9 ._-]", "_", ascii_str)
    return cleaned_filename

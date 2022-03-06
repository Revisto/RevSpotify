"""
source: https://github.com/clee704/audiodiff
"""

import hashlib
import os
import subprocess


#: Default FFmpeg path
FFMPEG_BIN = 'ffmpeg'


def ffmpeg_path():
    """Returns the path to FFmpeg binary."""
    return os.environ.get('FFMPEG_BIN', FFMPEG_BIN)


def checksum(name, ffmpeg_bin=None):
    """Returns an SHA1 checksum of the uncompressed PCM (signed 24-bit
    little-endian) data stream of the audio file. Note that the checksums for
    the same file may differ across different platforms if the file format is
    lossy, due to floating point problems and different implementations of
    decoders.
    """
    if ffmpeg_bin is None:
        ffmpeg_bin = ffmpeg_path()
    args = [
        ffmpeg_bin,
        '-i', name,
        '-vn',
        '-f', 's24le',
        '-',
    ]

    # Check if the file is readable and raise an appropriate exception if not
    with open(name, "rb") as f:
        f.read(1)

    with open(os.devnull, 'wb') as fnull:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        sha1sum = _compute_sha1(proc.stdout)
        proc.wait()
        try:
            if sha1sum is None:
                raise ExternalLibraryError(proc.stderr.read())
            return sha1sum
        finally:
            proc.stdout.close()
            proc.stderr.close()

def _compute_sha1(f):
    hasher = hashlib.sha1()
    empty = True
    while True:
        data = f.read(hasher.block_size * 128)
        if not data:
            break
        empty = False
        hasher.update(data)
    if empty:
        return None
    return hasher.hexdigest()


class AudiodiffException(Exception):
    """The root class of all audiodiff-related exceptions."""


class ExternalLibraryError(AudiodiffException):
    """Raised when there is an error during running FFmpeg."""


def audio_equal(name1, name2, ffmpeg_bin=None):
    """Compares two audio files and returns ``True`` if they have the same
    audio streams.
    """
    return checksum(name1, ffmpeg_bin) == checksum(name2, ffmpeg_bin)
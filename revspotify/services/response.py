class Response:
    def __init__(self, music_address=None, error=None, service=None):
        self.music_address = music_address
        self.error = error
        self.service = service

    def is_success(self):
        return self.error is None

    def is_error(self):
        return self.error is not None

    def __str__(self):
        return f"Response(music_address={self.music_address}, error={self.error}, service={self.service})"

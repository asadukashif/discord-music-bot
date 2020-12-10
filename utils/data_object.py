from .helper import number_to_timeformat


class DataObject():
    def __init__(self, data: dict) -> None:
        self.title = data.get('title')
        self.url = data.get('webpage_url')
        self.song_id = data.get('id')
        self.author = data.get('uploader')
        self.thumbnail = data.get('thumbnails')[0].get('url')
        self.duration_secs = data.get('duration')
        self.filepath = data.get('filepath')
        self.duration = number_to_timeformat(self.duration_secs)

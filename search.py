from google_images_search import GoogleImagesSearch
from random import randrange
from utils import envar
from enum import Enum


class Type(Enum):
    PRECISE = 0
    RANDOM = 1


class Index:
    def __init__(self):
        self._i = 0

    @property
    def i(self):
        return self._i

    def set_next(self, search_type: Type, size):
        if search_type == Type.PRECISE:
            self._i += 1
            self._i %= size
        elif search_type == Type.RANDOM:
            self._i = randrange(size)
        return self._i

    def reset(self):
        self._i = 0
        return self._i

    
class ResultType:
    fileType = None

class Picture(ResultType):
    fileType = "jpg|png"

class Animation(ResultType):
    fileType = "gif"


class Engine:
    def __init__(self):
        self.params = {"q": None, 'num': 10}
        self.result_type = None
        self.results = []

    def search(self, query: str, result_type: ResultType, **kwargs):
        gis = GoogleImagesSearch(envar("API_KEY"), envar("DEVELOPER_GCX"))
        self.params["q"] = query
        self.result_type = result_type
        self.params.update(**kwargs)
        self.params["fileType"] = getattr(result_type, "fileType")
        gis.search(self.params)
        self.results = gis.results()
        return self.results

    def search_once(self, query: str, result_type: ResultType, **kwargs):
        gis = GoogleImagesSearch(envar("API_KEY"), envar("DEVELOPER_GCX"))
        params = self.params
        params.update(kwargs)
        params["q"] = query
        params["fileType"] = getattr(result_type, "fileType")
        gis.search(params)
        return gis.results()

    @property
    def query(self):
        return self.params["q"]

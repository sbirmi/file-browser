from Utils import (
        ErrorResponse,
    )

class Search:
    def __init__(self, search_str):
        self.search_str = search_str
        self.tokens = [t for t in self.search_str.split(" ") if t]

        self.error_response = False
        for t in self.tokens:
            self.error_response = Search.invalid_token(t)
            if self.error_response:
                break

        self.filtering = self.tokens

    @staticmethod
    def invalid_token(tok):
        if len(tok) < 3:
            return ErrorResponse("Search parameter too short", tok)

    def match(self, row):
        assert not self.error_response
        assert self.filtering
        return self.search_str in row.file_ts

import itertools

from Utils import (
        ErrorResponse,
    )

class SearchParam:
    def __init__(self, tok):
        self.negate = tok.startswith("!")
        self.tok = tok if not self.negate else tok[1:]
        self.error_response = None

    def match(self, field):
        raise NotImplementedError

    @staticmethod
    def impl(tok):
        if tok.lower() in {"tagged", "!tagged"}:
            return TaggedParam(tok)
        return SubstrParam(tok)

class SubstrParam(SearchParam):
    """Looks for substring match in file_ts and tags
    """
    def __init__(self, tok):
        super(SubstrParam, self).__init__(tok)

        if len(self.tok) < 3:
            self.error_response = ErrorResponse("Search parameter too short", self.tok)

    def match(self, row):
        """
        Negative match against any field returns False, else
        Positive match against any field returns True, else
        return None
        """
        def match_field(field):
            """
            With negated search, always returns True or False
            With positive search, returns True, None
            """
            if self.negate:
                return self.tok not in field

            if self.tok in field:
                return True
            return None

        field_res = None
        for field in itertools.chain([row.file_ts], row.tags):
            res = match_field(field)
            print("Matching", self.tok, "against", field, res)
            if res is False:
                return False
            field_res = field_res or res

        return field_res

class TaggedParam(SearchParam):
    """Returns True if file is tagged, False otherwise.
    Behavior tweaked by leading "!"
    """
    def __init__(self, tok):
        super(TaggedParam, self).__init__(tok)

    def match(self, row):
        return bool(row.tags) ^ self.negate

class Search:
    def __init__(self, search_str):
        self.search_str = search_str
        self.params = [SearchParam.impl(t) for t in self.search_str.split(" ") if t]

        self.error_response = False
        for t in self.params:
            self.error_response = t.error_response
            if self.error_response:
                break

        self.filtering = bool(self.params)

    def match(self, row):
        assert not self.error_response
        assert self.filtering

        for token in self.params:
            token_res = token.match(row)

            # All params must match
            if token_res is not True:
                return False

        return True

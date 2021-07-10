import enum


class ArticleType(enum.IntEnum):
    REGULAR = 0
    MEDIUM = 1


class ArticleStatus(enum.IntEnum):
    DRAFT = 0
    REVIEWED = 1
    PUBLISHED = 2
    DELETED = 3

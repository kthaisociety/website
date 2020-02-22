import enum


class ArticleStatus(enum.IntEnum):
    DRAFT = 0
    REVIEWED = 1
    PUBLISHED = 2
    DELETED = 3

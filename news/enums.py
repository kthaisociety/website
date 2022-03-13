import enum


class ArticleType(enum.IntEnum):
    REGULAR = 0
    MEDIUM = 1


class ArticleStatus(enum.IntEnum):
    DRAFT = 0
    REVIEWED = 1
    PUBLISHED = 2
    DELETED = 3


class PostType(enum.IntEnum):
    FACEBOOK = 0
    INSTAGRAM = 1
    TWITTER = 2
    YOUTUBE = 3
    LINKEDIN = 4
    MEDIUM = 5
    GITHUB = 6


class FactStatus(enum.IntEnum):
    DRAFT = 0
    REVIEWED = 1
    PUBLISHED = 2
    DELETED = 3

import enum


class ContactType(enum.IntEnum):
    REPRESENTATIVE = 0
    RECRUITER = 1
    TECHNICAL = 2


class OfferType(enum.IntEnum):
    INTERNSHIP = 0
    SUMMER_INTERNSHIP = 1
    PART_TIME = 2
    FULL_TIME = 3
    VOLUNTEER = 4
    OTHER = 5

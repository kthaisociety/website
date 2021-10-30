import enum


class UserType(enum.IntEnum):
    ORGANISER = 0
    PARTICIPANT = 1
    SPONSOR = 2


class GenderType(enum.IntEnum):
    NONE = 0
    FEMALE = 1
    MALE = 2
    NON_BINARY = 3


GenderType.labels = {
    GenderType.NONE: "Prefer not to say",
    GenderType.FEMALE: "Women",
    GenderType.MALE: "Men",
    GenderType.NON_BINARY: "Non-binary",
}
GenderTypeDict = GenderType.labels


GenderType.colours = {
    GenderType.NONE: "#3a3a3a",
    GenderType.FEMALE: "#ed1a3e",
    GenderType.MALE: "#ebc934",
    GenderType.NON_BINARY: "#00abe7",
}
GenderTypeColoursDict = GenderType.colours


class DietType(enum.IntEnum):
    LACTOSE = 0
    GLUTEN = 1
    VEGETARIAN = 2
    VEGAN = 3
    OTHER = 4


DietType.labels = {
    DietType.LACTOSE: "Lactose intolerant",
    DietType.GLUTEN: "Gluten intolerant",
    DietType.VEGETARIAN: "Vegetarian",
    DietType.VEGAN: "Vegan",
    DietType.OTHER: "Other",
}
DietTypeDict = DietType.labels

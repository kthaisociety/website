import os

APP_NAME = "KTH AI Society"
APP_DESCRIPTION = "KTH AI Society website"
APP_TIMEZONE = "Europe/Stockholm"
APP_DOMAIN = os.environ.get("APP_DOMAIN", "localhost:8000")
APP_IP = os.environ.get("APP_IP", "localhost:8000")
APP_EMAIL_CONTACT = "contact@kthais.com"
APP_ORGANISER_EMAIL_REGEX = "^.*@kthais\.com$"
APP_EMAIL_WEBDEV = "webdev@kthais.com"
APP_EMAIL_NOREPLY = "noreply@kthais.com"

APP_SN_FACEBOOK = "KTHAISociety"
APP_SN_INSTAGRAM = "kthaisociety"
APP_SN_LINKEDIN = "kth-ai-society"
APP_SN_GITHUB = "kthaisociety"

APP_EMAIL_PREFIX = "[" + APP_NAME + "] "

APP_LEGAL_NAME = "KTH AI Society"
APP_LEGAL_ORGANISATION_NAME = "Tekniska Högskolans Studentkår"
APP_LEGAL_ORGANISATION_NUMBER = "802518-7249"
APP_LEGAL_ORGANISATION_BANKGIRO = "557-9198"
APP_LEGAL_ADDRESS_1 = "Drottning Kristinas Väg 15-19"
APP_LEGAL_ADDRESS_2 = ""
APP_LEGAL_POSTCODE = "100 44"
APP_LEGAL_CITY = "Stockholm"
APP_LEGAL_COUNTRY = "Sweden"

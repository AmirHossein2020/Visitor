PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_INDIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ENGLISH_DIGITS = "0123456789"

_DIGIT_TRANSLATION = str.maketrans(PERSIAN_DIGITS + ARABIC_INDIC_DIGITS, ENGLISH_DIGITS * 2)


def normalize_digits_to_english(value):
    return str(value or "").translate(_DIGIT_TRANSLATION)


def normalize_phone(value):
    return normalize_digits_to_english(value).strip()



# Produce a sorting key for a given title, such that datatables.js can use it to order titles like the game does.
# The key we produce is a string, but won't look anything like the actual title of the song; we just want it to
# be a list of keys that correspond to the characters of the string, where each key will be ordered based on
# where it falls in the final ordering scheme.  It's a string so that javascript compares it like a string.
# Knowing this, we convert each title to a list of numbers such that when strings of those numbers are compared,
# the corresponding titles are ordered the way we want.
# The 3icecream songdata.js "searchable_name" field is a pre-computed (THANK YOU Sunny!!) intermediary, where the japanese
# characters have been replaced by their hirigana equivalents, and strange characters have been unstrangeified (e.g. oversoul)
# So to produce our list of numbers for a final sort key, we need only convert each of the characters in the searchable_name
# to a number.
# Based on my experience with the game and looking through 3icecream's sorting code, I think the correct ordering is:
# - the vowel elongation character
# - japanese characters
# - letters
# - numbers
# Note that "symbols" does not appear here, because (I think) symbols should be normalized away by the searchable_title.
VOWEL_ELONGATION_CODE = 0x30FC
VOWEL_ELONGATION_KEY = ord('a') # start somewhere sane.

KATAKANA_CODE_LOWER = 0x30A1
KATAKANA_CODE_UPPER = 0x30F6
HIRIGANA_CODE_LOWER = 0x3041
HIRIGANA_CODE_UPPER = 0x3096
KATAKANA_HIRIGANA_CODE_OFFSET = KATAKANA_CODE_LOWER - HIRIGANA_CODE_LOWER
HIRIGANA_VOICED_CODES = [0x304C, 0x304E, 0x3050, 0x3052, 0x3054, 0x3056, 0x3058, 0x305A, 0x305C, 0x305E, 0x3060, 0x3062, 0x3065, 0x3067, 0x3069, 0x3070, 0x3073, 0x3076, 0x3079, 0x307C]
HIRIGANA_SEMI_VOICED_CODES = [0x3071, 0x3074, 0x3077, 0x307A, 0x307D]
HIRIGANA_SMALL_CODES = [0x3041, 0x3043, 0x3045, 0x3047, 0x3049, 0x3063, 0x3083, 0x3085, 0x3087, 0x308E, 0x3095, 0x3096]
JAPANESE_KEY = VOWEL_ELONGATION_KEY + 1

LOWERCASE_CODE_LOWER = ord('a')
LOWERCASE_CODE_UPPER = ord('z')
UPPERCASE_CODE_LOWER = ord('A')
UPPERCASE_CODE_UPPER = ord('Z')
LOWERCASE_UPPERCASE_CODE_OFFSET = LOWERCASE_CODE_LOWER - UPPERCASE_CODE_LOWER
ALPHABET_KEY = JAPANESE_KEY + (HIRIGANA_CODE_UPPER - HIRIGANA_CODE_LOWER) + 2

DIGIT_CODE_LOWER = ord('0')
DIGIT_CODE_UPPER = ord('9')
DIGIT_KEY = ALPHABET_KEY + 27

def sort_key(searchable_title):
	ret = ''
	for character in searchable_title:
		char_code = ord(character)
		
		if (char_code == VOWEL_ELONGATION_CODE):
			ret += (chr(VOWEL_ELONGATION_KEY))
			continue

		if (KATAKANA_CODE_LOWER <= char_code <= KATAKANA_CODE_UPPER):
			char_code -= KATAKANA_HIRIGANA_CODE_OFFSET
		if (HIRIGANA_CODE_LOWER <= char_code <= HIRIGANA_CODE_UPPER):
			if char_code in HIRIGANA_VOICED_CODES:
				char_code -= 1
			elif char_code in HIRIGANA_SEMI_VOICED_CODES:
				char_code -= 2
			elif char_code in HIRIGANA_SMALL_CODES:
				char_code += 1
			ret += (chr(char_code - HIRIGANA_CODE_LOWER + JAPANESE_KEY))
			continue

		if (LOWERCASE_CODE_LOWER <= char_code <= LOWERCASE_CODE_UPPER):
			char_code -= LOWERCASE_UPPERCASE_CODE_OFFSET
		if (UPPERCASE_CODE_LOWER <= char_code <= UPPERCASE_CODE_UPPER):
			ret += (chr(char_code - UPPERCASE_CODE_LOWER + ALPHABET_KEY))
			continue

		if (DIGIT_CODE_LOWER <= char_code <= DIGIT_CODE_UPPER):
			ret += (chr(char_code - DIGIT_CODE_LOWER + DIGIT_KEY))
		# everything else is ignored, including spaces.
	return ret
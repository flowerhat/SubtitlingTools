# -*- coding: utf-8 -*-
"""
Realign timeline based on the integrity of sentence.

An intuitive example:
    00:00:03.689 --> 00:00:08.570
    Hey programmers, I'm Alvin l come to our course
    on dynamic programming. So dynamic programming

    00:00:08.570 --> 00:00:10.436
    is one of my most favorite topics to teach.

Will be refactoring to:
    00:00:03.689 --> 00:00:07.388
    Hey programmers, I'm Alvin l come to our course on dynamic programming.

    00:00:07.388 --> 00:00:10.436
    So dynamic programming is one of my most favorite topics to teach.
"""

from collections import deque
import codecs

from translators import baidu as translator
from pysrt import SubRipFile, SubRipItem
import nltk

# macro
START_POSITION, END_POSITION, START_TIME, END_TIME, ORIGINAL_TEXT, TRANSLATED_TEXT = 0, 1, 2, 3, 5, 6

# configure
INPUT_PATH = r"e:\Youtube\Dynamic Programming.en.1.vtt"
OUTPUT_PATH = r"e:\output2.vtt"
TOKENIZE_MODEL = 'tokenizers/punkt/english.pickle'
SRC_LANG, DST_LANG = 'en', 'zh'
OUTPUT_TEXT_TYPE = ORIGINAL_TEXT  # ORIGINAL_TEXT OR TRANSLATED_TEXT


def calculate(x1: float, y1: float, y2: float):
    return (x1 / y1) * y2


def initialize_items() -> deque[:SubRipItem]:
    items = deque()
    with codecs.open(INPUT_PATH, 'r', encoding='utf-8') as f:
        for o in SubRipFile.stream(f):
            o.text = o.text.replace('\n', ' ') + ' '
            o.length = len(o.text)  # insert new attribute
            items.append(o)
    return items


def initialize_all_sentences(items) -> list[:dict]:
    text = ''.join(o.text for o in items)
    spans = nltk.data.load(TOKENIZE_MODEL).span_tokenize(text)
    return [dict([(START_POSITION, s[0]), (END_POSITION, s[1]), (ORIGINAL_TEXT, text[s[0]: s[1]])]) for s in spans]


def realign_timeline_based_on_the_integrity_of_sentence(items, sentences):
    item = items.popleft()
    start_pos, step, start_time = 0, item.length, item.start
    for sentence in sentences:
        while not start_pos <= sentence[END_POSITION] <= (start_pos + step):
            start_pos += item.length
            item = items.popleft()
            step = item.length
        else:
            time_span = int(calculate((sentence[END_POSITION] - start_pos + 1), step, (item.duration.ordinal / 1000.0)))
            sentence[START_TIME] = start_time
            sentence[END_TIME] = item.start + time_span
            start_time = sentence[END_TIME]


def merge_short_sentence_to_previous(sentences):
    done = []
    for ths in sentences:
        if len(ths[ORIGINAL_TEXT]) > 16:
            done.append(ths)
        else:
            prev: dict = done.pop()
            new_text = ' '.join([prev[ORIGINAL_TEXT], ths[ORIGINAL_TEXT]])
            prev[END_POSITION], prev[END_TIME], prev[ORIGINAL_TEXT] = ths[END_POSITION], ths[END_TIME], new_text
            done.append(prev)
    return done


def insert_translation(items) -> list[:dict]:
    total = len(items)
    cache = deque(maxlen=32)
    translations = []
    for i, o in enumerate(items):
        cache.append(o[ORIGINAL_TEXT])
        if (i % 32) == 31:
            print(total - i + 1, "less")
            translations.extend(translator('\n'.join(cache), SRC_LANG, DST_LANG, sleep_seconds=2).split('\n'))
            cache.clear()
    if len(cache) > 0:
        translations.extend(translator('\n'.join(cache), SRC_LANG, DST_LANG, sleep_seconds=2).split('\n'))
    for i, s in enumerate(translations):
        items[i][TRANSLATED_TEXT] = s


def output_file(done):
    if OUTPUT_TEXT_TYPE == TRANSLATED_TEXT:
        insert_translation(done)
    buffer = ["WEBVTT\nKind: captions\nLanguage: {}\n\n".format(SRC_LANG)]
    template = "{} --> {}\n{}\n\n"
    buffer.extend([template.format(str(o[START_TIME]), str(o[END_TIME]), o[OUTPUT_TEXT_TYPE]) for o in done])
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.writelines(''.join(buffer))


def app():
    items: deque[:SubRipItem] = initialize_items()
    sentences: list[:dict] = initialize_all_sentences(items)
    realign_timeline_based_on_the_integrity_of_sentence(items, sentences)
    done = merge_short_sentence_to_previous(sentences)
    output_file(done)


if __name__ == '__main__':
    app()

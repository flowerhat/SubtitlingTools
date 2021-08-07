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

Glossary:
    sp: start position   st: start time
    ep: end position    et: end time
"""

from collections import deque
import codecs
from pysrt import SubRipFile, SubRipItem
import nltk


def calculate(x1: float, y1: float, y2: float):
    return (x1 / y1) * y2


def app(input_path, output_path):
    # Initialize items
    items: deque[:SubRipItem] = deque()

    with codecs.open(input_path, encoding='utf-8') as f:
        for o in SubRipFile.stream(f):
            o.text = o.text.replace('\n', ' ') + ' '
            o.length = len(o.text)
            items.append(o)

    # Initialize text
    text = ''.join(o.text for o in items)

    # Initialize all sentences
    spans = nltk.data.load('tokenizers/punkt/english.pickle').span_tokenize(text)
    sentences = [dict(sp=s[0], ep=s[1], text=text[s[0]: s[1]]) for s in spans]

    # Initialize parameter for scan
    item = items.popleft()
    start_pos, step, start_time = 0, item.length, item.start

    # Scan and reset
    for sentence in sentences:
        while not start_pos <= sentence['ep'] <= (start_pos + step):
            start_pos += item.length
            item = items.popleft()
            step = item.length
        else:
            time_span = int(calculate((sentence['ep'] - start_pos + 1), step, (item.duration.ordinal / 1000.0)))

            # Update time of sentence
            sentence['st'] = start_time
            sentence['et'] = item.start + time_span

            # Update lp
            start_time = sentence['et']

    # Merge short sentence to previous
    done = []
    for cur in sentences:
        if len(cur['text']) > 16:
            done.append(cur)
        else:
            prev: dict = done.pop()
            new_text = ' '.join([prev['text'], cur['text']])
            prev['ep'], prev['et'], prev['text'] = cur['ep'], cur['et'], new_text
            done.append(prev)

    return done


if __name__ == '__main__':
    app(r"e:\demo.vtt", r"e:\output.vtt")

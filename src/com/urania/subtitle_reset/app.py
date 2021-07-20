# -*- coding: utf-8 -*-

# This is an english subtitle reset application based on the integrity of sentence.
# It returns a generator that provides convenience for calling the translation API next.
# The text reset work depends on ntlk.
# Each duration will be reset by a algorithm according to the proportion of characters.

# An intuitive example:

#   00:00:03.689 --> 00:00:08.570
#   Hey programmers, I'm Alvin l come to our course
#   on dynamic programming. So dynamic programming
#
#   00:00:08.570 --> 00:00:10.436
#   is one of my most favorite topics to teach.

# will be refactoring to:

#   00:00:03.689 --> 00:00:07.388
#   Hey programmers, I'm Alvin l come to our course on dynamic programming.
#
#   00:00:07.388 --> 00:00:10.436
#   So dynamic programming is one of my most favorite topics to teach.

from collections import deque
import datetime
import codecs
import pysrt
import nltk


class Util:
    @staticmethod
    def to_datetime(t):
        if not isinstance(t, pysrt.SubRipTime):
            raise TypeError("t must be a pysrt.SubRipTime instance")

        return datetime.datetime.combine(date=datetime.date.fromordinal(1), time=t.to_time())

    @staticmethod
    def to_timedelta(t):
        if not isinstance(t, pysrt.SubRipTime):
            raise TypeError("t must be a pysrt.SubRipTime instance")

        return datetime.timedelta(hours=t.hours, minutes=t.minutes, seconds=t.seconds, milliseconds=t.milliseconds)


def app(path):
    with codecs.open(path, encoding='utf-8') as file:
        source = deque(dict(
            start_time=Util.to_datetime(sub.start),
            total_seconds=Util.to_timedelta(sub.duration).total_seconds(),
            text=sub.text.replace('\n', ' ') + ' '
        ) for sub in pysrt.stream(file))

    text = ''.join([item['text'] for item in source])

    # Load tokenizer
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    # Tokenize
    sentences = deque(tokenizer.sentences_from_text(text))

    # Set all indexes of end character as objs
    objs = [tup[1] for tup in tokenizer.span_tokenize(text)]

    # Initialize parameter for scan
    item: dict = source.popleft()
    start = 0
    step = len(item['text'])
    lp = item['start_time']

    # Scan and reset
    for obj in objs:
        while not start <= obj <= (start + step):
            start += step
            item = source.popleft()
            step = len(item['text'])
        else:
            # Set the combination of (item.start) and (new total_seconds) as rp:right pointer
            rp = item['start_time'] + datetime.timedelta(seconds=((obj - start + 1) / step) * item['total_seconds'])

            # Append new item
            yield ''.join([str(lp)[11:23], ' --> ', str(rp)[11:23]]), sentences.popleft()

            # Update lp of duration
            lp = rp


if __name__ == '__main__':
    app(r"e:\youtube\demo.vtt")

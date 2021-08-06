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
    def to_datetime(t: pysrt.SubRipTime) -> datetime.datetime:
        return datetime.datetime.combine(date=datetime.date.fromordinal(1), time=t.to_time())

    @staticmethod
    def to_timedelta(t: pysrt.SubRipTime) -> datetime.timedelta:
        return datetime.timedelta(hours=t.hours, minutes=t.minutes, seconds=t.seconds, milliseconds=t.milliseconds)

    @staticmethod
    def scaling_transformation(x1: float, y1: float, y2: float) -> float:
        return (x1 / y1) * y2


class Node:
    __slots__ = "start_time", "seconds", "text", "length", "__weakref__"

    def __init__(self, _start_time, _total_seconds, _text):
        self.start_time = Util.to_datetime(_start_time)
        self.seconds = Util.to_timedelta(_total_seconds).total_seconds()
        self.text: str = _text.replace('\n', ' ') + ' '
        self.length: int = len(self.text)


def app(path):
    with codecs.open(path, encoding='utf-8') as f:
        chain: deque[:Node] = deque(Node(p.start, p.duration, p.text) for p in pysrt.stream(f))
    text = ''.join([item.text for item in chain])

    # Load tokenizer
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    # Tokenize
    sentences = deque(tokenizer.sentences_from_text(text))

    # Set all indexes of end character as objs
    objs = [tup[1] for tup in tokenizer.span_tokenize(text)]

    # Initialize parameter for scan
    node = chain.popleft()
    start, step, lp = 0, node.length, node.start_time

    # Scan and reset
    dst = deque([])
    for obj in objs:
        while not start <= obj <= (start + step):
            start += step
            node = chain.popleft()
            step = node.length
        else:
            # seconds of last sentence in item
            seconds_in_item = Util.scaling_transformation(
                x1=(obj - start + 1),  # index of the last char
                y1=step,  # total chars of item
                y2=node.seconds,  # total seconds
            )

            # Combine the result for true end time
            rp = datetime.timedelta(seconds=seconds_in_item) + node.start_time

            # Append new item
            dst.append((lp, rp, sentences.popleft()))

            # Update lp of duration
            lp = rp

    # Merge short sentence to previous
    done = deque([])

    for tup in dst:
        if len(tup[2]) > 16:
            done.append(tup)
        else:
            previous: tuple = done.pop()
            done.append((previous[0], tup[1], ' '.join([previous[2], tup[2]])))

    return done


if __name__ == '__main__':
    # ds = filter(lambda x: len(x[2]) > 180, app(r"e:\Youtube\Dynamic Programming.en.2.vtt"))
    dst = app(r"e:\Youtube\Dynamic Programming.en.2.vtt")

    print(*dst, sep='\n')

    # join string
    # HEADER = 'WEBVTT\nKind: captions\nLanguage: en'
    # SEP = ' --> '
    # SENTINEL = -1
    # dst.append(SENTINEL)
    # dst.append(HEADER)
    # while dst[0] != SENTINEL:
    #     item = dst.popleft()
    #     dst.append('\n'.join(
    #         [''.join([item[0], SEP, item[1]]), item[2]]
    #     ))
    # else:
    #     dst.popleft()
    #
    # buffer = '\n\n'.join(dst)
    #
    # with open(r"e:\Youtube\out.vtt", 'w') as f:
    #     f.writelines(buffer)

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
        """
        return x2 according to x1/y1 = x2/y2
        """
        return (x1 / y1) * y2


class Part:
    def __init__(self, _start_time, _total_seconds, _text):
        self.start_time = Util.to_datetime(_start_time)
        self.seconds = Util.to_timedelta(_total_seconds).total_seconds()
        self.text: str = _text.replace('\n', ' ') + ' '
        self.length: int = len(self.text)


def app(path):
    with codecs.open(path, encoding='utf-8') as f:
        all_parts: deque[:Part] = deque(Part(p.start, p.duration, p.text) for p in pysrt.stream(f))

    text = ''.join(p.text for p in all_parts)

    # Initialize all sentences
    sentences = [dict(start_pos=span[0], end_pos=span[1], text=text[span[0]: span[1]])
                 for span in nltk.data.load('tokenizers/punkt/english.pickle').span_tokenize(text)]

    # Initialize parameter for scan
    part = all_parts.popleft()
    start, step, lp = 0, part.length, part.start_time

    # Scan and reset
    for sentence in sentences:
        while not start <= sentence['end_pos'] <= (start + step):
            start += step
            part = all_parts.popleft()
            step = part.length
        else:
            # Update time of sentence
            sentence['start_time'] = lp
            sentence['end_time'] = part.start_time + datetime.timedelta(
                seconds=Util.scaling_transformation(x1=(sentence['end_pos'] - start + 1), y1=step, y2=part.seconds))

            # Update lp of duration
            lp = sentence['end_time']

    # Merge short sentence to previous
    done = []

    for cur in sentences:
        if len(cur['text']) > 16:
            done.append(cur)
        else:
            prev: dict = done.pop()
            new_text = ' '.join([prev['text'], cur['text']])
            prev['end_pos'], prev['end_time'], prev['text'] = cur['end_pos'], cur['end_time'], new_text
            done.append(prev)

    return done


if __name__ == '__main__':
    t1 = datetime.datetime.now()
    dst = [((str(v['start_time'])[11:23]), (str(v['end_time'])[11:23]), v['text'])
           for v in app(r"e:\Youtube\Dynamic Programming.en.1.vtt")]
    t2 = datetime.datetime.now()
    print(*dst, sep='\n')

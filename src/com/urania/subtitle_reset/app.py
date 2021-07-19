# -*- coding: utf-8 -*-

# This is a english subtitle reset application based on the integrity of sentence.
# It can output the reset text on the console that provides convenience for calling the translation API next.
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

import datetime
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
    # Load srt
    srt: list[: pysrt.SubRipItem] = pysrt.open(path=path)

    # Load tokenizer
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    # Prepare to tokenize.
    # It's necessary to replace but will cause one more space than each original paragraph
    all_plain_text = srt.text.replace("\n", " ")

    # Tokenize
    text_lst: list = tokenizer.tokenize(all_plain_text)

    # Align to all_plain_text
    for item in srt:
        item.text = item.text + " "

    # Set all indexes of end character as objs
    objs: list[: int] = [tup[1] for tup in tokenizer.span_tokenize(all_plain_text)]

    # Set start of duration as lp:left pointer
    lp = Util.to_datetime(srt[0].start)

    # Initialize scanned area
    start = 0
    iter_srt: iter = iter(srt)
    item: pysrt.SubRipItem = next(iter_srt)
    step = len(item.text)

    # Initialize buffer
    string_buffer = ""

    # Scan and reset
    for obj in objs:
        while not start <= obj <= (start + step):
            start += step
            item: pysrt.SubRipItem = next(iter_srt)
            step = len(item.text)
        else:
            # Set the combination of (item.start) and (new duration) as rp:right pointer
            rp = Util.to_datetime(item.start) + datetime.timedelta(seconds=((obj - start + 1) / step) * Util.to_timedelta(item.duration).total_seconds())

            # Update buffer
            string_buffer += ''.join([str(lp)[11:23], ' ', item.TIMESTAMP_SEPARATOR, ' ', str(rp)[11:23], '\n' + text_lst.pop(0) + '\n\n'])

            # Update lp of duration
            lp = rp

    # Output
    print(string_buffer)


if __name__ == '__main__':
    app(r"e:\youtube\demo.vtt")

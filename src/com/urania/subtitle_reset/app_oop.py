# -*- coding: utf-8 -*-
"""
Reorganize subtitle based on the integrity of sentence and align timeline.

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
from itertools import accumulate
from collections import deque
import codecs
import time

from pysrt import SubRipFile
import nltk


class Item:
    def __init__(self, start, end, text):
        self.start, self.end, self.text = start, end, text

    @property
    def milliseconds(self):
        return (self.end - self.start).ordinal

    @property
    def length(self):
        return len(self.text)


class ItemDeque(deque):

    def load_items(self, path):
        with codecs.open(path, 'r', encoding='utf-8') as f:
            for o in SubRipFile.stream(f):
                self.append(Item(o.start, o.end, o.text.replace('\n', ' ') + ' '))

    @property
    def text(self):
        return ''.join(o.text for o in self)

    @property
    def all_spans(self) -> list[:tuple]:
        lengths = list(accumulate([item.length for item in self], lambda x, y: x + y))
        return zip([0] + lengths[0:-1], [length - 1 for length in lengths])

    @property
    def all_spans_based_on_sentence_integrity(self):
        return nltk.data.load('tokenizers/punkt/english.pickle').span_tokenize(self.text)

    def reorganize_based_on_sentence_integrity(self):
        text = ''.join(o.text for o in self)
        old_spans = self.all_spans
        new_spans = self.all_spans_based_on_sentence_integrity
        item, (left, right) = self.popleft(), next(old_spans)
        start = item.start
        for start_position, end_position in new_spans:
            while not left <= end_position <= right:
                left, right = next(old_spans)
                item = self.popleft()
            else:
                end = item.start + int((end_position - left + 1) / (right - left + 1) * item.milliseconds)
                self.append(Item(start, end, text[start_position: end_position]))
                start = end

    def output(self, path, header, template):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(header)
            f.writelines([template.format(item.start, item.end, item.text) for item in self])

    def print_all(self):
        print(''.join(["{}  {}  {}\t  {}\n".format(item.start, item.end, item.length, item.text) for item in self]))

    def print_one(self, index):
        item = self[index]
        print("{}  {}  {}\t  {}".format(item.start, item.end, item.length, item.text))


def app():
    input_path = r"e:\Youtube\Dynamic Programming.en.1.vtt"
    output_path = r"e:\output2.vtt"
    header = "WEBVTT\nKind: captions\nLanguage: en\n\n"
    template = "{} --> {}\n{}\n\n"

    t1 = time.time()
    dq = ItemDeque()
    dq.load_items(input_path)
    dq.reorganize_based_on_sentence_integrity()
    t2 = time.time()
    dq.output(output_path, header, template)
    print('程序运行时间:%s毫秒' % ((t2 - t1) * 1000))


if __name__ == '__main__':
    app()

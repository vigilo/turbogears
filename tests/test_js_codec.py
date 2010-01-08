# -*- coding: utf-8 -*-
import unittest

import vigilo.turbogears.js_codec

class JsCodecEncodeTest(unittest.TestCase):
    def test_encode_single_quotes(self):
        res = "I'm, you're, and so on.".encode('backslash')
        self.assertEquals("I\\'m, you\\'re, and so on.", res)

    def test_encode_double_quotes(self):
        res = 'And then he said "hi !".'.encode('backslash')
        self.assertEquals('And then he said \\"hi !\\".', res)

    def test_encode_backslashes(self):
        res = "\\o/".encode('backslash')
        self.assertEquals("\\\\o/", res)

class JsCodecDecodeTest(unittest.TestCase):
    def test_decode_single_quotes(self):
        res = "I\\'m, you\\'re, and so on.".decode('backslash')
        self.assertEquals("I'm, you're, and so on.", res)

    def test_decode_double_quotes(self):
        res = 'And then he said \\"hi !\\".'.decode('backslash')
        self.assertEquals('And then he said "hi !".', res)

    def test_decode_backslashes(self):
        res = "\\\\o/".decode('backslash')
        self.assertEquals("\\o/", res)


# -*- coding: utf-8 -*-
"""
Teste l'échappement de chaînes de caractères en vue
de leur utilisation dans du code JavaScript.
"""
import unittest

import vigilo.turbogears.js_codec

class JsCodecEncodeTest(unittest.TestCase):
    def test_encode_single_quotes(self):
        """Échappement des apostrophes."""
        res = "I'm, you're, and so on.".encode('backslash')
        self.assertEquals("I\\'m, you\\'re, and so on.", res)

    def test_encode_double_quotes(self):
        """Échappement des guillemets."""
        res = 'And then he said "hi !".'.encode('backslash')
        self.assertEquals('And then he said \\"hi !\\".', res)

    def test_encode_backslashes(self):
        """Échappement des backslashes."""
        res = "\\o/".encode('backslash')
        self.assertEquals("\\\\o/", res)

class JsCodecDecodeTest(unittest.TestCase):
    def test_decode_single_quotes(self):
        """Suppression de l'échappement sur les apostrophes."""
        res = "I\\'m, you\\'re, and so on.".decode('backslash')
        self.assertEquals("I'm, you're, and so on.", res)

    def test_decode_double_quotes(self):
        """Suppression de l'échappement sur les guillemets."""
        res = 'And then he said \\"hi !\\".'.decode('backslash')
        self.assertEquals('And then he said "hi !".', res)

    def test_decode_backslashes(self):
        """Suppression de l'échappement sur les backslashes."""
        res = "\\\\o/".decode('backslash')
        self.assertEquals("\\o/", res)


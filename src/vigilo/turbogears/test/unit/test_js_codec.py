# -*- coding: utf-8 -*-
# Copyright (C) 2006-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Teste l'échappement de chaînes de caractères en vue
de leur utilisation dans du code JavaScript.
"""
import unittest

import vigilo.turbogears.js_codec

class JsCodecEncodeTest(unittest.TestCase):
    """Teste l'échappement de textes pour JavaScript."""

    def test_encode_single_quotes(self):
        """Échappement des apostrophes."""
        res = "I'm, you're, and so on.".encode('backslash')
        self.assertEqual("I\\'m, you\\'re, and so on.", res)

    def test_encode_double_quotes(self):
        """Échappement des guillemets."""
        res = 'And then he said "hi !".'.encode('backslash')
        self.assertEqual('And then he said \\"hi !\\".', res)

    def test_encode_backslashes(self):
        """Échappement des backslashes."""
        res = "\\o/".encode('backslash')
        self.assertEqual("\\\\o/", res)

class JsCodecDecodeTest(unittest.TestCase):
    """Teste la suppression de l'échappement pour JavaScript."""

    def test_decode_single_quotes(self):
        """Suppression de l'échappement sur les apostrophes."""
        res = "I\\'m, you\\'re, and so on.".decode('backslash')
        self.assertEqual("I'm, you're, and so on.", res)

    def test_decode_double_quotes(self):
        """Suppression de l'échappement sur les guillemets."""
        res = 'And then he said \\"hi !\\".'.decode('backslash')
        self.assertEqual('And then he said "hi !".', res)

    def test_decode_backslashes(self):
        """Suppression de l'échappement sur les backslashes."""
        res = "\\\\o/".decode('backslash')
        self.assertEqual("\\o/", res)


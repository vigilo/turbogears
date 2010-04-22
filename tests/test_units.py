# -*- coding: utf-8 -*-
"""
Teste le module de gestion des (conversions d') unités.
"""
import unittest

from vigilo.turbogears.units import convert_with_unit

class TestUnitManager(unittest.TestCase):
    """Conversion utilisant les puissances d'une unité."""
 
    def test_small(self):
        value = 5
        result = convert_with_unit(value)
        assert(result == '5')

    def test_large(self):
        value = 12345.
        result = convert_with_unit(value)
        assert(result == '12.345k')

    def test_negative(self):
        value = -3
        result = convert_with_unit(value)
        assert(result == '-3')

    def test_verysmall(self):
        value = -0.0007
        result = convert_with_unit(value)
        assert(result == '-700µ')

    def test_fraction(self):
        value = 0.07
        result = convert_with_unit(value)
        assert(result == '70m')

    def test_round(self):
        value = 12345.
        result = convert_with_unit(value, 1)
        assert(result == '12.3k')


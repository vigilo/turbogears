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
        assert(result == '12.3k')

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

    def test_digits(self):
        value = 12345.
        result = convert_with_unit(value)
        assert(result == '12.3k')

    def test_digits2(self):
        value = 0.29
        result = convert_with_unit(value)
        assert(result == '290m')

    def test_digits3(self):
        value = 201186
        result = convert_with_unit(value)
        assert(result == '201k')

    def test_digits4(self):
        value = -201
        result = convert_with_unit(value)
        assert(result == '-201')

    def test_digits5(self):
        value = -4242.2
        result = convert_with_unit(value)
        assert(result == '-4.24k')

    def test_digits6(self):
        value = 4242.2
        result = convert_with_unit(value)
        assert(result == '4.24k')

    def test_digits7(self):
        value = 301686.572889
        result = convert_with_unit(value)
        assert(result == '301k')

    def test_digits8(self):
        value = -30168.572889
        result = convert_with_unit(value)
        assert(result == '-30.1k')

    def test_None(self):
        value = None
        result = convert_with_unit(value)
        assert(result is None)

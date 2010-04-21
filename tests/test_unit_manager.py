# -*- coding: utf-8 -*-
"""
Teste le module de gestion des (conversions d') unités.
"""
import unittest

from vigilo.turbogears.unit_manager import UnitManager

class TestUnitManager(unittest.TestCase):
    """Tests du gestionnaire d'unités."""  
 
    def test_convert_with_unit(self):
        """Conversion utilisant les puissances d'une unité."""
        unitmanager = UnitManager()
    
        value = 5
        result = unitmanager.convert_with_unit(value)
        assert(result == '5.0')

        value = 12345.
        result = unitmanager.convert_with_unit(value)
        assert(result == '12.345k')

        value = -0.07
        result = unitmanager.convert_with_unit(value)
        assert(result == '-7.0c')

    def test_convert_with_percent(self):
        """Conversion d'une valeur en pourcentage."""
        unitmanager = UnitManager()
        value = 60
        maxvalue = 100
        result = unitmanager.convert_to_percent(value, maxvalue)
        assert(result == '60%')


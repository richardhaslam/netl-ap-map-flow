"""
Handles testing of the unit conversion module
#
Written By: Matthew Stadelman
Date Written: 2016/06/09
Last Modifed: 2016/06/11
#
"""
import pytest
from ApertureMapModelTools import UnitConversion
from ApertureMapModelTools.UnitConversion.__converter_core__ import process_unit_list
from ApertureMapModelTools.UnitConversion.__ConversionClasses__ import Distance
from ApertureMapModelTools.UnitConversion.__SI__ import SI
from ApertureMapModelTools.UnitConversion.__UnitDecomposition__ import UnitDecomposition


class TestUnitConversion:
    r"""
    Executes a set of functions to handle testing of the unit conversion
    routines
    """
    def setup_class(self):
        # value, unit_in='kelvin', unit_out='kelvin'
        self.temperature_units = [
            (0.0, 'C', 'SI', 273.15),
            (273.15, 'kelvin', 'C', 0.0),
            (273.15, 'K', 'celsius', 0.0),
            (0.0, 'C', 'F', 32.0),
            (32.0, 'F', 'C', 0.0),
            (459.67, 'R', 'F', 0.0),
            (0.0, 'F', 'R', 459.67),
            (0.0, 'R', 'K', 0.0)
        ]
        #
        self.abbrev_units = [
            (1000.0, 'mm', 'SI', 1.0),
            (1000.0, 'millimeter', 'SI', 1.0),
            (1.0, 'kpa', 'SI', 1000.0),
            (1.0E9, 'ns', 'SI', 1.0),
            (12.0, 'in', 'ft', 1.0)
        ]
        #
        self.formatted_units = [
            (10.0, 'gpm', 'ml/second', 630.902),
            (1.0, 'psi', 'uN/mm^2', 6894.755905511812)
        ]
        #
        self.all_unit_test = [
            (0.0, 'C', 'F', 32.0),
            (459.67, 'R', 'F', 0.0),
            (1.0, 'psi', 'kN/m^2', 6.894755905511812),
            (1.0, 'lbf', 'N', 4.44822072),
            (1000.0, 'kilogram/meter^3', 'lbm/ft^3', 62.42795644724207),
            (1.0, 'cP', 'dyne*s/cm^2', 0.01),
            (10.0, 'P', 'pascal*second', 1.0),
            (1000.0, 'micron', 'SI', 0.001)
        ]
        #
        self._convertion_factor_test = [
            ('psi', 'kN/m^2', 6.894755905511812),
            ('lbf', 'N', 4.44822072),
            ('kilogram/meter^3', 'lbm/ft^3', 0.06242795644724206),
            ('cP', 'dyne*s/cm^2', 0.01),
            ('P', 'pascal*second', 0.1),
            ('kl/sec', 'SI', 1.0)
        ]

    def test_convert_temperature(self):
        r"""
        Testing values returned by temperature conversion
        """
        for val_in, unit_in, unit_out, val_out in self.temperature_units:
            val = UnitConversion.convert_value(val_in, unit_in, unit_out)
            #
            # applying a tolerance since were working with floating point values
            val = round(val * 1.0E9)
            val_out = round(val_out * 1.0E9)
            msg = 'Temperature conversion from '+unit_in+' to '+unit_out+' failed.'
            #
            assert val == val_out, msg

    def test_convert_abbrev_units(self):
        r"""
        Testing values returned when using common unit abbrevations
        """
        for val_in, unit_in, unit_out, val_out in self.abbrev_units:
            val = UnitConversion.convert_value(val_in, unit_in, unit_out)
            #
            # applying a tolerance since were working with floating point values
            val = round(val * 1.0E9)
            val_out = round(val_out * 1.0E9)
            msg = 'Abbreviated unit conversion from {} to {} failed.'
            msg = msg.format(unit_in, unit_out)
            #
            assert val == val_out, msg
        #

    def test_convert_formatted_units(self):
        r"""
        Testing values returned by formatted unit strings
        """
        for val_in, unit_in, unit_out, val_out in self.formatted_units:
            val = UnitConversion.convert_value(val_in, unit_in, unit_out)
            #
            # applying a tolerance since were working with floating point values
            val = round(val * 1.0E9)
            val_out = round(val_out * 1.0E9)
            msg = 'Formatted unit conversion from {} to {} failed.'
            msg = msg.format(unit_in, unit_out)
            #
            assert val == val_out, msg
        #
        # manually sending a formatted unit list with a prefix
        unit_list = UnitDecomposition.build_unit_list('[millimeter^1]')
        factor = process_unit_list(unit_list)
        assert factor == 0.001

    def test_convert_all_units(self):
        r"""
        Testing values returned bya general test of many conversions
        """
        for val_in, unit_in, unit_out, val_out in self.all_unit_test:
            val = UnitConversion.convert_value(val_in, unit_in, unit_out)
            #
            # applying a tolerance since were working with floating point values
            val = round(val * 1.0E9)
            val_out = round(val_out * 1.0E9)
            msg = 'Mutlitple unit conversion from {} to {} failed.'
            msg = msg.format(unit_in, unit_out)
            #
            assert val == val_out, msg

    def test_get_conversion_factor(self):
        r"""
        Testing the get_conversion_factor function
        """
        for unit_in, unit_out, test_fact in self._convertion_factor_test:
            fact = UnitConversion.get_conversion_factor(unit_in, unit_out)
            fact = round(fact * 1.0E9)
            test_fact = round(test_fact * 1.0E9)
            msg = 'Get conversion factor for {} to {} failed.'
            msg = msg.format(unit_in, unit_out)
            #
            assert fact == test_fact, msg

    def test_conversion_errors(self):
        r"""
        Sends invalid unit strings to various functions
        """
        #
        root_unit, prefix = SI.check_abbreviation('badunit')
        assert(root_unit == 'badunit')
        assert(prefix == '')
        #
        with pytest.raises(ValueError):
            SI.convert_to_si('badunit')
        #
        with pytest.raises(Exception):
            UnitDecomposition.parse_unit_string('celsius')
        #
        with pytest.raises(KeyError):
            UnitDecomposition.parse_unit_string('badunit')
        #
        with pytest.raises(AttributeError):
            UnitDecomposition.build_unit_list('[pascal_1]')
        #
        with pytest.raises(ValueError):
            UnitDecomposition.build_unit_list('[millipascal^1]')
        #
        with pytest.raises(KeyError):
            UnitDecomposition.build_unit_list('[badunit^1]')
        #
        with pytest.raises(ValueError):
            UnitConversion.convert_temperature(0.0, 'badunit', 'SI')
        #
        with pytest.raises(ValueError):
            UnitConversion.convert_temperature(0.0, 'SI', 'badunit')
        #
        with pytest.raises(ValueError):
            Distance.convert_to_si('badunit')
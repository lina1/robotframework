import unittest

from robot.variables import VariableSplitter
from robot.utils.asserts import assert_equals


class TestVariableSplitter(unittest.TestCase):

    _identifiers = ['$','@','%','&','*']

    def test_empty(self):
        self._test('', None)

    def test_no_vars(self):
        for inp in ['hello world', '$hello', '{hello}', '$\\{hello}',
                    '${hello', '$hello}' ]:
            self._test(inp, None)

    def test_backslashes(self):
        for inp in ['\\', '\\\\', '\\\\\\\\\\',
                    '\\hello\\\\world\\\\\\']:
            self._test(inp, None)

    def test_one_var(self):
        self._test('${hello}', '${hello}', 0)
        self._test('1 @{hello} more', '@{hello}', 2)
        self._test('*{hi}}', '*{hi}', 0)
        self._test('{%{{hi}}', '%{{hi}', 1)
        self._test('-= ${} =-', '${}', 3)
        # In this case splitter thinks there are internal but there aren't.
        # Better check would probably spent more time than that is saved when
        # variable base is processed again in this special case.
        self._test('%{hi%{u}', '%{hi%{u}', 0, internal=True)

    def test_multiple_vars(self):
        self._test('${hello} ${world}', '${hello}', 0)
        self._test('hi %{u}2 and @{u2} and also *{us3}', '%{u}', 3)
        self._test('0123456789 %{1} and @{2', '%{1}', 11)

    def test_escaped_var(self):
        self._test('\\${hello}', None)
        self._test('hi \\\\\\${hello} moi', None)

    def test_not_escaped_var(self):
        self._test('\\\\${hello}', '${hello}', 2)
        self._test('\\hi \\\\\\\\\\\\${hello} moi', '${hello}',
                   len('\\hi \\\\\\\\\\\\'))
        self._test('\\ ${hello}', '${hello}', 2)
        self._test('${hello}\\', '${hello}', 0)
        self._test('\\ \\ ${hel\\lo}\\', '${hel\\lo}', 4)

    def test_escaped_and_not_escaped_vars(self):
        for inp, var, start in [
                ('\\${esc} ${not}', '${not}', len('\\${esc} ')),
                ('\\\\\\${esc} \\\\${not}', '${not}',
                 len('\\\\\\${esc} \\\\')),
                ('\\${esc}\\\\${not}${n2}', '${not}', len('\\${esc}\\\\')) ]:
            self._test(inp, var, start)

    def test_internal_vars(self):
        for inp, var, start in [
                ('${hello${hi}}', '${hello${hi}}', 0),
                ('bef ${${hi}hello} aft', '${${hi}hello}', 4),
                ('\\${not} ${hel${hi}lo} ', '${hel${hi}lo}', len('\\${not} ')),
                ('${${hi}${hi}}\\', '${${hi}${hi}}', 0),
                ('${${hi${hi}}} ${xx}', '${${hi${hi}}}', 0),
                ('${xx} ${${hi${hi}}}', '${xx}', 0),
                ('${\\${hi${hi}}}', '${\\${hi${hi}}}', 0),
                ('\\${${hi${hi}}}', '${hi${hi}}', len('\\${')),
                ('\\${\\${hi\\\\${hi}}}', '${hi}', len('\\${\\${hi\\\\')) ]:
            internal = var.count('{') > 1
            self._test(inp, var, start, internal=internal)

    def test_index(self):
        self._test('@{x}[0]', '@{x}', 0, '0')
        self._test('.@{x}[42]..', '@{x}', 1, '42')
        self._test('@{x}[${i}] ${xyz}', '@{x}', 0, '${i}')
        self._test('@{x}[]', '@{x}', 0, '')
        self._test('@{x}[inv]', '@{x}', 0, 'inv')
        self._test('@{x}[0', '@{x}', 0, None)
        self._test('@{x}}[0]', '@{x}', 0, None)
        self._test('${x}[0]', '${x}', 0, None)
        self._test('%{x}[0]', '%{x}', 0, None)
        self._test('*{x}[0]', '*{x}', 0, None)
        self._test('&{x}[0]', '&{x}', 0, None)

    def test_custom_identifiers(self):
        for inp, start in [ ('@{x}${y}', 4),
                            ('%{x} ${y}', 5),
                            ('*{x}567890${y}', 10),
                            ('&{x}%{x}@{x}\\${x}${y}',
                             len('&{x}%{x}@{x}\\${x}')) ]:
            self._test(inp, '${y}', start, identifiers=['$'])

    def test_identifier_as_variable_name(self):
        for i in self._identifiers:
            for count in 1,2,3,42:
                var = '%s{%s}' % (i, i*count)
                self._test(var, var)
                self._test(var+'spam', var)
                self._test('eggs'+var+'spam', var, start=4)
                self._test(i+var+i, var, start=1)

    def test_identifier_as_variable_name_with_internal_vars(self):
        for i in self._identifiers:
            for count in 1,2,3,42:
                var = '%s{%s{%s}}' % (i, i*count, i)
                self._test(var, var, internal=True)
                self._test('eggs'+var+'spam', var, start=4, internal=True)
                var = '%s{%s{%s}}' % (i, i*count, i*count)
                self._test(var, var, internal=True)
                self._test('eggs'+var+'spam', var, start=4, internal=True)

    def _test(self, inp, variable, start=0, index=None, identifiers=None,
              internal=False):
        if variable is not None:
            identifier = variable[0]
            base = variable[2:-1]
            end = start + len(variable)
            if index is not None:
                end += len(index) + 2
        else:
            identifier = base = None
            start = end = -1
        if not identifiers:
            identifiers = self._identifiers
        res = VariableSplitter(inp, identifiers)
        assert_equals(res.base, base, "'%s' base" % inp)
        assert_equals(res.start, start, "'%s' start" % inp)
        assert_equals(res.end, end, "'%s' end" % inp)
        assert_equals(res.identifier, identifier, "'%s' indentifier" % inp)
        assert_equals(res.index, index, "'%s' index" % inp)
        assert_equals(res._may_have_internal_variables, internal,
                      "'%s' internal" % inp)


if __name__ == '__main__':
    unittest.main()
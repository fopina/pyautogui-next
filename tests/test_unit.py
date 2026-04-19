from __future__ import division, print_function

import doctest
import random
import unittest

from test_common import GUI_TEST, install_headless_stubs

install_headless_stubs()

import pyautogui


class TestHelperFunctions(unittest.TestCase):
    def test__normalizeXYArgs(self):
        self.assertEqual(pyautogui._normalizeXYArgs(1, 2), pyautogui.Point(x=1, y=2))
        self.assertEqual(pyautogui._normalizeXYArgs((1, 2), None), pyautogui.Point(x=1, y=2))
        self.assertEqual(pyautogui._normalizeXYArgs([1, 2], None), pyautogui.Point(x=1, y=2))

    @GUI_TEST
    def test__normalizeXYArgs_image_lookup(self):
        pyautogui.useImageNotFoundException()
        with self.assertRaises(pyautogui.ImageNotFoundException):
            pyautogui._normalizeXYArgs('100x100blueimage.png', None)
        pyautogui.useImageNotFoundException(False)
        self.assertEqual(pyautogui._normalizeXYArgs('100x100blueimage.png', None), None)


class TestDoctests(unittest.TestCase):
    def test_doctests(self):
        doctest.testmod(pyautogui)


class TestRun(unittest.TestCase):
    def test_getNumberToken(self):
        self.assertEqual(pyautogui._getNumberToken('5hello'), '5')
        self.assertEqual(pyautogui._getNumberToken('-5hello'), '-5')
        self.assertEqual(pyautogui._getNumberToken('+5hello'), '+5')
        self.assertEqual(pyautogui._getNumberToken('5.5hello'), '5.5')
        self.assertEqual(pyautogui._getNumberToken('+5.5hello'), '+5.5')
        self.assertEqual(pyautogui._getNumberToken('-5.5hello'), '-5.5')
        self.assertEqual(pyautogui._getNumberToken('  5hello'), '  5')
        self.assertEqual(pyautogui._getNumberToken('  -5hello'), '  -5')
        self.assertEqual(pyautogui._getNumberToken('  +5hello'), '  +5')
        self.assertEqual(pyautogui._getNumberToken('  5.5hello'), '  5.5')
        self.assertEqual(pyautogui._getNumberToken('  +5.5hello'), '  +5.5')
        self.assertEqual(pyautogui._getNumberToken('  -5.5hello'), '  -5.5')

        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getNumberToken('')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getNumberToken('hello')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getNumberToken('    ')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getNumberToken('hello 42')

    def test_getQuotedStringToken(self):
        self.assertEqual(pyautogui._getQuotedStringToken("'hello'world"), "'hello'")
        self.assertEqual(pyautogui._getQuotedStringToken("''world"), "''")
        self.assertEqual(pyautogui._getQuotedStringToken("  'hello'world"), "  'hello'")

        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getQuotedStringToken('xyz')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getQuotedStringToken('xyz')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getQuotedStringToken('  xyz')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getQuotedStringToken("'xyz")
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getQuotedStringToken("xyz'")
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getQuotedStringToken('"xyz"')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getQuotedStringToken('')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getQuotedStringToken("xyz 'hello'")

    def test_getCommaToken(self):
        self.assertEqual(pyautogui._getCommaToken(','), ',')
        self.assertEqual(pyautogui._getCommaToken('  ,'), '  ,')

        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getCommaToken('')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getCommaToken('hello,')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getCommaToken('hello')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getCommaToken('    ')

    def test_getParensCommandStrToken(self):
        self.assertEqual(pyautogui._getParensCommandStrToken('()'), '()')
        self.assertEqual(pyautogui._getParensCommandStrToken('  ()'), '  ()')
        self.assertEqual(pyautogui._getParensCommandStrToken('()hello'), '()')
        self.assertEqual(pyautogui._getParensCommandStrToken('  ()hello'), '  ()')
        self.assertEqual(pyautogui._getParensCommandStrToken('(hello)world'), '(hello)')
        self.assertEqual(pyautogui._getParensCommandStrToken('  (hello)world'), '  (hello)')
        self.assertEqual(pyautogui._getParensCommandStrToken('(he(ll)(o))world'), '(he(ll)(o))')
        self.assertEqual(pyautogui._getParensCommandStrToken('  (he(ll)(o))world'), '  (he(ll)(o))')
        self.assertEqual(pyautogui._getParensCommandStrToken('(he(ll)(o)))world'), '(he(ll)(o))')
        self.assertEqual(pyautogui._getParensCommandStrToken('  (he(ll)(o)))world'), '  (he(ll)(o))')

        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getParensCommandStrToken('')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getParensCommandStrToken('  ')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getParensCommandStrToken('hello')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getParensCommandStrToken(' (')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getParensCommandStrToken('(he(ll)o')
        with self.assertRaises(pyautogui.PyAutoGUIException):
            pyautogui._getParensCommandStrToken('')

    def test_tokenizeCommandStr(self):
        self.assertEqual(pyautogui._tokenizeCommandStr(''), [])
        self.assertEqual(pyautogui._tokenizeCommandStr('  '), [])
        self.assertEqual(pyautogui._tokenizeCommandStr('c'), ['c'])
        self.assertEqual(pyautogui._tokenizeCommandStr('  c  '), ['c'])
        self.assertEqual(pyautogui._tokenizeCommandStr('ccc'), ['c', 'c', 'c'])
        self.assertEqual(pyautogui._tokenizeCommandStr('  c  c  c  '), ['c', 'c', 'c'])
        self.assertEqual(pyautogui._tokenizeCommandStr('clmr'), ['c', 'l', 'm', 'r'])
        self.assertEqual(pyautogui._tokenizeCommandStr('susdss'), ['su', 'sd', 'ss'])
        self.assertEqual(pyautogui._tokenizeCommandStr(' su sd ss '), ['su', 'sd', 'ss'])
        self.assertEqual(pyautogui._tokenizeCommandStr('clmrsusdss'), ['c', 'l', 'm', 'r', 'su', 'sd', 'ss'])

        random.seed(42)
        for _ in range(100):
            commands = []
            commands.extend(['c'] * random.randint(0, 9))
            commands.extend(['l'] * random.randint(0, 9))
            commands.extend(['m'] * random.randint(0, 9))
            commands.extend(['r'] * random.randint(0, 9))
            commands.extend(['su'] * random.randint(0, 9))
            commands.extend(['sd'] * random.randint(0, 9))
            commands.extend(['ss'] * random.randint(0, 9))
            random.shuffle(commands)
            command_str = []
            for command in commands:
                command_str.append(command)
                command_str.append(' ' * random.randint(0, 9))
            command_str = ''.join(command_str)
            self.assertEqual(pyautogui._tokenizeCommandStr(command_str), commands)

        self.assertEqual(pyautogui._tokenizeCommandStr('g10,10'), ['g', '10', '10'])
        self.assertEqual(pyautogui._tokenizeCommandStr('g 10,10'), ['g', '10', '10'])
        self.assertEqual(pyautogui._tokenizeCommandStr('g10 ,10'), ['g', '10', '10'])
        self.assertEqual(pyautogui._tokenizeCommandStr('g10, 10'), ['g', '10', '10'])
        self.assertEqual(pyautogui._tokenizeCommandStr(' g 10 , 10 '), ['g', '10', '10'])
        self.assertEqual(pyautogui._tokenizeCommandStr('  g  10  ,  10  '), ['g', '10', '10'])

        self.assertEqual(pyautogui._tokenizeCommandStr('g+10,+10'), ['g', '+10', '+10'])
        self.assertEqual(pyautogui._tokenizeCommandStr('g +10,+10'), ['g', '+10', '+10'])
        self.assertEqual(pyautogui._tokenizeCommandStr('g+10 ,+10'), ['g', '+10', '+10'])
        self.assertEqual(pyautogui._tokenizeCommandStr('g+10, +10'), ['g', '+10', '+10'])
        self.assertEqual(pyautogui._tokenizeCommandStr(' g +10 , +10 '), ['g', '+10', '+10'])
        self.assertEqual(pyautogui._tokenizeCommandStr('  g  +10  ,  +10  '), ['g', '+10', '+10'])

        self.assertEqual(pyautogui._tokenizeCommandStr('g-10,-10'), ['g', '-10', '-10'])
        self.assertEqual(pyautogui._tokenizeCommandStr('g -10,-10'), ['g', '-10', '-10'])
        self.assertEqual(pyautogui._tokenizeCommandStr('g-10 ,-10'), ['g', '-10', '-10'])
        self.assertEqual(pyautogui._tokenizeCommandStr('g-10, -10'), ['g', '-10', '-10'])
        self.assertEqual(pyautogui._tokenizeCommandStr(' g -10 , -10 '), ['g', '-10', '-10'])
        self.assertEqual(pyautogui._tokenizeCommandStr('  g  -10  ,  -10  '), ['g', '-10', '-10'])

        self.assertEqual(pyautogui._tokenizeCommandStr('d10,10'), ['d', '10', '10'])
        self.assertEqual(pyautogui._tokenizeCommandStr('d1,2g3,4'), ['d', '1', '2', 'g', '3', '4'])
        self.assertEqual(pyautogui._tokenizeCommandStr("w'hello'"), ['w', 'hello'])
        self.assertEqual(pyautogui._tokenizeCommandStr("d1,2w'hello'g3,4"), ['d', '1', '2', 'w', 'hello', 'g', '3', '4'])
        self.assertEqual(pyautogui._tokenizeCommandStr('s42'), ['s', '42'])
        self.assertEqual(pyautogui._tokenizeCommandStr('s42.3'), ['s', '42.3'])
        self.assertEqual(pyautogui._tokenizeCommandStr('f10(c)'), ['f', '10', ['c']])
        self.assertEqual(pyautogui._tokenizeCommandStr('f10(lmr)'), ['f', '10', ['l', 'm', 'r']])
        self.assertEqual(pyautogui._tokenizeCommandStr('f10(f5(cc))'), ['f', '10', ['f', '5', ['c', 'c']]])

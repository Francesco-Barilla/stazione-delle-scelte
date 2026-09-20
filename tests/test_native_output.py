import unittest
from engine import parse, generate, run, action, CodeError
from missions import BY_KEY, MISSIONS, validate


class NativeOutputTests(unittest.TestCase):
    def test_real_output_is_an_animated_message(self):
        sources = {'Python': 'print("ricarica")', 'JavaScript': 'console.log("ricarica");',
                   'C': 'printf("%s\\n", "ricarica");', 'Java': 'System.out.println("ricarica");'}
        for language, code in sources.items():
            with self.subTest(language=language):
                nodes = parse(code, language)
                self.assertEqual(run(nodes, {}, language)[-1].actions, ('ricarica',))
                self.assertEqual(generate([action('ricarica')], language).strip(), code)

    def test_fake_function_and_wrong_printf_signature_are_rejected(self):
        for code, language in [('ricarica()', 'Python'), ('ricarica();', 'C'),
                               ('printf("%d\\n", "ricarica");', 'C'),
                               ('printf("%s\\n");', 'C'), ('print("ricarica");', 'Java')]:
            with self.subTest(code=code), self.assertRaises(CodeError):
                parse(code, language)

    def test_portello_rejects_adjacent_string_literals_in_java_and_javascript(self):
        sources = {
            'JavaScript': 'if (badge) { console.log("ap" "ri"); } else { console.log("nega"); }',
            'Java': 'if (badge) { System.out.println("ap" "ri"); } else { System.out.println("nega"); }',
        }
        for language, code in sources.items():
            with self.subTest(language=language), self.assertRaisesRegex(CodeError, 'virgolette'):
                validate(BY_KEY['portello'], code, language)

    def test_portello_rejects_python_only_hex_escape_in_java(self):
        code = r'if (badge) { System.out.println("\x61pri"); } else { System.out.println("nega"); }'
        with self.assertRaisesRegex(CodeError, 'virgolette'):
            validate(BY_KEY['portello'], code, 'Java')

    def test_missions_generate_only_standard_printing(self):
        for m in MISSIONS:
            for lang in ('Python', 'JavaScript', 'C', 'Java'):
                code = m.solution(lang)
                self.assertNotRegex(code, r'\b(?:ricarica|apri|parti|nega)\(\)')
                self.assertTrue(parse(code, lang))


if __name__ == '__main__':
    unittest.main()

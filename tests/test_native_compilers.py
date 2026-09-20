"""Run only trusted authored examples through actual language runtimes."""
import shutil
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from lessons import QUIZZES
from missions import MISSIONS
from native_context import input_fields, input_block, wrap_program


class NativeCompilerTests(unittest.TestCase):
    def test_authored_cases_use_real_input_and_output(self):
        for language in ('Python', 'JavaScript', 'C', 'Java'):
            with self.subTest(language=language), tempfile.TemporaryDirectory() as directory:
                snippets, inputs, expected = [], [], []
                authored = [(m.solution(language), case.data, m.rule(case.data)) for m in MISSIONS for case in m.cases]
                # Quiz outputs are an independent authored oracle, not engine execution.
                quiz_outputs = [(), ('ricarica',), ('ricarica',), ('ricarica', 'controlla'), ('ricarica',), ('corsia_rapida',), ('apri',),
                                ('allarme',), ('carica',), ('nega',), (), ('nega', 'registra'), ('attendi',), ('attendi',), ('nega',),
                                ('ricarica',), ('registra',), ('registra',), ('attendi',), ('attendi',)]
                authored += [(q.source(language), q.case.data, output) for q, output in zip(QUIZZES, quiz_outputs)]
                for code, data, output in authored:
                    snippet = input_block(code, language) + '\n' + code
                    snippets.append(snippet if language == 'Python' else '{\n' + snippet + '\n}')
                    inputs.extend(str(int(data[name])) for name in input_fields(code))
                    expected.extend(output)
                root = Path(directory)
                body = '\n'.join(snippets)
                program = wrap_program(body, language)
                if language == 'C':
                    compiler = shutil.which('gcc')
                    if not compiler:
                        self.skipTest('GCC unavailable')
                    path = root / 'main.c'
                    path.write_text(program, encoding='utf-8')
                    compiled = subprocess.run([compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', str(path), '-o', str(root/'main.exe')], capture_output=True, text=True, timeout=30)
                    self.assertEqual(compiled.returncode, 0, compiled.stderr)
                    command = [str(root/'main.exe')]
                elif language == 'Java':
                    compiler, runtime = shutil.which('javac'), shutil.which('java')
                    if not compiler or not runtime:
                        self.skipTest('Java unavailable')
                    path = root/'Main.java'
                    path.write_text(program, encoding='utf-8')
                    compiled = subprocess.run([compiler, '-encoding', 'UTF-8', str(path)], capture_output=True, text=True, timeout=30)
                    self.assertEqual(compiled.returncode, 0, compiled.stderr)
                    command = [runtime, '-cp', str(root), 'Main']
                elif language == 'JavaScript':
                    runtime = shutil.which('node')
                    if not runtime:
                        self.skipTest('Node unavailable')
                    import json
                    path = root/'main.js'
                    path.write_text('const queue = '+json.dumps(inputs)+';\nconst prompt = () => queue.shift();\n'+program, encoding='utf-8')
                    command = [runtime, str(path)]
                else:
                    path = root/'main.py'
                    path.write_text(program, encoding='utf-8')
                    command = [sys.executable, str(path)]
                result = subprocess.run(command, input='\n'.join(inputs)+'\n', capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(), expected)


if __name__ == '__main__':
    unittest.main()

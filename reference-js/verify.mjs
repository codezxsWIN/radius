import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { canonical, fromText, parse } from './reference.mjs';

const manifest = JSON.parse(readFileSync(new URL('../conformance/manifest.json', import.meta.url), 'utf8'));
let passed = 0;
for (const entry of manifest.fixtures) {
  const fixtureText = readFileSync(new URL('../conformance/' + entry.file, import.meta.url), 'utf8');
  const fixture = parse(fixtureText);
  for (const model of manifest.required_models) {
    const request = canonical({ contract_version: '1.0-draft', input: fixture.input, parameters: { constraint_model: model, step_bound: fixture.step_bound, threshold: '1/4' } });
    const observed = fromText(request);
    assert.deepEqual(JSON.parse(canonical(observed)), JSON.parse(canonical(fixture.expected[model])), fixture.id + ':' + model);
    assert.equal(canonical(fromText(request)), canonical(observed));
    passed++;
  }
}
assert.equal(fromText('{"contract_version":"future"}').error, 'UNSUPPORTED_CONTRACT');
assert.equal(fromText('invalid-json').error, 'INVALID_GRAPH_OR_PARAMETERS');
assert.equal(canonical(parse('{"float":1.0,"integer":1,"unicode":"\u00e9"}')), '{"float":1.0,"integer":1,"unicode":"\\u00e9"}');
assert.throws(() => parse('{"same":1,"same":2}'));
assert.throws(() => parse('{"\\u0061":1,"a":2}'));
assert.throws(() => parse('0.10000000000000001'));
assert.equal(canonical(parse('9007199254740993')), '9007199254740993');
assert.equal(canonical(parse('1' + '0'.repeat(400))), '1' + '0'.repeat(400));
assert.equal(canonical(parse('{"a":{"same":1},"b":{"same":2},"text":"{\\\"same\\\":3}"}')), '{"a":{"same":1},"b":{"same":2},"text":"{\\\"same\\\":3}"}');
console.log(JSON.stringify({ language: 'JavaScript', passed, cases: manifest.fixtures.length * manifest.required_models.length }));
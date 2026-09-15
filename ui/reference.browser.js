(function(){
const PROFILE = '1.0-draft';
const MODELS = ['default', 'strict', 'session-theft-aware'];
const schema = {"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:blastradius:prototype:graph:0.1","title":"Blast Radius v0.1 synthetic graph","type":"object","additionalProperties":false,"required":["schema_version","synthetic","organization","observed_at","action_weights","nodes","edges","coverage"],"properties":{"schema_version":{"const":"0.1"},"synthetic":{"const":true},"organization":{"type":"string","pattern":"^Fictional ","maxLength":160},"observed_at":{"type":"string","format":"date-time"},"action_weights":{"type":"object","minProperties":1,"propertyNames":{"enum":["read","write","administer","read_metadata","read_secret"]},"additionalProperties":{"type":"integer","minimum":1}},"nodes":{"type":"array","items":{"$ref":"#/$defs/node"}},"edges":{"type":"array","items":{"$ref":"#/$defs/edge"}},"coverage":{"type":"array","items":{"type":"string","maxLength":500}}},"$defs":{"id":{"type":"string","pattern":"^[A-Za-z0-9][A-Za-z0-9:._/-]{0,255}$"},"ids":{"type":"array","uniqueItems":true,"items":{"$ref":"#/$defs/id"}},"provenance":{"type":"object","additionalProperties":false,"required":["connector","source_api","observed_at","evidence_ref"],"properties":{"connector":{"type":"string"},"source_api":{"type":"string"},"observed_at":{"type":"string","format":"date-time"},"evidence_ref":{"type":"string"}}},"node":{"type":"object","additionalProperties":false,"required":["id","kind","subtype","name","provenance"],"properties":{"id":{"$ref":"#/$defs/id"},"kind":{"enum":["principal","credential","binding","resource","constraint"]},"subtype":{"type":"string"},"name":{"type":"string","maxLength":160},"provenance":{"$ref":"#/$defs/provenance"},"principal_id":{"$ref":"#/$defs/id"},"actions":{"$ref":"#/$defs/ids"},"session_satisfied_constraints":{"type":"array","uniqueItems":true,"items":{"enum":["device_required"]}},"sensitivity":{"type":"number","minimum":0,"maximum":1},"effect":{"enum":["allow","deny"]},"constraints":{"$ref":"#/$defs/ids"},"eligible":{"type":"boolean"},"provisioned_at":{"type":["string","null"],"format":"date-time"}},"allOf":[{"if":{"properties":{"kind":{"const":"principal"}}},"then":{"properties":{"subtype":{"enum":["human_user","service_principal","managed_identity","workload_identity","ai_agent","group"]}}}},{"if":{"properties":{"kind":{"const":"credential"}}},"then":{"required":["principal_id"],"properties":{"subtype":{"enum":["password","key","certificate","token","passkey","federated_trust"]}}}},{"if":{"properties":{"kind":{"const":"binding"}}},"then":{"required":["effect","constraints","eligible"],"properties":{"subtype":{"enum":["role_assignment","policy_attachment","group_membership","sharing_grant"]}}}},{"if":{"properties":{"kind":{"const":"resource"}}},"then":{"required":["actions","sensitivity"],"properties":{"actions":{"minItems":1}}}},{"if":{"properties":{"kind":{"const":"constraint"}}},"then":{"properties":{"subtype":{"enum":["device_required","approval_required","network_restriction","time_window","pim_eligible"]}}}}]},"edge":{"type":"object","additionalProperties":false,"required":["id","source","target","kind","provenance"],"properties":{"id":{"$ref":"#/$defs/id"},"source":{"$ref":"#/$defs/id"},"target":{"$ref":"#/$defs/id"},"kind":{"enum":["authenticates_as","member_of","assigned","grants","can_assume","can_read_secret","constrained_by"]},"provenance":{"$ref":"#/$defs/provenance"},"actions":{"$ref":"#/$defs/ids"},"constraints":{"$ref":"#/$defs/ids"},"actor_id":{"$ref":"#/$defs/id"},"requires":{"type":"object","additionalProperties":false,"required":["resource_id","action"],"properties":{"resource_id":{"$ref":"#/$defs/id"},"action":{"const":"read_secret"}}}},"allOf":[{"if":{"properties":{"kind":{"const":"grants"}}},"then":{"required":["actions"],"properties":{"actions":{"minItems":1}}}},{"if":{"properties":{"kind":{"const":"can_read_secret"}}},"then":{"required":["requires"]}}]}}};
const digest = value => sha256(value);
const ensure = condition => { if (!condition) throw new Error('INVALID_GRAPH_OR_PARAMETERS'); };
const valueOf = value => value instanceof Number ? Number(value) : value;
const compare = (left, right) => {
  if (Array.isArray(left) && Array.isArray(right)) {
    for (let index = 0; index < Math.min(left.length, right.length); index++) {
      const order = compare(left[index], right[index]);
      if (order) return order;
    }
    return left.length - right.length;
  }
  return left < right ? -1 : left > right ? 1 : 0;
};

function floatToken(value) {
  const numeric = Number(value);
  if (Object.is(numeric, -0)) return '-0.0';
  if (numeric === 0) return '0.0';
  const absolute = Math.abs(numeric);
  if (absolute < 0.0001 || absolute >= 1e16) {
    const [mantissa, exponent] = numeric.toExponential().split('e');
    return mantissa + 'e' + (Number(exponent) < 0 ? '-' : '+') + String(Math.abs(Number(exponent))).padStart(2, '0');
  }
  return Number.isInteger(numeric) ? String(numeric) + '.0' : String(numeric);
}

function parse(text) {
  const parsed = JSON.parse(text, (key, value, context) => {
    if (typeof value === 'number') {
      ensure(context && typeof context.source === 'string');
      ensure(!/[.eE]/.test(context.source) || Number.isFinite(value));
      const boxed = new Number(value);
      boxed.wire = /[.eE]/.test(context.source) ? floatToken(value) : BigInt(context.source).toString();
      ensure(rationalCompare(decimal(context.source), decimal(boxed.wire)) === 0);
      return boxed;
    }
    return value;
  });
  const tokens = text.match(/"(?:\\[\s\S]|[^"\\])*"|[{}\[\]:]/g) ?? [];
  const scopes = [];
  for (let index = 0; index < tokens.length; index++) {
    const token = tokens[index];
    if (token === '{') scopes.push(new Set());
    else if (token === '[') scopes.push(null);
    else if (token === '}' || token === ']') scopes.pop();
    else if (token.startsWith('"') && tokens[index + 1] === ':') {
      const key = JSON.parse(token), scope = scopes.at(-1);
      ensure(scope instanceof Set && !scope.has(key));
      scope.add(key);
    }
  }
  return parsed;
}

function canonical(value) {
  if (value instanceof Number) return value.wire;
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(key => canonical(key) + ':' + canonical(value[key])).join(',') + '}';
  const result = JSON.stringify(value);
  ensure(result !== undefined);
  return result.replace(/[\u007f-\uffff]/g, character => '\\u' + character.charCodeAt(0).toString(16).padStart(4, '0'));
}

function schemaValid(value, rule) {
  if (rule.$ref) return schemaValid(value, rule.$ref.slice(2).split('/').reduce((current, part) => current[part], schema));
  const actual = valueOf(value);
  const typeMatches = type => type === 'object' ? actual !== null && typeof actual === 'object' && !Array.isArray(actual) && !(actual instanceof Number)
    : type === 'array' ? Array.isArray(actual) : type === 'integer' ? value instanceof Number ? !/[.e]/i.test(value.wire) || Number.isInteger(actual) : typeof actual === 'number' && Number.isInteger(actual)
      : type === 'number' ? typeof actual === 'number' && Number.isFinite(actual) : type === 'null' ? actual === null : typeof actual === type;
  if (rule.type && !(Array.isArray(rule.type) ? rule.type : [rule.type]).some(typeMatches)) return false;
  if ('const' in rule && actual !== rule.const) return false;
  if (rule.enum && !rule.enum.includes(actual)) return false;
  if (typeof actual === 'number' && ((rule.minimum !== undefined && actual < rule.minimum) || (rule.maximum !== undefined && actual > rule.maximum))) return false;
  if (typeof actual === 'string') {
    if (rule.maxLength !== undefined && [...actual].length > rule.maxLength) return false;
    if (rule.pattern && !(new RegExp(rule.pattern)).test(actual)) return false;
    if (rule.format === 'date-time' && (!/(Z|[+-]\d\d:\d\d)$/.test(actual) || !Number.isFinite(Date.parse(actual)))) return false;
  }
  if (Array.isArray(actual)) {
    if (rule.minItems !== undefined && actual.length < rule.minItems) return false;
    if (rule.uniqueItems && new Set(actual.map(canonical)).size !== actual.length) return false;
    if (rule.items && !actual.every(item => schemaValid(item, rule.items))) return false;
  }
  if (typeMatches('object')) {
    const keys = Object.keys(actual);
    if (rule.required && !rule.required.every(key => key in actual)) return false;
    if (rule.minProperties && keys.length < rule.minProperties) return false;
    if (rule.propertyNames && !keys.every(key => schemaValid(key, rule.propertyNames))) return false;
    for (const key of keys) {
      if (rule.properties && key in rule.properties) { if (!schemaValid(actual[key], rule.properties[key])) return false; }
      else if (rule.additionalProperties === false) return false;
      else if (rule.additionalProperties && !schemaValid(actual[key], rule.additionalProperties)) return false;
    }
  }
  if (rule.allOf && !rule.allOf.every(branch => schemaValid(value, branch))) return false;
  if (rule.if && schemaValid(value, rule.if) && rule.then && !schemaValid(value, rule.then)) return false;
  return true;
}

function validate(graph) {
  ensure(schemaValid(graph, schema));
  const nodes = new Map(graph.nodes.map(node => [node.id, node]));
  const edges = new Map(graph.edges.map(edge => [edge.id, edge]));
  ensure(nodes.size === graph.nodes.length && edges.size === graph.edges.length && [...edges.keys()].every(key => !nodes.has(key)));
  const extra = { principal: ['provisioned_at'], credential: ['principal_id', 'provisioned_at', 'session_satisfied_constraints'], binding: ['effect', 'constraints', 'eligible'], resource: ['actions', 'sensitivity'], constraint: [] };
  for (const node of nodes.values()) {
    const fields = ['id', 'kind', 'subtype', 'name', 'provenance', ...extra[node.kind]];
    ensure(Object.keys(node).every(key => fields.includes(key)));
    if (node.kind === 'resource') ensure(node.actions.every(action => action in graph.action_weights));
    if (node.kind === 'credential') {
      ensure(nodes.get(node.principal_id)?.kind === 'principal' && nodes.get(node.principal_id).subtype !== 'group');
      ensure(!node.session_satisfied_constraints?.length || node.subtype === 'token');
    }
    ensure((node.constraints ?? []).every(key => nodes.get(key)?.kind === 'constraint'));
  }
  const endpoints = { authenticates_as: ['credential', 'principal'], member_of: ['principal', 'principal'], assigned: ['principal', 'binding'], grants: ['binding', 'resource'], can_assume: ['principal', 'principal'], can_read_secret: ['principal', 'credential'] };
  for (const edge of edges.values()) {
    const source = nodes.get(edge.source), target = nodes.get(edge.target);
    ensure((edge.kind === 'grants' || !('actions' in edge)) && (edge.kind === 'can_read_secret' || !('requires' in edge)));
    if (edge.kind === 'constrained_by') {
      ensure((source || edges.has(edge.source)) && target?.kind === 'constraint' && (!source || source.kind === 'binding'));
      continue;
    }
    ensure(source && target && source.kind === endpoints[edge.kind][0] && target.kind === endpoints[edge.kind][1]);
    ensure((edge.constraints ?? []).every(key => nodes.get(key)?.kind === 'constraint'));
    if (edge.kind === 'authenticates_as') ensure(source.principal_id === target.id);
    if (edge.kind === 'member_of') ensure(target.subtype === 'group');
    if (edge.kind === 'can_assume') ensure(target.subtype !== 'group');
    if (edge.kind === 'grants') ensure(edge.actions.every(action => target.actions.includes(action)));
    if (edge.kind === 'assigned' && target.effect === 'deny') ensure(!target.eligible && !target.constraints.length && !edge.constraints?.length);
    if (edge.kind === 'can_read_secret') {
      const resource = nodes.get(edge.requires.resource_id);
      ensure(resource?.subtype === 'secret_store' && edge.requires.action === 'read_secret' && resource.actions.includes('read_secret'));
    }
    if (edge.actor_id) ensure(nodes.get(edge.actor_id)?.kind === 'principal');
  }
  ensure(graph.nodes.some(node => node.kind === 'resource' && node.actions.length));
  graph.nodes.sort((left, right) => compare(left.id, right.id));
  graph.edges.sort((left, right) => compare(left.id, right.id));
  for (const item of [...graph.nodes, ...graph.edges]) for (const field of ['actions', 'constraints', 'session_satisfied_constraints']) if (item[field]) item[field].sort();
  return { graph, nodes, edges };
}

function gcd(left, right) {
  left = left < 0n ? -left : left;
  right = right < 0n ? -right : right;
  while (right) [left, right] = [right, left % right];
  return left;
}

function rational(numerator, denominator = 1n) {
  numerator = BigInt(numerator); denominator = BigInt(denominator);
  ensure(denominator !== 0n);
  if (denominator < 0n) { numerator = -numerator; denominator = -denominator; }
  const divisor = gcd(numerator, denominator);
  return [numerator / divisor, denominator / divisor];
}

function decimal(value) {
  const text = value instanceof Number ? value.wire : String(valueOf(value));
  if (text.includes('/')) { const [numerator, denominator] = text.split('/'); return rational(numerator, denominator); }
  const match = /^([+-]?)(\d+)(?:\.(\d*))?(?:e([+-]?\d+))?$/i.exec(text);
  ensure(match);
  const exponent = Number(match[4] ?? 0) - (match[3]?.length ?? 0);
  const numerator = BigInt((match[1] === '-' ? '-' : '') + match[2] + (match[3] ?? ''));
  return exponent >= 0 ? rational(numerator * 10n ** BigInt(exponent)) : rational(numerator, 10n ** BigInt(-exponent));
}
const add = (left, right) => rational(left[0] * right[1] + right[0] * left[1], left[1] * right[1]);
const divide = (left, right) => rational(left[0] * right[1], left[1] * right[0]);
const multiply = (left, right) => rational(left[0] * right[0], left[1] * right[1]);
const rationalCompare = (left, right) => compare(left[0] * right[1], right[0] * left[1]);
const textOf = value => value[1] === 1n ? String(value[0]) : `${value[0]}/${value[1]}`;
const total = values => values.reduce(add, rational(0));

function calculateReach(nodes, edges, credential, model) {
  const constraints = item => [...new Set([...(item.constraints ?? []), ...[...edges.values()].filter(edge => edge.kind === 'constrained_by' && edge.source === item.id).map(edge => edge.target)])];
  const blocked = item => constraints(item).some(key => {
    const subtype = nodes.get(key).subtype;
    const rejects = ['device_required', 'approval_required', ...(model === 'strict' ? ['network_restriction', 'time_window'] : [])];
    const completed = model === 'session-theft-aware' && item.kind === 'authenticates_as' && nodes.get(item.source).subtype === 'token' && nodes.get(item.source).session_satisfied_constraints?.includes(subtype);
    return rejects.includes(subtype) && !completed;
  });
  const memberships = new Map();
  const groups = (actor, qualified = false) => {
    const cache = actor + ':' + qualified;
    if (!memberships.has(cache)) {
      const found = new Set([actor]);
      let changed = true;
      while (changed) {
        changed = false;
        for (const edge of edges.values()) if (edge.kind === 'member_of' && found.has(edge.source) && (!edge.actor_id || edge.actor_id === actor) && !(qualified && blocked(edge)) && !found.has(edge.target)) { found.add(edge.target); changed = true; }
      }
      memberships.set(cache, found);
    }
    return memberships.get(cache);
  };
  const denied = (actor, resource, action) => [...edges.values()].some(assignment => assignment.kind === 'assigned' && groups(actor).has(assignment.source) && (!assignment.actor_id || assignment.actor_id === actor) && nodes.get(assignment.target).effect === 'deny' && [...edges.values()].some(grant => grant.kind === 'grants' && grant.source === assignment.target && grant.target === resource && grant.actions.includes(action) && (!grant.actor_id || grant.actor_id === actor)));
  const states = new Map();
  const initial = [credential.id, '', credential.principal_id];
  states.set(JSON.stringify(initial), { state: initial, rank: [0, 0, []] });
  let changed = true;
  while (changed) {
    changed = false;
    for (const current of [...states.values()]) {
      const [sourceId, action, actor] = current.state;
      for (const edge of edges.values()) {
        if (edge.kind === 'constrained_by' || (edge.actor_id && edge.actor_id !== actor)) continue;
        if (edge.kind === 'can_read_secret') {
          if (sourceId !== edge.requires.resource_id || action !== 'read_secret' || !groups(actor, true).has(edge.source)) continue;
        } else if (edge.source !== sourceId) continue;
        const target = nodes.get(edge.target);
        if (blocked(edge) || (target.kind === 'binding' && (target.effect === 'deny' || blocked(target)))) continue;
        let cost = ['can_assume', 'can_read_secret'].includes(edge.kind) ? 1 : 0;
        if (edge.kind === 'assigned' && (target.eligible || constraints(target).some(key => nodes.get(key).subtype === 'pim_eligible'))) cost++;
        const nextActor = target.kind === 'credential' ? target.principal_id : edge.kind === 'can_assume' ? target.id : actor;
        for (const nextAction of edge.actions ?? ['']) {
          if (target.kind === 'resource' && denied(actor, target.id, nextAction)) continue;
          const state = [target.id, nextAction, nextActor];
          const key = JSON.stringify(state);
          const rank = [current.rank[0] + cost, current.rank[1] + 1, [...current.rank[2], edge.id]];
          if (!states.has(key) || compare(rank, states.get(key).rank) < 0) { states.set(key, { state, rank }); changed = true; }
        }
      }
    }
  }
  const pairs = new Map();
  for (const { state, rank } of states.values()) if (nodes.get(state[0]).kind === 'resource') {
    const pair = state.slice(0, 2), key = JSON.stringify(pair);
    if (!pairs.has(key) || compare(rank, pairs.get(key).rank) < 0) pairs.set(key, { pair, rank });
  }
  return [...pairs.values()].sort((left, right) => compare(left.pair, right.pair));
}

function statistics(values, threshold) {
  values.sort(rationalCompare);
  const count = values.length;
  if (!count) return { credential_count: 0, maximum: null, p95: null, gini: null, share_above_threshold: null };
  const sum = total(values);
  const numerator = total(values.map((value, index) => multiply(value, rational(2 * (index + 1) - count - 1))));
  const gini = sum[0] === 0n ? rational(0) : divide(numerator, multiply(rational(count), sum));
  return { credential_count: count, maximum: textOf(values[count - 1]), p95: textOf(values[Math.ceil(0.95 * count) - 1]), gini: textOf(gini), share_above_threshold: textOf(rational(values.filter(value => rationalCompare(value, threshold) > 0).length, count)) };
}

function respond(request) {
  if (!request || request.contract_version !== PROFILE) return { contract_version: PROFILE, status: 'error', error: 'UNSUPPORTED_CONTRACT' };
  try {
    const { graph, nodes, edges } = validate(request.input);
    const parameters = request.parameters;
    ensure(compare(Object.keys(parameters).sort(), ['constraint_model', 'step_bound', 'threshold']) === 0 && MODELS.includes(parameters.constraint_model));
    ensure(typeof parameters.threshold === 'string');
    const steps = decimal(parameters.step_bound), threshold = decimal(parameters.threshold);
    ensure(parameters.step_bound instanceof Number && !/[.e]/i.test(parameters.step_bound.wire) && steps[1] === 1n && steps[0] >= 0n && rationalCompare(threshold, rational(0)) >= 0 && rationalCompare(threshold, rational(1)) <= 0);
    const universe = graph.nodes.filter(node => node.kind === 'resource').flatMap(node => node.actions.map(action => [node.id, action]));
    const sensitivitySum = pairs => total(pairs.map(([resource]) => decimal(nodes.get(resource).sensitivity)));
    const actionSum = pairs => total(pairs.map(([, action]) => decimal(graph.action_weights[action])));
    const sensitivityDenominator = sensitivitySum(universe), actionDenominator = actionSum(universe);
    const credentials = graph.nodes.filter(node => node.kind === 'credential').map(credential => {
      const reach = calculateReach(nodes, edges, credential, parameters.constraint_model);
      const pairs = reach.map(item => item.pair), bounded = reach.filter(item => BigInt(item.rank[0]) <= steps[0]).map(item => item.pair);
      const witnesses = [...reach].sort((left, right) => rationalCompare(decimal(nodes.get(right.pair[0]).sensitivity), decimal(nodes.get(left.pair[0]).sensitivity)) || compare(left.rank, right.rank) || compare(left.pair, right.pair));
      const best = witnesses[0];
      return { credential_id: credential.id, absolute_reach: pairs.length, universe_size: universe.length,
        canonical_radius: textOf(rational(pairs.length, universe.length)), sensitivity_weighted_radius: sensitivityDenominator[0] === 0n ? null : textOf(divide(sensitivitySum(pairs), sensitivityDenominator)),
        action_weighted_radius: textOf(divide(actionSum(pairs), actionDenominator)), step_bounded_radius: textOf(rational(bounded.length, universe.length)),
        reachable_pairs: pairs, bounded_pairs: bounded,
        witness: best ? { resource_id: best.pair[0], action: best.pair[1], escalation_steps: best.rank[0], graph_hops: best.rank[1], edge_ids: best.rank[2] } : null };
    });
    const distributions = {};
    for (const field of ['canonical_radius', 'sensitivity_weighted_radius', 'action_weighted_radius', 'step_bounded_radius']) distributions[field] = statistics(credentials.filter(item => item[field] !== null).map(item => decimal(item[field])), threshold);
    const response = { contract_version: PROFILE, status: 'ok', snapshot_hash: digest(canonical(graph)), parameters, credentials, statistics: distributions };
    response.manifest_hash = digest(canonical(response));
    return response;
  } catch {
    return { contract_version: PROFILE, status: 'error', error: 'INVALID_GRAPH_OR_PARAMETERS' };
  }
}

function fromText(text) {
  try { return respond(parse(text)); }
  catch { return { contract_version: PROFILE, status: 'error', error: 'INVALID_GRAPH_OR_PARAMETERS' }; }
}


globalThis.BRReference={fromText,canonical,parse,inspect(graph,id,model){const validated=validate(parse(JSON.stringify(graph)));return calculateReach(validated.nodes,validated.edges,validated.nodes.get(id),model);}};})();
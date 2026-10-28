const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('app/index.html', 'utf8');
const start = html.indexOf('function ufoPhase(');
const end = html.indexOf('\n(()=>{', start);
assert(start >= 0 && end > start, 'runner timing helpers must remain available as a deterministic block');
const sandbox = {};
vm.runInNewContext(`${html.slice(start, end)}\nglobalThis.ufoPhase=ufoPhase;globalThis.ufoEase=ufoEase;globalThis.nearestUfoCactus=nearestUfoCactus;globalThis.ufoPose=ufoPose;`, sandbox);

assert.equal(sandbox.ufoPhase(0), 'enter');
assert.equal(sandbox.ufoPhase(2.999), 'enter');
assert.equal(sandbox.ufoPhase(3), 'hover');
assert.equal(sandbox.ufoPhase(5.999), 'hover');
assert.equal(sandbox.ufoPhase(6), 'exit');
assert.equal(sandbox.ufoPhase(8.999), 'exit');
assert.equal(sandbox.ufoPhase(9), 'done');
assert.equal(sandbox.ufoEase(0), 0);
assert.equal(sandbox.ufoEase(.5), .5);
assert.equal(sandbox.ufoEase(1), 1);

const target = sandbox.nearestUfoCactus([
  { x: 8, w: 18, h: 30 },
  { x: 260, w: 20, h: 25 },
  { x: 140, w: 16, h: 32 },
], 64);
assert.equal(target.x, 140, 'UFO targets the nearest cactus ahead of the character');
assert.equal(sandbox.nearestUfoCactus([{ x: 1, w: 20 }], 64), null, 'cacti behind the character are ignored');

const pose = sandbox.ufoPose({ direction: 1, phase: 0 }, 3, 500, 300);
assert(Math.abs(pose.x - 310) < 4, 'UFO reaches its hover point after the three-second entrance');
const reverse = sandbox.ufoPose({ direction: -1, phase: 0 }, 3, 500, 300);
assert(Math.abs(reverse.x - 190) < 4, 'alternate UFOs enter from the opposite side');
assert(sandbox.ufoPose({ direction: 1, phase: 0 }, 9, 500, 300).x > 500, 'UFO exits beyond the right edge');
assert(sandbox.ufoPose({ direction: -1, phase: 0 }, 9, 500, 300).x < 0, 'alternate UFO exits beyond the left edge');
assert.notEqual(pose.rotation, sandbox.ufoPose({ direction: 1, phase: 0 }, 4, 500, 300).rotation, 'UFO spins around its own axis');

console.log('OK: UFO phases last three seconds, entry eases to the hover point, targets the nearest cactus and spins.');

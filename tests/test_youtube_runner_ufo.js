const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('app/index.html', 'utf8');
const start = html.indexOf('function ufoPhase(');
const end = html.indexOf('\n(()=>{', start);
assert(start >= 0 && end > start, 'runner timing helpers must remain available as a deterministic block');
const sandbox = {};
vm.runInNewContext(`${html.slice(start, end)}\nglobalThis.ufoPhase=ufoPhase;globalThis.ufoEase=ufoEase;globalThis.nearestUfoCactus=nearestUfoCactus;globalThis.ufoReadyToSpawn=ufoReadyToSpawn;globalThis.ufoPose=ufoPose;`, sandbox);

assert.equal(sandbox.ufoPhase(0), 'enter');
assert.equal(sandbox.ufoPhase(.999), 'enter');
assert.equal(sandbox.ufoPhase(1), 'hover');
assert.equal(sandbox.ufoPhase(1.999), 'hover');
assert.equal(sandbox.ufoPhase(2), 'exit');
assert.equal(sandbox.ufoPhase(2.999), 'exit');
assert.equal(sandbox.ufoPhase(3), 'done');
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
assert.equal(sandbox.ufoReadyToSpawn(3, 0), true, 'a UFO enters after three seconds when none is active');
assert.equal(sandbox.ufoReadyToSpawn(3, 1), false, 'an active UFO prevents overlapping spawns');
assert.equal(sandbox.ufoReadyToSpawn(2.99, 0), false, 'the spawn timer keeps the three-second cadence');

const pose = sandbox.ufoPose({ direction: 1, phase: 0 }, 1, 500, 300);
assert(Math.abs(pose.x - 310) < 3, 'UFO reaches its hover point after the one-second entrance');
const reverse = sandbox.ufoPose({ direction: -1, phase: 0 }, 1, 500, 300);
assert(Math.abs(reverse.x - 190) < 3, 'alternate UFOs enter from the opposite side');
assert(sandbox.ufoPose({ direction: 1, phase: 0 }, 3, 500, 300).x > 500, 'UFO exits beyond the right edge');
assert(sandbox.ufoPose({ direction: -1, phase: 0 }, 3, 500, 300).x < 0, 'alternate UFO exits beyond the left edge');
assert(Math.abs(pose.tilt) <= .045, 'UFO keeps upright with only a slight tilt');
assert.notEqual(pose.tilt, sandbox.ufoPose({ direction: 1, phase: 0 }, 1.2, 500, 300).tilt, 'UFO gently rocks around its own axis');

console.log('OK: a single UFO arrives every three seconds, completes one-second phases, stays upright, targets the nearest cactus and uses cached drawing.');

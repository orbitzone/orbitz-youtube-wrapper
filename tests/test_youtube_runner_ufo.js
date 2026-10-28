const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('app/index.html', 'utf8');
const start = html.indexOf('function ufoPhase(');
const end = html.indexOf('\n(()=>{', start);
assert(start >= 0 && end > start, 'runner timing helpers must remain available as a deterministic block');
const sandbox = {};
vm.runInNewContext(`${html.slice(start, end)}\nglobalThis.ufoPhase=ufoPhase;globalThis.ufoEase=ufoEase;globalThis.obstacleTop=obstacleTop;globalThis.runnerHitsObstacle=runnerHitsObstacle;globalThis.nearestUfoCactus=nearestUfoCactus;globalThis.ufoReadyToSpawn=ufoReadyToSpawn;globalThis.ufoPose=ufoPose;globalThis.validRunnerBest=validRunnerBest;`, sandbox);

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
  { type: 'cactus', x: 8, w: 18, h: 30 },
  { type: 'rock', x: 80, w: 20, h: 15 },
  { type: 'mosquito', x: 100, w: 20, h: 10, altitude: 35 },
  { type: 'cactus', x: 260, w: 20, h: 25 },
  { type: 'cactus', x: 140, w: 16, h: 32 },
], 64);
assert.equal(target.x, 140, 'UFO targets the nearest cactus ahead of the character');
assert.equal(sandbox.nearestUfoCactus([{ type: 'cactus', x: 1, w: 20 }], 64), null, 'cacti behind the character are ignored');
assert.equal(sandbox.nearestUfoCactus([{ type: 'rock', x: 80, w: 20 }], 64), null, 'rocks are excluded from the UFO cactus target');
const mosquito = { type: 'mosquito', x: 50, w: 24, h: 10, altitude: 35 };
assert.equal(sandbox.obstacleTop(mosquito, 300), 260, 'mosquito flies above the ground at a fixed altitude');
assert.equal(sandbox.runnerHitsObstacle(mosquito, 300, 300), true, 'a grounded player collides with the mosquito');
assert.equal(sandbox.runnerHitsObstacle(mosquito, 258, 300), false, 'a jump clears the mosquito flight path');
assert.equal(sandbox.runnerHitsObstacle({ type: 'rock', x: 50, w: 24, h: 15 }, 300, 300), true, 'ground obstacles still collide');
assert.equal(sandbox.ufoReadyToSpawn(0, 0), true, 'a UFO enters when its delay reaches zero');
assert.equal(sandbox.ufoReadyToSpawn(5, 0), false, 'the five-second delay prevents an early spawn');
assert.equal(sandbox.ufoReadyToSpawn(0, 1), false, 'an active UFO prevents overlapping spawns');
assert.equal(sandbox.ufoReadyToSpawn(.01, 0), false, 'the timer waits for the full delay');

const pose = sandbox.ufoPose({ direction: 1, phase: 0 }, 1, 500, 300);
assert(Math.abs(pose.x - 310) < 3, 'UFO reaches its hover point after the one-second entrance');
const reverse = sandbox.ufoPose({ direction: -1, phase: 0 }, 1, 500, 300);
assert(Math.abs(reverse.x - 190) < 3, 'alternate UFOs enter from the opposite side');
assert(sandbox.ufoPose({ direction: 1, phase: 0 }, 3, 500, 300).x > 500, 'UFO exits beyond the right edge');
assert(sandbox.ufoPose({ direction: -1, phase: 0 }, 3, 500, 300).x < 0, 'alternate UFO exits beyond the left edge');
assert(Math.abs(pose.tilt) <= .045, 'UFO keeps upright with only a slight tilt');
assert.notEqual(pose.tilt, sandbox.ufoPose({ direction: 1, phase: 0 }, 1.2, 500, 300).tilt, 'UFO gently rocks around its own axis');
assert.equal(sandbox.validRunnerBest(1234), true, 'valid high scores can be saved');
assert.equal(sandbox.validRunnerBest(-1), false, 'negative scores are rejected');
assert.equal(sandbox.validRunnerBest(1.5), false, 'fractional scores are rejected');

console.log('OK: runner collisions handle flying mosquitoes, record values are valid, and UFO phases, targets and cached drawing work.');

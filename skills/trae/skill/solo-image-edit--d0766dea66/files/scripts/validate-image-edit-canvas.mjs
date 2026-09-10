#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const IMAGE_EXTENSIONS = new Set(['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg']);
const errors = [];

function fail(location, message) {
  errors.push(`[${location}] ${message}`);
}

function parseArgs(argv) {
  const args = { projectDir: null, nodeId: null, imageSrc: null };
  for (const arg of argv) {
    if (arg.startsWith('--node-id=')) args.nodeId = arg.slice('--node-id='.length);
    else if (arg.startsWith('--image-src=')) args.imageSrc = arg.slice('--image-src='.length);
    else if (arg.startsWith('--')) fail('args', `unknown flag: ${arg}`);
    else if (!args.projectDir) args.projectDir = arg;
    else fail('args', `unexpected positional argument: ${arg}`);
  }
  return args;
}

function isPositiveInteger(value) {
  return Number.isInteger(value) && value > 0;
}

function isFiniteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

function isFlatAssetPath(value) {
  if (typeof value !== 'string') return false;
  const normalized = value.replaceAll('\\', '/');
  return normalized.startsWith('assets/')
    && path.posix.dirname(normalized) === 'assets'
    && normalized !== 'assets/.'
    && !normalized.includes('../');
}

function findDesignFile(projectDir) {
  if (!projectDir) {
    fail('args', 'missing <design-project-path>');
    return null;
  }
  if (!fs.existsSync(projectDir)) {
    fail('project', `directory not found: ${projectDir}`);
    return null;
  }
  if (!fs.statSync(projectDir).isDirectory()) {
    fail('project', `not a directory: ${projectDir}`);
    return null;
  }
  const designFiles = fs.readdirSync(projectDir).filter((name) => name.endsWith('.design')).sort();
  if (designFiles.length !== 1) {
    fail('project', `expected exactly one root .design file, found ${designFiles.length}`);
    return null;
  }
  return path.join(projectDir, designFiles[0]);
}

function readDesign(designPath) {
  if (!designPath) return null;
  try {
    const parsed = JSON.parse(fs.readFileSync(designPath, 'utf8'));
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      fail('root', 'must be a JSON object');
      return null;
    }
    return parsed;
  } catch (error) {
    fail('json', `cannot parse .design: ${error.message}`);
    return null;
  }
}

function validateImageNode(node, index, projectDir, seenIds) {
  const location = `data[${index}]`;
  if (typeof node.id !== 'string' || node.id.length === 0) {
    fail(`${location}.id`, 'must be a non-empty string');
  } else if (seenIds.has(node.id)) {
    fail(`${location}.id`, `duplicate id: ${node.id}`);
  } else {
    seenIds.add(node.id);
  }

  if (node.type !== 'image') return;

  if (typeof node.title !== 'string' || node.title.trim().length === 0) {
    fail(`${location}.title`, 'must be a non-empty string');
  }
  if (!isPositiveInteger(node.version)) {
    fail(`${location}.version`, 'must be a positive integer');
  }
  if (!isPositiveInteger(node.createdAt)) {
    fail(`${location}.createdAt`, 'must be a positive millisecond timestamp');
  }

  const imageSrc = node.devMetadata?.imageSrc;
  if (!isFlatAssetPath(imageSrc)) {
    fail(`${location}.devMetadata.imageSrc`, 'must be a flat project-relative assets/<filename> path');
  } else {
    const extension = path.extname(imageSrc).toLowerCase();
    if (!IMAGE_EXTENSIONS.has(extension)) {
      fail(`${location}.devMetadata.imageSrc`, `unsupported image extension: ${extension}`);
    }
    const resolvedAsset = path.resolve(projectDir, imageSrc);
    const assetsRoot = path.resolve(projectDir, 'assets');
    if (!resolvedAsset.startsWith(`${assetsRoot}${path.sep}`)) {
      fail(`${location}.devMetadata.imageSrc`, 'must stay inside assets/');
    } else if (!fs.existsSync(resolvedAsset) || !fs.statSync(resolvedAsset).isFile()) {
      fail(`${location}.devMetadata.imageSrc`, `asset file not found: ${imageSrc}`);
    }
  }

  if (!node.canvasData || typeof node.canvasData !== 'object' || Array.isArray(node.canvasData)) {
    fail(`${location}.canvasData`, 'must be an object');
  } else {
    if (!isFiniteNumber(node.canvasData.x)) fail(`${location}.canvasData.x`, 'must be a finite number');
    if (!isFiniteNumber(node.canvasData.y)) fail(`${location}.canvasData.y`, 'must be a finite number');
    if (Object.prototype.hasOwnProperty.call(node.canvasData, 'group')) {
      fail(`${location}.canvasData.group`, 'must not exist on image nodes');
    }
  }
}

function validateTarget(design, args) {
  if (!args.nodeId) fail('args', 'missing --node-id');
  if (!args.imageSrc) fail('args', 'missing --image-src');
  if (!Array.isArray(design.data) || design.data.length === 0) {
    fail('data', 'must be a non-empty array');
    return;
  }

  const seenIds = new Set();
  design.data.forEach((node, index) => {
    if (!node || typeof node !== 'object' || Array.isArray(node)) {
      fail(`data[${index}]`, 'must be an object');
      return;
    }
    validateImageNode(node, index, args.projectDir, seenIds);
  });

  const targets = design.data.filter((node) => node?.id === args.nodeId);
  if (targets.length !== 1) {
    fail('target', `expected exactly one node "${args.nodeId}", found ${targets.length}`);
    return;
  }
  const target = targets[0];
  if (target.type !== 'image') fail('target.type', 'must be "image"');
  if (target.devMetadata?.imageSrc !== args.imageSrc) {
    fail('target.devMetadata.imageSrc', `expected "${args.imageSrc}", found "${target.devMetadata?.imageSrc ?? ''}"`);
  }
}

const args = parseArgs(process.argv.slice(2));
if (args.projectDir) args.projectDir = path.resolve(args.projectDir);
const designPath = findDesignFile(args.projectDir);
const design = readDesign(designPath);
if (design) validateTarget(design, args);

if (errors.length > 0) {
  console.error('Validation failed:');
  for (const error of errors) console.error(`  [FAIL] ${error}`);
  process.exit(1);
}

console.log(`Validation passed: ${args.nodeId} registers ${args.imageSrc} on the .design canvas.`);

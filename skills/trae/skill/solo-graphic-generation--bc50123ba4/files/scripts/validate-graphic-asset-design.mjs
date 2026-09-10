#!/usr/bin/env node

/**
 * Validate an image-only .design project for the solo-design static graphic asset branch.
 *
 * Usage: node validate-graphic-asset-design.mjs <design-project-path> [--report-json=<path>]
 *
 * Exit codes: 0 = passed, 1 = failed
 */

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const VALID_DEVICE_TYPES = new Set(['desktop', 'mobile', 'tablet', 'freeSize']);
const IMAGE_EXTENSIONS = new Set(['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg']);
const MAX_DESIGN_JSON_BYTES = 10 * 1024 * 1024;
const MAX_PROJECT_HASH_ASSET_ENTRIES = 500;
const MAX_PROJECT_HASH_ASSET_DEPTH = 8;
const SUMMARY_MUTABLE_FIELDS = new Set([
  'validationHistory',
  'validationRepairLedger',
  'lastValidationReportCheckedAt',
  'validationSnapshot',
  'repairEntryEvidence',
  'repairStopConditionMet',
  'repairStopReason',
  'remainingBlockingIssues',
  'lastValidationReportPath',
]);
const errors = [];
const warnings = [];
const fileHashCache = new Map();
const JSON_READ_FAILED = Symbol('JSON_READ_FAILED');

function addError(loc, message) {
  errors.push(`[${loc}] ${message}`);
}

function addWarning(loc, message) {
  warnings.push(`[${loc}] ${message}`);
}

function isPositiveInteger(value) {
  return Number.isInteger(value) && value > 0;
}

function isFiniteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

function parseImageIdNumber(id) {
  const match = /^image-(\d{3,})$/.exec(id);
  if (!match) return null;
  const idNumber = Number(match[1]);
  return Number.isSafeInteger(idNumber) && idNumber > 0 ? idNumber : null;
}

function readJson(filePath) {
  try {
    const stat = fs.statSync(filePath);
    if (!stat.isFile()) {
      addError('json', `Cannot parse ${filePath}: path is not a file`);
      return JSON_READ_FAILED;
    }
    if (stat.size > MAX_DESIGN_JSON_BYTES) {
      addError('json', `Cannot parse ${filePath}: file is too large (${stat.size} bytes; max ${MAX_DESIGN_JSON_BYTES})`);
      return JSON_READ_FAILED;
    }
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (error) {
    addError('json', `Cannot parse ${filePath}: ${error.message}`);
    return JSON_READ_FAILED;
  }
}

function directoryState(dirPath, loc) {
  if (!fs.existsSync(dirPath)) return 'missing';
  try {
    return fs.statSync(dirPath).isDirectory() ? 'directory' : 'not-directory';
  } catch (error) {
    addError(loc, `Cannot inspect directory path: ${dirPath} (${error.message})`);
    return 'unreadable';
  }
}

function listTopLevelImageFiles(assetsDir) {
  try {
    if (directoryState(assetsDir, 'assets') !== 'directory') return [];
    return fs
      .readdirSync(assetsDir, { withFileTypes: true })
      .filter((entry) => entry.isFile() && IMAGE_EXTENSIONS.has(path.extname(entry.name).toLowerCase()))
      .map((entry) => entry.name)
      .sort();
  } catch (error) {
    addError('assets', `Cannot read assets directory: ${assetsDir} (${error.message})`);
    return [];
  }
}

function validateConfig(config) {
  if (config === undefined) return;
  if (typeof config !== 'object' || config === null || Array.isArray(config)) {
    addError('config', 'must be an object when present');
    return;
  }
  if (config.autoLayout !== undefined && typeof config.autoLayout !== 'boolean') {
    addError('config.autoLayout', 'must be a boolean when present');
  }
  if (config.deviceType !== undefined && !VALID_DEVICE_TYPES.has(config.deviceType)) {
    addError('config.deviceType', `invalid value "${config.deviceType}"`);
  }
  if (config.projectName !== undefined && typeof config.projectName !== 'string') {
    addError('config.projectName', 'must be a string when present');
  }
}

function validateImageNode(node, index, designDir, seenIds, seenSrcs, imageIdState) {
  const loc = `data[${index}]`;
  const idNumber = typeof node.id === 'string' ? parseImageIdNumber(node.id) : null;

  if (idNumber === null) {
    addError(`${loc}.id`, 'must match image-001 style');
  } else if (seenIds.has(node.id)) {
    addError(`${loc}.id`, `duplicate id "${node.id}"`);
  } else if (idNumber <= imageIdState.lastNumber) {
    addError(`${loc}.id`, `must be greater than previous image id "${imageIdState.lastId}"`);
  } else {
    seenIds.add(node.id);
    imageIdState.lastNumber = idNumber;
    imageIdState.lastId = node.id;
  }

  if (typeof node.title !== 'string' || node.title.trim().length === 0) {
    addError(`${loc}.title`, 'must be a non-empty string');
  }

  if (node.type !== 'image') {
    addError(`${loc}.type`, `must be "image", got "${node.type}"`);
  }

  if (!isPositiveInteger(node.version)) {
    addError(`${loc}.version`, 'must be a positive integer');
  }

  if (!isPositiveInteger(node.createdAt)) {
    addError(`${loc}.createdAt`, 'must be a positive integer timestamp');
  }

  if (typeof node.devMetadata !== 'object' || node.devMetadata === null || Array.isArray(node.devMetadata)) {
    addError(`${loc}.devMetadata`, 'must be an object');
  } else {
    const imageSrc = node.devMetadata.imageSrc;
    if (typeof imageSrc !== 'string' || imageSrc.length === 0) {
      addError(`${loc}.devMetadata.imageSrc`, 'must be a non-empty string');
    } else {
      if (!imageSrc.startsWith('assets/')) {
        addError(`${loc}.devMetadata.imageSrc`, `must start with "assets/", got "${imageSrc}"`);
      }
      const ext = path.extname(imageSrc).toLowerCase();
      if (!IMAGE_EXTENSIONS.has(ext)) {
        addError(`${loc}.devMetadata.imageSrc`, `unsupported image extension "${ext}"`);
      }
      if (seenSrcs.has(imageSrc)) {
        addError(`${loc}.devMetadata.imageSrc`, `duplicate imageSrc "${imageSrc}"`);
      } else {
        seenSrcs.add(imageSrc);
      }

      const resolved = path.resolve(designDir, imageSrc);
      const assetsRoot = path.resolve(designDir, 'assets');
      if (!resolved.startsWith(`${assetsRoot}${path.sep}`)) {
        addError(`${loc}.devMetadata.imageSrc`, 'must stay inside assets/');
      } else if (!fs.existsSync(resolved)) {
        addError(`${loc}.devMetadata.imageSrc`, `image file not found: ${imageSrc}`);
      }
    }
  }

  if (typeof node.canvasData !== 'object' || node.canvasData === null || Array.isArray(node.canvasData)) {
    addError(`${loc}.canvasData`, 'must be an object');
  } else {
    if (!isFiniteNumber(node.canvasData.x)) {
      addError(`${loc}.canvasData.x`, 'must be a finite number');
    }
    if (!isFiniteNumber(node.canvasData.y)) {
      addError(`${loc}.canvasData.y`, 'must be a finite number');
    }
    if (Object.prototype.hasOwnProperty.call(node.canvasData, 'group')) {
      addError(`${loc}.canvasData.group`, 'must not exist on image nodes');
    }
  }
}

function validateProject(projectDir) {
  if (!fs.existsSync(projectDir)) {
    addError('project', `directory not found: ${projectDir}`);
    return;
  }
  if (!fs.statSync(projectDir).isDirectory()) {
    addError('project', `not a directory: ${projectDir}`);
    return;
  }

  const designFiles = fs.readdirSync(projectDir).filter((name) => name.endsWith('.design')).sort();
  if (designFiles.length === 0) {
    addError('project', 'no .design file found in project root');
    return;
  }
  if (designFiles.length > 1) {
    addError('project', `expected one .design file, found ${designFiles.join(', ')}`);
    return;
  }

  const assetsDir = path.join(projectDir, 'assets');
  const assetsState = directoryState(assetsDir, 'assets');
  if (assetsState === 'missing') {
    addError('assets', 'assets/ directory not found');
  } else if (assetsState === 'not-directory') {
    addError('assets', 'assets exists but is not a directory');
  }

  const pagesDir = path.join(projectDir, 'pages');
  const pagesState = directoryState(pagesDir, 'pages');
  if (pagesState === 'not-directory') {
    addError('pages', 'pages exists but is not a directory');
  } else if (pagesState === 'directory') {
    try {
      const htmlFiles = fs
        .readdirSync(pagesDir, { withFileTypes: true })
        .filter((entry) => entry.isFile() && entry.name.endsWith('.html'))
        .map((entry) => entry.name);
      if (htmlFiles.length > 0) {
        addError('pages', `image-only projects must not contain HTML pages: ${htmlFiles.join(', ')}`);
      } else {
        addWarning('pages', 'pages/ directory exists but is unused in image-only projects');
      }
    } catch (error) {
      addError('pages', `Cannot read pages directory: ${pagesDir} (${error.message})`);
    }
  }

  const designPath = path.join(projectDir, designFiles[0]);
  const parsed = readJson(designPath);
  if (parsed === JSON_READ_FAILED) return;

  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
    addError('root', 'must be a JSON object');
    return;
  }

  validateConfig(parsed.config);

  if (!Array.isArray(parsed.data)) {
    addError('data', 'must be an array');
    return;
  }
  if (parsed.data.length === 0) {
    addError('data', 'must not be empty');
    return;
  }

  const seenIds = new Set();
  const seenSrcs = new Set();
  const imageIdState = { lastNumber: 0, lastId: 'image-000' };

  parsed.data.forEach((node, index) => {
    if (typeof node !== 'object' || node === null || Array.isArray(node)) {
      addError(`data[${index}]`, 'node must be an object');
      return;
    }
    validateImageNode(node, index, projectDir, seenIds, seenSrcs, imageIdState);
  });

  const topLevelImages = assetsState === 'directory' ? listTopLevelImageFiles(assetsDir) : [];
  const expectedSrcs = new Set(topLevelImages.map((name) => `assets/${name}`));

  for (const src of expectedSrcs) {
    if (!seenSrcs.has(src)) {
      addError('assets', `image file is not registered in .design: ${src}`);
    }
  }

  for (const src of seenSrcs) {
    if (!expectedSrcs.has(src)) {
      addError('data', `imageSrc does not match a top-level assets file: ${src}`);
    }
  }
}

function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

async function sha256File(filePath) {
  const stat = fs.statSync(filePath);
  const cacheKey = `${path.resolve(filePath)}:${stat.size}:${stat.mtimeMs}`;
  const cached = fileHashCache.get(cacheKey);
  if (typeof cached === 'string') return cached;
  if (cached) return cached;

  const promise = (async () => {
    const hash = crypto.createHash('sha256');
    const handle = await fs.promises.open(filePath, 'r');
    const buffer = Buffer.allocUnsafe(1024 * 1024);
    try {
      let bytesRead = 0;
      do {
        ({ bytesRead } = await handle.read(buffer, 0, buffer.length, null));
        if (bytesRead > 0) hash.update(buffer.subarray(0, bytesRead));
      } while (bytesRead > 0);
    } finally {
      await handle.close();
    }
    return hash.digest('hex');
  })();

  fileHashCache.set(cacheKey, promise);
  const digest = await promise;
  fileHashCache.set(cacheKey, digest);
  return digest;
}

async function hashFile(filePath, relPath) {
  if (relPath === 'runtime-orchestration-summary.json') {
    try {
      const summary = JSON.parse(await fs.promises.readFile(filePath, 'utf8'));
      const cloned = JSON.parse(JSON.stringify(summary));
      if (cloned.project && typeof cloned.project === 'object') {
        for (const field of SUMMARY_MUTABLE_FIELDS) delete cloned.project[field];
      }
      return crypto.createHash('sha256').update(stableJson(cloned)).digest('hex');
    } catch {
      return sha256File(filePath);
    }
  }
  return sha256File(filePath);
}

async function mapLimit(items, limit, worker) {
  const results = new Array(items.length);
  let nextIndex = 0;
  async function runWorker() {
    while (nextIndex < items.length) {
      const currentIndex = nextIndex;
      nextIndex += 1;
      results[currentIndex] = await worker(items[currentIndex], currentIndex);
    }
  }
  const workers = Array.from({ length: Math.min(limit, items.length) }, () => runWorker());
  await Promise.all(workers);
  return results;
}

async function collectProjectFileHashes(projectDir) {
  const relPaths = [];
  let assetEntryCount = 0;
  let assetDepthWarningEmitted = false;
  let assetCountWarningEmitted = false;
  function addIfExists(relPath) {
    const filePath = path.join(projectDir, relPath);
    if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
      relPaths.push(relPath.replace(/\\/g, '/'));
    }
  }
  for (const entry of fs.readdirSync(projectDir, { withFileTypes: true })) {
    if (entry.isFile() && entry.name.endsWith('.design')) relPaths.push(entry.name);
  }
  addIfExists('runtime-orchestration-summary.json');
  const assetsDir = path.join(projectDir, 'assets');
  if (fs.existsSync(assetsDir) && fs.statSync(assetsDir).isDirectory()) {
      (function visit(dir, prefix, depth = 0) {
        if (depth > MAX_PROJECT_HASH_ASSET_DEPTH) {
          if (!assetDepthWarningEmitted) {
            addWarning('project-hash', `assets/ traversal exceeded max depth ${MAX_PROJECT_HASH_ASSET_DEPTH}; deeper assets skipped`);
            assetDepthWarningEmitted = true;
          }
          return;
        }
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const rel = path.join(prefix, entry.name);
        const full = path.join(dir, entry.name);
          if (entry.isDirectory()) {
            visit(full, rel, depth + 1);
          } else if (entry.isFile() && IMAGE_EXTENSIONS.has(path.extname(entry.name).toLowerCase())) {
            if (assetEntryCount >= MAX_PROJECT_HASH_ASSET_ENTRIES) {
              if (!assetCountWarningEmitted) {
                addWarning('project-hash', `assets/ traversal reached max image count ${MAX_PROJECT_HASH_ASSET_ENTRIES}; remaining assets skipped`);
                assetCountWarningEmitted = true;
              }
              continue;
            }
            assetEntryCount += 1;
            relPaths.push(rel.replace(/\\/g, '/'));
          }
      }
    })(assetsDir, 'assets');
  }
  const entries = await mapLimit(relPaths, 8, async relPath => {
    const filePath = path.join(projectDir, relPath);
    return [relPath, await hashFile(filePath, relPath)];
  });
  const hashes = {};
  for (const [relPath, hash] of entries) hashes[relPath] = hash;
  return hashes;
}

async function writeReportJson(reportPath, projectDir) {
  const success = errors.length === 0;
  const report = {
    success,
    renderBlockingErrorCount: errors.length,
    softWarningCount: warnings.length,
    errors: [...errors],
    warnings: [...warnings],
    projectFileHashes: await collectProjectFileHashes(projectDir),
    designDir: projectDir,
    checkedAt: new Date().toISOString(),
  };
  fs.mkdirSync(path.dirname(path.resolve(reportPath)), { recursive: true });
  fs.writeFileSync(path.resolve(reportPath), `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  return report;
}

function printReport() {
  if (warnings.length > 0) {
    console.log('Warnings:');
    for (const warning of warnings) console.log(`  [WARN] ${warning}`);
  }

  if (errors.length > 0) {
    console.error('Validation failed:');
    for (const error of errors) console.error(`  [FAIL] ${error}`);
    return false;
  }

  console.log('Validation passed: image-only .design project is valid.');
  return true;
}

async function main() {
  const argv = process.argv.slice(2);
  let projectDir = null;
  let reportJsonPath = null;

  for (const arg of argv) {
    if (arg.startsWith('--report-json=')) {
      reportJsonPath = arg.slice('--report-json='.length);
    } else if (arg.startsWith('--')) {
      console.error(`Unknown flag: ${arg}`);
      process.exit(1);
    } else if (!projectDir) {
      projectDir = arg;
    }
  }

  if (!projectDir) {
    console.error('Usage: node validate-graphic-asset-design.mjs <design-project-path> [--report-json=<path>]');
    process.exit(1);
  }

  const resolvedDir = path.resolve(projectDir);
  validateProject(resolvedDir);
  const passed = printReport();

  if (reportJsonPath) {
    const report = await writeReportJson(reportJsonPath, resolvedDir);
    console.log(`\nValidation report written to: ${path.resolve(reportJsonPath)}`);
    console.log(JSON.stringify(report, null, 2));
  }

  process.exit(passed ? 0 : 1);
}

main().catch(error => {
  console.error(`[ERROR] ${error.message}`);
  process.exit(1);
});

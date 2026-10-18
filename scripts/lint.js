#!/usr/bin/env node
/**
 * Hermes Production Patterns Linter (MVP)
 *
 * Scans a Hermes skills directory and checks:
 *   1. SKILL.md frontmatter has version field (skill-evolution compliance)
 *   2. Skills with cron/scheduled tasks have corresponding STATE.md
 *   3. STATE.md / SKILL.md don't contain sensitive data patterns
 *
 * Usage:
 *   npx hermes-production-patterns lint <path>
 *   npx hermes-production-patterns lint ~/.hermes/skills/
 *   npx hermes-production-patterns lint . --fix
 */

const fs = require('fs');
const path = require('path');

// --- Configuration ---

const SENSITIVE_PATTERNS = [
  { name: 'API Key', pattern: /(?:sk|api|key|token|secret)[_-]?[a-zA-Z0-9]{20,}/gi, source: 'data-retention-privacy' },
  { name: 'Email', pattern: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, source: 'data-retention-privacy' },
  { name: 'Phone (CN)', pattern: /1[3-9]\d{9}/g, source: 'data-retention-privacy' },
  { name: 'Bearer Token', pattern: /Bearer\s+[A-Za-z0-9\-._~+/]+=*/gi, source: 'secret-management' },
  { name: 'AWS Key', pattern: /AKIA[0-9A-Z]{16}/g, source: 'secret-management' },
  { name: 'Private Key Block', pattern: /-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----/g, source: 'secret-management' },
];

const REQUIRED_FRONTMATTER_FIELDS = ['name', 'description', 'version'];
const RECOMMENDED_FRONTMATTER_FIELDS = ['maturity', 'hpp_category', 'hpp_en'];

// --- Frontmatter Parser ---

function normalizeEol(s) {
  return s.replace(/\r\n/g, '\n');
}

function detectEol(s) {
  return s.includes('\r\n') ? '\r\n' : '\n';
}

// Display width: CJK characters occupy two terminal columns. Without this the
// findings table misaligns on every Chinese file name or issue text.
function dispWidth(s) {
  let w = 0;
  for (const ch of s) {
    const cp = ch.codePointAt(0);
    const wide =
      (cp >= 0x1100 && cp <= 0x115f) ||
      (cp >= 0x2e80 && cp <= 0xa4cf) ||
      (cp >= 0xac00 && cp <= 0xd7a3) ||
      (cp >= 0xf900 && cp <= 0xfaff) ||
      (cp >= 0xfe30 && cp <= 0xfe6f) ||
      (cp >= 0xff00 && cp <= 0xff60) ||
      (cp >= 0xffe0 && cp <= 0xffe6);
    w += wide ? 2 : 1;
  }
  return w;
}

function pad(s, n) {
  return s + ' '.repeat(Math.max(0, n - dispWidth(s)));
}

function parseFrontmatter(content) {
  const src = normalizeEol(content);
  const match = src.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;
  const yaml = match[1];
  const result = {};
  for (const line of yaml.split('\n')) {
    const m = line.match(/^(\w[\w-]*):\s*(.+)/);
    if (m) {
      let val = m[2].trim();
      if (val.startsWith('"') && val.endsWith('"')) val = val.slice(1, -1);
      if (val.startsWith("'") && val.endsWith("'")) val = val.slice(1, -1);
      if (val.startsWith('[') && val.endsWith(']')) {
        val = val.slice(1, -1).split(',').map(s => s.trim().replace(/['"]/g, ''));
      }
      result[m[1]] = val;
    }
  }
  return result;
}

// --- File Discovery ---

// Generated / vendored trees. `docs/` and `site/` are build output (gitignored),
// so linting them reports findings that no contributor can act on — and makes
// a local `build_docs.py` run turn the lint red.
const SKIP_DIRS = new Set(['node_modules', 'docs', 'site', '__pycache__', 'venv']);

function walkDir(dir, filelist = []) {
  try {
    const files = fs.readdirSync(dir);
    for (const file of files) {
      const filepath = path.join(dir, file);
      try {
        const stat = fs.statSync(filepath);
        if (stat.isDirectory()) {
          if (!file.startsWith('.') && !SKIP_DIRS.has(file)) {
            walkDir(filepath, filelist);
          }
        } else {
          filelist.push(filepath);
        }
      } catch (e) {
        // skip inaccessible files
      }
    }
  } catch (e) {
    // skip inaccessible directories
  }
  return filelist;
}

// --- Rule Checks ---

function checkVersionField(filepath, content, frontmatter, findings) {
  if (!frontmatter) {
    // If the file clearly starts with a frontmatter fence but we could not
    // parse it, prepending another block would corrupt the file (this is how
    // the old --fix turned CRLF files into double-frontmatter files).
    const looksFenced = /^---\r?\n/.test(content);
    findings.push({
      file: filepath,
      issue: looksFenced
        ? 'Frontmatter present but unparsable — refusing to auto-fix'
        : 'No YAML frontmatter found',
      fixable: !looksFenced,
      pattern: 'skill-evolution',
    });
    return;
  }
  if (!frontmatter.version) {
    findings.push({
      file: filepath,
      issue: 'Missing version field in frontmatter',
      fixable: true,
      pattern: 'skill-evolution',
    });
  }
}

function checkMaturityField(filepath, content, frontmatter, findings) {
  if (frontmatter && !frontmatter.maturity) {
    findings.push({
      file: filepath,
      issue: 'Missing maturity field (battle-tested/beta/experimental)',
      fixable: true,
      pattern: 'pattern-composition',
    });
  }
}

function checkStateFile(skillDir, filepath, findings) {
  // Check if this skill has cron-related content
  const content = fs.readFileSync(filepath, 'utf-8').toLowerCase();
  const hasCron = content.includes('cron') || content.includes('schedule') || content.includes('定时') || content.includes('自动');
  if (!hasCron) return;

  // Look for STATE.md in the skill directory or parent
  const dir = path.dirname(filepath);
  const statePaths = [
    path.join(dir, 'STATE.md'),
    path.join(dir, '..', 'reports', path.basename(dir), 'STATE.md'),
  ];
  const hasState = statePaths.some(p => {
    try { return fs.statSync(p).isFile(); } catch { return false; }
  });

  if (!hasState) {
    findings.push({
      file: filepath,
      issue: 'Cron-related skill missing STATE.md (参考 state-file-pattern.md)',
      fixable: false,
      pattern: 'state-file-pattern',
    });
  }
}

function checkSensitiveData(filepath, content, findings) {
  // Skip binary-looking content
  if (content.includes('\0')) return;

  for (const { name, pattern, source } of SENSITIVE_PATTERNS) {
    const regex = new RegExp(pattern.source, pattern.flags);
    const matches = content.match(regex);
    if (matches && matches.length > 0) {
      // Filter out false positives (example/template content)
      const lineNum = content.substring(0, content.indexOf(matches[0])).split('\n').length;
      const line = content.split('\n')[lineNum - 1] || '';
      if (line.includes('example') || line.includes('示例') || line.includes('template') || line.includes('<!--')) continue;

      findings.push({
        file: filepath,
        issue: `Potential ${name} detected (line ~${lineNum}) — 参考 data-retention-privacy.md`,
        fixable: false,
        pattern: source,
      });
      break; // one finding per file per rule
    }
  }
}

// --- Fix Mode ---

function applyFix(filepath, content, finding) {
  if (!finding.fixable) return content;

  const eol = detectEol(content);
  const src = normalizeEol(content);
  let out = src;

  if (finding.issue.includes('No YAML frontmatter')) {
    const name = path.basename(path.dirname(filepath)) || path.basename(filepath, '.md');
    out = `---\nname: ${name}\ndescription: "TODO: Add description"\nversion: 0.1.0\nauthor: TODO\nlicense: MIT\nplatforms: [linux, macos, windows]\nmaturity: experimental\n---\n\n` + src;
  } else if (finding.issue.includes('Missing version field')) {
    out = src.replace(/^(---\n)/, '$1version: 0.1.0\n');
  } else if (finding.issue.includes('Missing maturity field')) {
    if (src.startsWith('---\n')) {
      out = src.replace(/^---\n/, '---\nmaturity: experimental\n');
    }
  }

  if (out === src) return content;
  return eol === '\n' ? out : out.replace(/\n/g, '\r\n');
}

// --- Main ---

function main() {
  const args = process.argv.slice(2);
  let targetDir = '.';
  let fixMode = false;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--fix') {
      fixMode = true;
    } else if (!args[i].startsWith('-')) {
      targetDir = args[i];
    }
  }

  targetDir = path.resolve(targetDir);

  if (!fs.existsSync(targetDir)) {
    console.error(`Error: Directory not found: ${targetDir}`);
    process.exit(1);
  }

  console.log(`\n🔍 Scanning: ${targetDir}\n`);

  const allFiles = walkDir(targetDir);
  const mdFiles = allFiles.filter(f => f.endsWith('.md'));
  const skillFiles = mdFiles.filter(f => path.basename(f) === 'SKILL.md');
  const stateFiles = mdFiles.filter(f => path.basename(f) === 'STATE.md');
  const conventionFiles = mdFiles.filter(f =>
    path.basename(f).endsWith('.md') &&
    (f.includes('/conventions/') || f.includes('\\conventions\\'))
  );

  const findings = [];

  // Rule 1: SKILL.md version check
  for (const filepath of skillFiles) {
    const content = fs.readFileSync(filepath, 'utf-8');
    const frontmatter = parseFrontmatter(content);
    checkVersionField(filepath, content, frontmatter, findings);
    checkMaturityField(filepath, content, frontmatter, findings);
  }

  // Rule 1b: Convention files maturity check
  for (const filepath of conventionFiles) {
    const content = fs.readFileSync(filepath, 'utf-8');
    const frontmatter = parseFrontmatter(content);
    checkVersionField(filepath, content, frontmatter, findings);
    checkMaturityField(filepath, content, frontmatter, findings);
  }

  // Rule 2: STATE.md existence for cron-related skills
  for (const filepath of skillFiles) {
    checkStateFile(path.dirname(filepath), filepath, findings);
  }

  // Rule 3: Sensitive data scan (STATE.md + SKILL.md)
  for (const filepath of [...stateFiles, ...skillFiles]) {
    const content = fs.readFileSync(filepath, 'utf-8');
    checkSensitiveData(filepath, content, findings);
  }

  // Apply fixes if requested. Every touched file is copied to a timestamped
  // backup directory first, so --fix is always reversible.
  if (fixMode) {
    const fixable = findings.filter(f => f.fixable);
    if (fixable.length > 0) {
      const stamp = new Date().toISOString().replace(/[:.]/g, '-');
      const backupDir = path.join(targetDir, '.hpp-backup', stamp);
      let fixCount = 0;
      for (const finding of fixable) {
        const content = fs.readFileSync(finding.file, 'utf-8');
        const fixed = applyFix(finding.file, content, finding);
        if (fixed === content) continue;
        const rel = path.relative(targetDir, finding.file);
        const backupPath = path.join(backupDir, rel);
        fs.mkdirSync(path.dirname(backupPath), { recursive: true });
        fs.copyFileSync(finding.file, backupPath);
        fs.writeFileSync(finding.file, fixed, 'utf-8');
        fixCount++;
        finding.fixed = true;
      }
      if (fixCount > 0) {
        console.log(`🔧 Auto-fixed ${fixCount} file(s)`);
        console.log(`   Backups: ${backupDir}\n`);
      }
    }
  }

  // Output results
  if (findings.length === 0) {
    console.log('✅ No issues found.\n');
    process.exit(0);
  }

  // Table output
  const maxFile = Math.max(6, ...findings.map(f => dispWidth(f.file)));
  const maxIssue = Math.max(7, ...findings.map(f => dispWidth(f.issue)));

  console.log('│ ' + pad('File', maxFile) + ' │ ' + pad('Issue', maxIssue) + ' │ ' + pad('Pattern Reference', 26) + ' │ Status │');
  console.log('│' + '─'.repeat(maxFile + 2) + '│' + '─'.repeat(maxIssue + 2) + '│' + '─'.repeat(28) + '│' + '─'.repeat(8) + '│');

  for (const f of findings) {
    const status = f.fixed ? '🔧 FIXED' : f.fixable ? '⚠️  WARN ' : '❌ ERROR';
    const patternLink = `conventions/${f.pattern}.md`;
    console.log(`│ ${pad(f.file, maxFile)} │ ${pad(f.issue, maxIssue)} │ ${pad(patternLink, 26)} │ ${status} │`);
  }

  console.log(`\n📊 Summary: ${findings.length} finding(s) across ${skillFiles.length} skills + ${conventionFiles.length} conventions`);
  console.log(`   Skills scanned: ${skillFiles.length}`);
  console.log(`   STATE.md files found: ${stateFiles.length}`);
  if (fixMode) {
    console.log(`   Auto-fixed: ${findings.filter(f => f.fixed).length}`);
  } else {
    console.log(`   Run with --fix to auto-repair fixable issues`);
  }
  console.log('');

  // Exit non-zero only for findings that still need attention.
  const remaining = findings.filter(f => !f.fixed);
  process.exit(remaining.length > 0 ? 1 : 0);
}

main();

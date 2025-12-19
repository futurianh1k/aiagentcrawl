#!/usr/bin/env node
/**
 * run-sql.js
 *
 * MySQL에 로컬 .sql 파일을 실행하기 위한 Node.js 유틸리티
 * 주요 기능:
 *   - .env 및 환경변수(.env via dotenv) 또는 CLI 인자 사용 가능
 *   - 여러 SQL 문을 한 번에 실행 (multipleStatements: true)
 *   - 결과 출력 옵션(--show-results) 및 롤백 테스트(--no-commit)
 *
 * 환경 변수 (선택):
 *   - MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
 *   - SEARCH_QUERY, OUTPUT 등은 크롤러와 동일한 패턴을 따릅니다 (로컬에서 import 시 참고)
 *
 * 사용 예시:
 *   node run-sql.js --file 04_database_setup.sql
 *   MYSQL_HOST=localhost MYSQL_USER=root MYSQL_PASSWORD=secret node run-sql.js --auto-yes
 *
 * 트랜잭션 주의사항:
 *   - 스크립트는 --no-commit 옵션으로 트랜잭션을 시도하여 롤백할 수 있으나,
 *     MySQL의 일부 DDL은 자동 커밋되어 롤백되지 않을 수 있습니다. 따라서 프로덕션 DB에
 *     적용할 경우 반드시 백업을 권장합니다.
 *
 * 의존성 설치:
 *   npm install mysql2 dotenv
 *
 * Author: GitHub Copilot
 */

'use strict';

const fs = require('fs');
const path = require('path');

// Try to load dotenv if present (optional)
try {
  require('dotenv').config();
} catch (e) {
  // dotenv optional
}

const mysql = (() => {
  try {
    return require('mysql2/promise');
  } catch (e) {
    return null;
  }
})();

function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  let i = 0;
  while (i < args.length) {
    const a = args[i];
    if (a === '--file' || a === '-f') {
      out.file = args[++i];
    } else if (a.startsWith('--file=')) {
      out.file = a.split('=')[1];
    } else if (a === '--host') {
      out.host = args[++i];
    } else if (a.startsWith('--host=')) {
      out.host = a.split('=')[1];
    } else if (a === '--port') {
      out.port = args[++i];
    } else if (a.startsWith('--port=')) {
      out.port = a.split('=')[1];
    } else if (a === '--user') {
      out.user = args[++i];
    } else if (a.startsWith('--user=')) {
      out.user = a.split('=')[1];
    } else if (a === '--password' || a === '--pass') {
      out.password = args[++i];
    } else if (a.startsWith('--password=')) {
      out.password = a.split('=')[1];
    } else if (a === '--database' || a === '--db') {
      out.database = args[++i];
    } else if (a.startsWith('--database=')) {
      out.database = a.split('=')[1];
    } else if (a === '--auto-yes' || a === '-y') {
      out.autoYes = true;
    } else if (a === '--show-results') {
      out.showResults = true;
    } else if (a === '--no-commit') {
      out.commit = false;
    } else if (a === '--commit') {
      out.commit = true;
    } else if (a === '--encoding') {
      out.encoding = args[++i];
    } else if (a === '--help' || a === '-h') {
      out.help = true;
    }
    i++;
  }
  return out;
}

function printHelp() {
  const script = path.basename(process.argv[1]);
  console.log(`Usage: node ${script} [options]

Options:
  --file, -f <path>       Path to .sql file (default: ./04_database_setup.sql)
  --host <host>           MySQL host (env MYSQL_HOST)
  --port <port>           MySQL port (env MYSQL_PORT)
  --user <user>           MySQL user (env MYSQL_USER)
  --password <pw>         MySQL password (env MYSQL_PASSWORD)
  --database, --db <db>   Default database (env MYSQL_DATABASE)
  --auto-yes, -y          Skip confirmation prompt and run immediately
  --show-results          Print results from SELECT statements (first 20 rows)
  --no-commit             Attempt to rollback instead of commit (may not undo DDL)
  --encoding <enc>        File encoding (default utf8-8)
  --help, -h              Show this help
`);
}

async function askConfirmation() {
  if (process.env.CI) return true;
  return new Promise((resolve) => {
    const rl = require('readline').createInterface({ input: process.stdin, output: process.stdout });
    rl.question('Proceed to execute the SQL script? [y/N]: ', (answer) => {
      rl.close();
      const ok = /^\s*(y|yes)\s*$/i.test(answer);
      resolve(ok);
    });
  });
}

async function askPassword(promptVisible) {
  if (process.env.MYSQL_PASSWORD) return process.env.MYSQL_PASSWORD;
  if (promptVisible) {
    return new Promise((resolve) => {
      const rl = require('readline').createInterface({ input: process.stdin, output: process.stdout });
      rl.question('Password (will be visible): ', (pw) => { rl.close(); resolve(pw); });
    });
  }
  // Try to use prompt-sync if available to hide input
  try {
    const prompt = require('prompt-sync')({ sigint: true });
    return prompt('Password (hidden): ', { echo: '*' });
  } catch (e) {
    // fallback to visible prompt
    return askPassword(true);
  }
}

async function main() {
  const args = parseArgs();
  if (args.help) {
    printHelp();
    process.exit(0);
  }

  const filePath = args.file || path.join(__dirname, '04_database_setup.sql');
  const encoding = args.encoding || 'utf-8';

  if (!fs.existsSync(filePath)) {
    console.error('SQL file not found:', filePath);
    process.exit(1);
  }

  const sqlText = fs.readFileSync(filePath, { encoding });

  const host = args.host || process.env.MYSQL_HOST || 'localhost';
  const port = args.port || process.env.MYSQL_PORT || '3306';
  const user = args.user || process.env.MYSQL_USER || 'root';
  const passwordArg = args.password || process.env.MYSQL_PASSWORD;
  const database = args.database || process.env.MYSQL_DATABASE || undefined;
  const autoYes = args.autoYes || false;
  const showResults = !!args.showResults;
  const commit = (typeof args.commit === 'undefined') ? true : !!args.commit;

  if (!mysql) {
    console.error('Dependency missing: mysql2 (install with: npm install mysql2)');
    process.exit(2);
  }

  let password = passwordArg;
  if (!password) {
    password = await askPassword(false);
  }

  console.log('SQL file:', filePath);
  console.log(`MySQL host=${host} port=${port} user=${user} database=${database || '<none>'}`);

  if (!autoYes) {
    const ok = await askConfirmation();
    if (!ok) {
      console.log('Cancelled by user.');
      process.exit(0);
    }
  }

  let connection;
  try {
    connection = await mysql.createConnection({
      host,
      port: Number(port),
      user,
      password,
      database,
      multipleStatements: true,
      // Helpful options
      charset: 'utf8mb4',
    });
  } catch (err) {
    console.error('Connection error:', err.message || err);
    process.exit(3);
  }

  try {
    console.log('Connected. Executing script...');

    // Attempt to use transaction if no-commit requested
    let startedTx = false;
    if (!commit) {
      try {
        await connection.beginTransaction();
        startedTx = true;
        console.log('Transaction started (will ROLLBACK at the end). Note: DDL may not be rolled back.')
      } catch (e) {
        console.warn('Could not start transaction (DDL may still be irreversible):', e.message || e);
      }
    }

    const [results] = await connection.query(sqlText);

    // mysql2 returns different shapes depending on queries; when multipleStatements=true results can be an array
    if (Array.isArray(results)) {
      console.log(`Executed ${results.length} statement groups.`);
      if (showResults) {
        // print SELECT-like results where applicable
        for (let i = 0; i < results.length; i++) {
          const res = results[i];
          if (Array.isArray(res)) {
            console.log(`-- Result set #${i}: ${res.length} rows (showing up to 20)`);
            res.slice(0, 20).forEach((r) => console.log(r));
            if (res.length > 20) console.log(`  ... and ${res.length - 20} more rows`);
          } else if (res && typeof res === 'object' && 'affectedRows' in res) {
            console.log(`-- Statement #${i}: affectedRows=${res.affectedRows}`);
          }
        }
      }
    } else {
      // single result
      if (showResults && Array.isArray(results)) {
        results.slice(0, 20).forEach((r) => console.log(r));
      } else if (results && typeof results === 'object') {
        console.log('Execution result:', JSON.stringify(results).slice(0, 500));
      }
    }

    if (!commit) {
      if (startedTx) {
        await connection.rollback();
        console.log('Rolled back transaction. NOTE: DDL may still have been applied.')
      } else {
        console.log('No transaction was started; cannot rollback reliably. Consider running with --no-commit only for DML tests.')
      }
    } else {
      // Try to commit; many DDLs auto-commit or are applied immediately
      try {
        await connection.commit();
        console.log('Committed (if any transaction was active).');
      } catch (e) {
        // commit may fail if no transaction
      }
    }

    console.log('Done.');
    await connection.end();
    process.exit(0);

  } catch (err) {
    console.error('Error while executing SQL:', err.message || err);
    try {
      if (!commit) {
        await connection.rollback();
        console.log('Rolled back transaction after error.');
      }
    } catch (e) {
      // ignore
    }
    await connection.end();
    process.exit(4);
  }
}

if (require.main === module) {
  main().catch((err) => {
    console.error('Fatal error:', err);
    process.exit(10);
  });
}

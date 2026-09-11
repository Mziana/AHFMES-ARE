/**
 * Knowledge Ingestion Script - Standalone
 * Run with: npx tsx scripts/ingest-knowledge-standalone.ts
 */

import Database from 'better-sqlite3';
import { join } from 'path';
import { existsSync, mkdirSync, readFileSync, readdirSync } from 'fs';
import fetch from 'node-fetch';

const DB_DIR = join(process.cwd(), 'data', 'knowledge');
const DB_PATH = join(DB_DIR, 'knowledge.db');

if (!existsSync(DB_DIR)) {
  mkdirSync(DB_DIR, { recursive: true });
}

const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');

const OLLAMA_URL = 'http://localhost:11434/api/embeddings';
const EMBEDDING_MODEL = 'nomic-embed-text:latest';

function initSchema() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS knowledge (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      category TEXT NOT NULL,
      title TEXT NOT NULL,
      content TEXT NOT NULL,
      tags TEXT NOT NULL DEFAULT '[]',
      importance REAL NOT NULL DEFAULT 0.5,
      embedding BLOB,
      token_count INTEGER NOT NULL DEFAULT 0,
      source TEXT NOT NULL DEFAULT 'manual',
      source_id TEXT,
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge(category);
    CREATE INDEX IF NOT EXISTS idx_knowledge_source ON knowledge(source);
    CREATE INDEX IF NOT EXISTS idx_knowledge_importance ON knowledge(importance DESC);
    CREATE INDEX IF NOT EXISTS idx_knowledge_created ON knowledge(created_at DESC);

    CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
      title, content, tags, category,
      content='knowledge',
      content_rowid='id',
      tokenize='porter unicode61'
    );

    CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge BEGIN
      INSERT INTO knowledge_fts(rowid, title, content, tags, category)
      VALUES (new.id, new.title, new.content, new.tags, new.category);
    END;

    CREATE TRIGGER IF NOT EXISTS knowledge_ad AFTER DELETE ON knowledge BEGIN
      INSERT INTO knowledge_fts(knowledge_fts, rowid, title, content, tags, category)
      VALUES ('delete', old.id, old.title, old.content, old.tags, old.category);
    END;

    CREATE TRIGGER IF NOT EXISTS knowledge_au AFTER UPDATE ON knowledge BEGIN
      INSERT INTO knowledge_fts(knowledge_fts, rowid, title, content, tags, category)
      VALUES ('delete', old.id, old.title, old.content, old.tags, old.category);
      INSERT INTO knowledge_fts(rowid, title, content, tags, category)
      VALUES (new.id, new.title, new.content, new.tags, new.category);
    END;
  `);
}

initSchema();

async function generateEmbedding(text: string): Promise<Buffer | null> {
  try {
    const response = await fetch(OLLAMA_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: EMBEDDING_MODEL,
        prompt: text,
      }),
      signal: AbortSignal.timeout(30000),
    });

    if (!response.ok) {
      console.warn(`Ollama embedding failed: ${response.status}`);
      return null;
    }

    const data = await response.json();
    const embedding = data.embedding as number[];
    
    if (!embedding || !Array.isArray(embedding) || embedding.length === 0) {
      return null;
    }

    const float32 = new Float32Array(embedding);
    return Buffer.from(float32.buffer);
  } catch (e) {
    console.warn('Embedding generation failed:', e);
    return null;
  }
}

function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4);
}

function insertEntry(entry: {
  category: string;
  title: string;
  content: string;
  tags: string[];
  importance: number;
  embedding: Buffer | null;
  token_count: number;
  source: string;
  source_id: string | null;
}): number {
  const now = Date.now();
  const stmt = db.prepare(`
    INSERT INTO knowledge (category, title, content, tags, importance, embedding, token_count, source, source_id, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  const result = stmt.run(
    entry.category,
    entry.title,
    entry.content,
    JSON.stringify(entry.tags),
    entry.importance,
    entry.embedding,
    entry.token_count,
    entry.source,
    entry.source_id,
    now,
    now
  );
  return result.lastInsertRowid as number;
}

function updateEntry(id: number, embedding: Buffer): boolean {
  const stmt = db.prepare('UPDATE knowledge SET embedding = ?, updated_at = ? WHERE id = ?');
  const result = stmt.run(embedding, Date.now(), id);
  return result.changes > 0;
}

async function seedKnowledge(): Promise<number> {
  const seeds = [
    {
      category: 'strategy',
      title: 'RSI Scalping Rules',
      content: 'RSI 14 Close. Trend Level 50. Buy: cross_up_30. Sell: cross_down_70. Divergence strongest. H1 confirmation.',
      tags: ['rsi', 'scalping'],
      importance: 0.9,
      source: 'seed',
    },
    {
      category: 'risk',
      title: 'Position Sizing',
      content: 'Account <$100: lot 0.01. SL 300-400pts. TP 300-500pts. Max 2% risk.',
      tags: ['risk', 'sizing'],
      importance: 0.95,
      source: 'seed',
    },
    {
      category: 'session',
      title: 'Trading Sessions',
      content: 'Asian low vol. London high vol best scalping. NY high vol. Overlap best.',
      tags: ['session'],
      importance: 0.8,
      source: 'seed',
    },
    {
      category: 'news',
      title: 'High Impact Events',
      content: 'NFP 1st Friday avoid 30min. CPI mid-month avoid. FOMC 8x/year avoid.',
      tags: ['news', 'nfp', 'cpi', 'fomc'],
      importance: 0.9,
      source: 'seed',
    },
    {
      category: 'pattern',
      title: 'Candlestick Patterns',
      content: 'Engulfing: strong reversal. Pin Bar: rejection at key level. Doji: indecision. Inside Bar: consolidation before breakout.',
      tags: ['pattern', 'candlestick'],
      importance: 0.85,
      source: 'seed',
    },
    {
      category: 'regime',
      title: 'Volatility Regimes',
      content: 'LOW: ATR < 3, tight spreads, range strategies. NORMAL: ATR 3-4.5, trend following works. HIGH: ATR > 4.5, wide spreads, reduce size, avoid scalping.',
      tags: ['regime', 'volatility', 'atr'],
      importance: 0.9,
      source: 'seed',
    },
    {
      category: 'parameter',
      title: 'EMA Crossover Parameters',
      content: 'Fast EMA: 9-21 for scalping, 20-50 for swing. Slow EMA: 21-50 for scalping, 50-200 for swing. Cross up = buy, cross down = sell. Filter with ADX > 25.',
      tags: ['ema', 'crossover', 'parameters'],
      importance: 0.8,
      source: 'seed',
    },
    {
      category: 'lesson',
      title: 'Overfitting Prevention',
      content: 'Always use WFO with purged K-fold. Require DSR p-value < 0.05. PSR > 0.95. Min 100 trades in OOS. Reject if IS/OOS correlation > 0.8.',
      tags: ['overfitting', 'wfo', 'dsr', 'validation'],
      importance: 0.95,
      source: 'seed',
    },
  ];

  let count = 0;
  for (const seed of seeds) {
    const embedding = await generateEmbedding(seed.content);
    insertEntry({
      ...seed,
      tags: seed.tags,
      embedding,
      token_count: estimateTokens(seed.content),
      source_id: null,
    });
    count++;
  }
  return count;
}

async function ingestFromTrades(limit: number = 100): Promise<number> {
  const filePath = join(process.cwd(), 'data', 'learning', 'trade_memory.jsonl');
  
  if (!existsSync(filePath)) {
    console.log('Trade memory file not found');
    return 0;
  }

  const lines = readFileSync(filePath, 'utf-8').trim().split('\n');
  let count = 0;

  for (const line of lines.reverse()) {
    if (count >= limit) break;
    try {
      const trade = JSON.parse(line);
      if (trade.evt === 'close') {
        const direction = trade.direction || 'UNKNOWN';
        const pnl = trade.pnl || 0;
        const win = pnl > 0;
        
        const embedding = await generateEmbedding(
          `Trade ${win ? 'WIN' : 'LOSS'}: ${direction} ${trade.style || 'micro'} @ ${trade.entry || 'N/A'}`
        );
        
        insertEntry({
          category: 'postmortem',
          title: `Trade ${win ? 'WIN' : 'LOSS'}: ${direction} ${trade.style || 'micro'} @ ${trade.entry || 'N/A'}`,
          content: `Style: ${trade.style || 'micro'}\nDirection: ${direction}\nEntry: ${trade.entry}\nExit: ${trade.exit}\nPnL: ${pnl}\nWin: ${win}\nReason: ${trade.close_reason}\nTicket: ${trade.ticket}`,
          tags: [trade.style || 'micro', direction, win ? 'win' : 'loss', trade.close_reason || 'unknown'].filter(Boolean),
          importance: 0.6,
          source: 'trade',
          source_id: String(trade.ticket),
          embedding,
          token_count: estimateTokens(`Trade ${direction} ${trade.style} ${pnl}`),
        });
        count++;
      }
    } catch (e) {
      // Skip invalid lines
    }
  }

  return count;
}

async function ingestFromBacktests(limit: number = 50): Promise<number> {
  const dirPath = join(process.cwd(), 'data', 'backtests');
  
  if (!existsSync(dirPath)) {
    console.log('Backtests directory not found');
    return 0;
  }

  const files = readdirSync(dirPath)
    .filter(f => f.endsWith('.json'))
    .sort((a, b) => b.localeCompare(a))
    .slice(0, limit);

  let count = 0;

  for (const file of files) {
    try {
      const content = readFileSync(join(dirPath, file), 'utf-8');
      const bt = JSON.parse(content);
      
      const metrics = bt.results || {};
      const config = bt.config || {};
      
      const embedding = await generateEmbedding(
        `Backtest ${bt.strategyName || 'Unknown'} ${bt.id || file}: ${metrics.totalTrades || 0} trades, ${metrics.winRate || 0}% WR, ${metrics.sharpe || 0} Sharpe`
      );
      
      insertEntry({
        category: 'backtest',
        title: `Backtest: ${bt.strategyName || 'Unknown'} ${bt.id || file}`,
        content: `Strategy: ${bt.strategyName || 'N/A'}\nSymbol: ${config.symbol || 'XAUUSD'}\nTimeframe: ${config.timeframe || 'H1'}\nPeriod: ${config.startDate} to ${config.endDate}\nTrades: ${metrics.totalTrades || 0}\nWin Rate: ${metrics.winRate || 0}%\nProfit Factor: ${metrics.profitFactor || 0}\nSharpe: ${metrics.sharpe || 0}\nMax DD: ${metrics.maxDrawdown || 0}%\nNet PnL: ${metrics.netPnl || 0}\nTotal Return: ${metrics.totalReturnPct || 0}%`,
        tags: [config.symbol || 'XAUUSD', config.timeframe || 'H1', 'backtest', bt.strategyName || 'unknown'].filter(Boolean),
        importance: Math.min(0.5 + (metrics.sharpe || 0) * 0.1, 1.0),
        source: 'backtest',
        source_id: bt.id || file.replace('.json', ''),
        embedding,
        token_count: estimateTokens(`Backtest ${bt.strategyName} ${metrics.totalTrades} trades`),
      });
      count++;
    } catch (e) {
      // Skip invalid files
    }
  }

  return count;
}

async function backfillEmbeddings(limit: number = 100): Promise<{ processed: number; failed: number }> {
  const stmt = db.prepare(`
    SELECT id, content FROM knowledge 
    WHERE embedding IS NULL 
    ORDER BY importance DESC, created_at DESC 
    LIMIT ?
  `);
  const rows = stmt.all(limit) as { id: number; content: string }[];
  
  let processed = 0;
  let failed = 0;

  for (const row of rows) {
    try {
      const embedding = await generateEmbedding(row.content);
      if (embedding) {
        const updated = updateEntry(row.id, embedding);
        if (updated) processed++;
        else failed++;
      } else {
        failed++;
      }
    } catch (e) {
      failed++;
      console.warn(`Failed to embed entry ${row.id}:`, e);
    }
  }

  return { processed, failed };
}

function getStats() {
  const total = db.prepare('SELECT COUNT(*) as c FROM knowledge').get() as { c: number };
  
  const byCat = db.prepare('SELECT category, COUNT(*) as c FROM knowledge GROUP BY category').all() as { category: string; c: number }[];
  const bySrc = db.prepare('SELECT source, COUNT(*) as c FROM knowledge GROUP BY source').all() as { source: string; c: number }[];
  const withEmb = db.prepare('SELECT COUNT(*) as c FROM knowledge WHERE embedding IS NOT NULL').get() as { c: number };
  
  return {
    total: total.c,
    byCategory: Object.fromEntries(byCat.map(r => [r.category, r.c])),
    bySource: Object.fromEntries(bySrc.map(r => [r.source, r.c])),
    withEmbeddings: withEmb.c,
  };
}

async function main() {
  console.log('🚀 Starting Knowledge Base Ingestion...\n');
  
  try {
    console.log('📚 Seeding base knowledge...');
    const seeded = await seedKnowledge();
    console.log(`   ✅ Seeded ${seeded} entries\n`);

    console.log('📊 Ingesting from trade memory...');
    const tradeCount = await ingestFromTrades(200);
    console.log(`   ✅ Ingested ${tradeCount} trades\n`);

    console.log('📈 Ingesting from backtest results...');
    const backtestCount = await ingestFromBacktests(100);
    console.log(`   ✅ Ingested ${backtestCount} backtests\n`);

    console.log('🔮 Backfilling embeddings...');
    const { processed, failed } = await backfillEmbeddings(500);
    console.log(`   ✅ Processed: ${processed}, Failed: ${failed}\n`);

    console.log('📊 Final Knowledge Base Stats:');
    const stats = getStats();
    console.log(`   Total entries: ${stats.total}`);
    console.log(`   With embeddings: ${stats.withEmbeddings}`);
    console.log('   By category:', stats.byCategory);
    console.log('   By source:', stats.bySource);
    console.log('\n✅ Knowledge Base Ingestion Complete!');

  } catch (error: any) {
    console.error('❌ Ingestion failed:', error);
    process.exit(1);
  } finally {
    db.close();
  }
}

main();
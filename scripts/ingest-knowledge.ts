/**
 * Knowledge Ingestion Script
 * Run with: npx tsx scripts/ingest-knowledge.ts
 * Seeds the knowledge base with trades, backtests, and seed knowledge
 */

import { seedKnowledge, ingestFromTrades, ingestFromBacktests, getKnowledgeStats } from '@/lib/knowledge/service';

async function main() {
  console.log('🚀 Starting Knowledge Base Ingestion...\n');
  
  try {
    // 1. Seed initial knowledge
    console.log('📚 Seeding base knowledge...');
    const seeded = await seedKnowledge();
    console.log(`   ✅ Seeded ${seeded} entries\n`);

    // 2. Ingest from trades
    console.log('📊 Ingesting from trade memory...');
    const tradeCount = await ingestFromTrades(200);
    console.log(`   ✅ Ingested ${tradeCount} trades\n`);

    // 3. Ingest from backtests
    console.log('📈 Ingesting from backtest results...');
    const backtestCount = await ingestFromBacktests(100);
    console.log(`   ✅ Ingested ${backtestCount} backtests\n`);

    // 4. Backfill embeddings for entries without them
    console.log('🔮 Backfilling embeddings...');
    const { processed, failed } = await backfillEmbeddings(500);
    console.log(`   ✅ Processed: ${processed}, Failed: ${failed}\n`);

    // 5. Show final stats
    console.log('📊 Final Knowledge Base Stats:');
    const stats = getKnowledgeStats();
    console.log(`   Total entries: ${stats.total}`);
    console.log(`   With embeddings: ${stats.withEmbeddings}`);
    console.log('   By category:', stats.byCategory);
    console.log('   By source:', stats.bySource);
    console.log('\n✅ Knowledge Base Ingestion Complete!');

  } catch (error: any) {
    console.error('❌ Ingestion failed:', error);
    process.exit(1);
  }
}

main();
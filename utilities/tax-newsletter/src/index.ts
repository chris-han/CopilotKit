import axios from 'axios';
import * as cheerio from 'cheerio';
import Parser from 'rss-parser';
import * as fs from 'fs/promises';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Types
interface NewsItem {
  title: string;
  url: string;
  date: string;
  summary: string;
  source: string;
  priority: number;
}

interface Source {
  name: string;
  url: string;
  type: 'rss' | 'web' | 'publication';
  rss_url?: string;
  keywords?: string[];
  priority: number;
}

// Configuration (simplified - in production would read from config.yml)
const config = {
  focusTopics: [
    'US-source income', 'Nonresident aliens', 'Form 1040-NR', 'W-8BEN', 
    'W-8BEN-E', 'FATCA', 'Tax treaty', 'China-US tax treaty', 
    'CRS', '1099-K', '1099-DA', 'Cross-border taxation', 
    '境外所得', '金税四期', 'Double taxation', 'Foreign account', '非居民纳税人'
  ],
  sources: {
    irs: [
      {
        name: 'IRS Newsroom',
        url: 'https://www.irs.gov/newsroom',
        type: 'rss' as const,
        rss_url: 'https://www.irs.gov/newsroom/rss',
        keywords: ['international', 'nonresident', 'alien', 'treaty', 'FATCA', 'foreign'],
        priority: 5
      },
      {
        name: 'Taxation of Nonresident Aliens',
        url: 'https://www.irs.gov/individuals/international-taxpayers/taxation-of-nonresident-aliens',
        type: 'web' as const,
        priority: 5
      },
      {
        name: 'Publication 519',
        url: 'https://www.irs.gov/publications/p519',
        type: 'publication' as const,
        priority: 5
      },
      {
        name: 'China Tax Treaty Documents',
        url: 'https://www.irs.gov/businesses/international-businesses/china-tax-treaty-documents',
        type: 'web' as const,
        priority: 4
      }
    ],
    treasury: [
      {
        name: 'Tax Treaty Documents',
        url: 'https://home.treasury.gov/policy-issues/tax-policy/treaties',
        type: 'web' as const,
        priority: 4
      }
    ],
    china: [
      {
        name: 'National Tax Administration',
        url: 'https://www.chinatax.gov.cn/',
        type: 'web' as const,
        keywords: ['境外所得', 'CRS', '税收协定', '非居民'],
        priority: 5
      },
      {
        name: 'AEOI (Automatic Exchange of Information)',
        url: 'http://www.chinatax.gov.cn/aeoi_index.html',
        type: 'web' as const,
        priority: 4
      }
    ],
    professional: [
      {
        name: 'China Briefing',
        url: 'https://www.china-briefing.com/',
        type: 'rss' as const,
        rss_url: 'https://www.china-briefing.com/news/feed/',
        keywords: ['tax', 'US', 'China', 'cross-border'],
        priority: 4
      }
    ]
  }
};

// RSS Parser
const parser = new Parser({
  timeout: 10000,
  headers: {
    'User-Agent': 'Mozilla/5.0 (compatible; TaxNewsletterBot/1.0)'
  }
});

// Fetch RSS feeds
async function fetchRSS(source: Source): Promise<NewsItem[]> {
  if (!source.rss_url) return [];
  
  try {
    console.log(`Fetching RSS from ${source.name}...`);
    const feed = await parser.parseURL(source.rss_url);
    const items: NewsItem[] = [];
    
    for (const item of feed.items.slice(0, 10)) { // Get latest 10 items
      if (!item.title || !item.link) continue;
      
      const title = item.title;
      const content = item.contentSnippet || item.content || '';
      
      // Check if relevant
      const isRelevant = source.keywords?.some(keyword => 
        title.toLowerCase().includes(keyword.toLowerCase()) ||
        content.toLowerCase().includes(keyword.toLowerCase())
      ) || !source.keywords;
      
      if (isRelevant) {
        items.push({
          title,
          url: item.link,
          date: item.pubDate || item.isoDate || new Date().toISOString(),
          summary: content.substring(0, 300) + (content.length > 300 ? '...' : ''),
          source: source.name,
          priority: source.priority
        });
      }
    }
    
    console.log(`Found ${items.length} relevant items from ${source.name}`);
    return items;
  } catch (error) {
    console.error(`Error fetching RSS from ${source.name}:`, error instanceof Error ? error.message : error);
    return [];
  }
}

// Fetch web pages
async function fetchWeb(source: Source): Promise<NewsItem[]> {
  try {
    console.log(`Fetching web page from ${source.name}...`);
    const response = await axios.get(source.url, {
      timeout: 10000,
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; TaxNewsletterBot/1.0)'
      }
    });
    
    const $ = cheerio.load(response.data);
    const items: NewsItem[] = [];
    
    // Generic news extraction (would need to be customized per site)
    $('article, .news-item, .update-item').slice(0, 5).each((_, element) => {
      const $elem = $(element);
      const title = $elem.find('h2, h3, .title').first().text().trim();
      const link = $elem.find('a').first().attr('href');
      const summary = $elem.find('p, .summary, .description').first().text().trim();
      
      if (title && link) {
        const fullUrl = link.startsWith('http') ? link : new URL(link, source.url).href;
        items.push({
          title,
          url: fullUrl,
          date: new Date().toISOString(),
          summary: summary.substring(0, 300) + (summary.length > 300 ? '...' : ''),
          source: source.name,
          priority: source.priority
        });
      }
    });
    
    // If no items found with generic selectors, create a placeholder
    if (items.length === 0) {
      items.push({
        title: `${source.name} - Check for Updates`,
        url: source.url,
        date: new Date().toISOString(),
        summary: 'Please visit the source website for the latest updates.',
        source: source.name,
        priority: source.priority
      });
    }
    
    console.log(`Found ${items.length} items from ${source.name}`);
    return items;
  } catch (error) {
    console.error(`Error fetching web page from ${source.name}:`, error instanceof Error ? error.message : error);
    // Return placeholder for failed sources
    return [{
      title: `${source.name} - Check for Updates`,
      url: source.url,
      date: new Date().toISOString(),
      summary: 'Unable to automatically fetch updates. Please visit the source website.',
      source: source.name,
      priority: source.priority
    }];
  }
}

// Collect all news items
async function collectNews(): Promise<NewsItem[]> {
  const allItems: NewsItem[] = [];
  
  // Process all source categories
  for (const [category, sources] of Object.entries(config.sources)) {
    console.log(`\nProcessing category: ${category}`);
    
    for (const source of sources) {
      try {
        let items: NewsItem[] = [];
        
        if (source.type === 'rss') {
          items = await fetchRSS(source);
        } else if (source.type === 'web' || source.type === 'publication') {
          items = await fetchWeb(source);
        }
        
        allItems.push(...items);
        
        // Small delay to be respectful
        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (error) {
        console.error(`Error processing source ${source.name}:`, error);
      }
    }
  }
  
  return allItems;
}

// Generate markdown newsletter
function generateMarkdown(items: NewsItem[]): string {
  const now = new Date();
  const dateStr = now.toISOString().split('T')[0];
  
  // Sort by priority and date
  const sortedItems = items.sort((a, b) => {
    if (a.priority !== b.priority) return b.priority - a.priority;
    return new Date(b.date).getTime() - new Date(a.date).getTime();
  });
  
  // Group by source category
  const byCategory: Record<string, NewsItem[]> = {
    'US IRS Updates': [],
    'US Treasury Updates': [],
    'China Tax Administration Updates': [],
    'Professional Analysis': []
  };
  
  for (const item of sortedItems) {
    if (item.source.includes('IRS') || item.source.includes('Publication')) {
      byCategory['US IRS Updates'].push(item);
    } else if (item.source.includes('Treasury')) {
      byCategory['US Treasury Updates'].push(item);
    } else if (item.source.includes('China') || item.source.includes('National Tax') || item.source.includes('AEOI')) {
      byCategory['China Tax Administration Updates'].push(item);
    } else {
      byCategory['Professional Analysis'].push(item);
    }
  }
  
  let markdown = `# US-China Tax Regulations Update Newsletter

**Generated:** ${dateStr}

---

## 📋 Overview

This newsletter provides the latest updates on US-China cross-border tax regulations, focusing on:
- US IRS regulations for nonresident aliens and foreign entities
- China tax administration policies on overseas income
- FATCA/CRS compliance updates
- Tax treaty developments
- Professional tax advisory insights

---

`;

  // Add each category
  for (const [category, categoryItems] of Object.entries(byCategory)) {
    if (categoryItems.length === 0) continue;
    
    markdown += `## ${category}\n\n`;
    
    for (const item of categoryItems) {
      const date = new Date(item.date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
      
      markdown += `### ${item.title}\n\n`;
      markdown += `**Source:** ${item.source} | **Date:** ${date}\n\n`;
      markdown += `${item.summary}\n\n`;
      markdown += `🔗 [Read more](${item.url})\n\n`;
      markdown += `---\n\n`;
    }
  }
  
  // Add key resources section
  markdown += `## 📚 Key Resources

### US Resources
- [IRS International Taxpayers](https://www.irs.gov/individuals/international-taxpayers)
- [Publication 519 - US Tax Guide for Aliens](https://www.irs.gov/publications/p519)
- [China-US Tax Treaty Documents](https://www.irs.gov/businesses/international-businesses/china-tax-treaty-documents)
- [Treasury Tax Treaties](https://home.treasury.gov/policy-issues/tax-policy/treaties)

### China Resources
- [National Tax Administration (国家税务总局)](https://www.chinatax.gov.cn/)
- [AEOI Portal](http://www.chinatax.gov.cn/aeoi_index.html)

### Professional Services
- [China Briefing](https://www.china-briefing.com/)
- [PwC Tax News](https://www.pwccn.com/en/tax-news.html)
- [Deloitte China Tax](https://www2.deloitte.com/cn/en/pages/tax/topics/tax-news.html)

---

## 🔍 Focus Topics

This newsletter tracks updates related to:
${config.focusTopics.map(topic => `- ${topic}`).join('\n')}

---

## ℹ️ About This Newsletter

This newsletter is automatically generated weekly by monitoring official tax administration websites and professional tax services. 

**Disclaimer:** This newsletter is for informational purposes only and does not constitute tax advice. Always consult with qualified tax professionals for your specific situation.

**Need Expert Advice?** For cross-border tax matters, consider consulting:
- A CPA licensed in both US and China
- International tax attorneys
- Big Four accounting firms with US-China tax practices

---

*Generated automatically by Tax Newsletter Bot*
`;

  return markdown;
}

// Main function
async function main() {
  console.log('🚀 Starting US-China Tax Regulations Newsletter Generation...\n');
  
  try {
    // Collect news
    console.log('📰 Collecting news from sources...');
    const items = await collectNews();
    console.log(`\n✅ Collected ${items.length} total items\n`);
    
    // Generate markdown
    console.log('📝 Generating markdown newsletter...');
    const markdown = generateMarkdown(items);
    
    // Ensure output directory exists
    const projectRoot = path.resolve(__dirname, '../../../');
    const outputDir = path.join(projectRoot, 'newsletters');
    await fs.mkdir(outputDir, { recursive: true });
    
    // Save newsletter
    const dateStr = new Date().toISOString().split('T')[0];
    const filename = `newsletter-${dateStr}.md`;
    const filepath = path.join(outputDir, filename);
    
    await fs.writeFile(filepath, markdown, 'utf-8');
    
    console.log(`\n✅ Newsletter generated successfully!`);
    console.log(`📄 Saved to: ${filepath}`);
    console.log(`📊 Total items: ${items.length}`);
    
    // Also save a 'latest.md' for easy reference
    await fs.writeFile(path.join(outputDir, 'latest.md'), markdown, 'utf-8');
    console.log(`📄 Also saved as: ${path.join(outputDir, 'latest.md')}`);
    
  } catch (error) {
    console.error('❌ Error generating newsletter:', error);
    process.exit(1);
  }
}

// Run
main();

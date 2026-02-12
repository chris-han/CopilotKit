import { source } from '../source';

export const revalidate = 3600; // Revalidate every hour

const baseUrl =
  process.env.NODE_ENV === 'development' || !process.env.VERCEL_URL
    ? 'http://localhost:3000'
    : `https://${process.env.VERCEL_URL}`;

function escapeXml(unsafe: string): string {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

export async function GET() {
  const pages = source.getPages();
  
  const rssItems = pages
    .map((page) => {
      const title = escapeXml(page.data.title || 'Untitled');
      const description = escapeXml(page.data.description || '');
      const link = `${baseUrl}${page.url}`;
      const pageData = page.data as { lastModified?: string };
      
      // Validate lastModified date
      let pubDate: string;
      if (pageData.lastModified) {
        const date = new Date(pageData.lastModified);
        pubDate = !isNaN(date.getTime()) ? date.toUTCString() : new Date().toUTCString();
      } else {
        pubDate = new Date().toUTCString();
      }
      
      return `    <item>
      <title>${title}</title>
      <description>${description}</description>
      <link>${link}</link>
      <guid isPermaLink="true">${link}</guid>
      <pubDate>${pubDate}</pubDate>
    </item>`;
    })
    .join('\n');

  const escapedBaseUrl = escapeXml(baseUrl);

  const rssFeed = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>CopilotKit Documentation</title>
    <link>${escapedBaseUrl}</link>
    <description>Build agent-native applications with generative UI, shared state, and human-in-the-loop workflows.</description>
    <language>en</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${escapedBaseUrl}/rss.xml" rel="self" type="application/rss+xml"/>
${rssItems}
  </channel>
</rss>`;

  return new Response(rssFeed, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, s-maxage=3600',
    },
  });
}

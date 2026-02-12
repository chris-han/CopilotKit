# US-China Tax Regulations Newsletter Generator

This utility automatically generates a newsletter with the latest updates on US-China cross-border tax regulations.

## Overview

The newsletter generator monitors multiple official and professional sources for tax regulation updates, including:

- **US Sources:**
  - IRS Newsroom and International Taxpayers section
  - Publication 519 (US Tax Guide for Aliens)
  - China-US Tax Treaty Documents
  - Treasury Department tax treaty updates

- **China Sources:**
  - National Tax Administration (国家税务总局)
  - AEOI (Automatic Exchange of Information) portal

- **Professional Services:**
  - China Briefing
  - PwC, Deloitte, EY, KPMG tax news (when available)

## Focus Topics

The newsletter tracks updates related to:

- US-source income and nonresident alien taxation
- Forms: 1040-NR, W-8BEN, W-8BEN-E, 1099-K, 1099-DA
- FATCA and CRS (Common Reporting Standard)
- China-US tax treaty (1984/1986, ongoing updates)
- Cross-border taxation and double taxation
- Foreign account reporting
- 境外所得 (overseas income) and 金税四期 (Golden Tax Phase IV)

## Automated Schedule

The newsletter is generated automatically:
- **Weekly:** Every Monday at 9:00 AM UTC (5:00 PM Beijing, 4:00 AM EST)
- **Manual:** Can be triggered on-demand via GitHub Actions

## Usage

### Running Locally

```bash
# Navigate to the utility directory
cd utilities/tax-newsletter

# Install dependencies
npm install

# Generate newsletter
npm run generate
```

The newsletter will be saved to `/newsletters/newsletter-YYYY-MM-DD.md`

### Manual Trigger

You can manually trigger the newsletter generation:

1. Go to the GitHub Actions tab
2. Select "US-China Tax Regulations Newsletter" workflow
3. Click "Run workflow"

## Output

The generated newsletter includes:

1. **Overview** - Summary of focus areas
2. **US IRS Updates** - Latest from IRS sources
3. **China Tax Administration Updates** - Updates from Chinese authorities
4. **Professional Analysis** - Insights from tax advisory firms
5. **Key Resources** - Quick reference links
6. **Focus Topics** - Complete list of tracked topics

## Configuration

Configuration is managed in `config.yml` and can be customized:

- Add/remove data sources
- Adjust update frequency
- Modify focus topics
- Change output format

## Technical Details

- **Language:** TypeScript/Node.js
- **Dependencies:**
  - `axios` - HTTP client
  - `cheerio` - HTML parsing
  - `rss-parser` - RSS feed parsing
- **Output Format:** Markdown
- **CI/CD:** GitHub Actions

## Important Notes

⚠️ **Disclaimer:** This newsletter is for informational purposes only and does not constitute tax advice. Always consult with qualified tax professionals for your specific situation.

🔒 **Privacy:** The tool only collects publicly available information from official sources. No personal data is collected or stored.

🤝 **Rate Limiting:** The tool respects source websites by:
- Adding delays between requests
- Using appropriate User-Agent headers
- Caching results to minimize requests

## Contributing

To add new data sources:

1. Edit `config.yml` to add the source
2. Update `src/index.ts` if custom parsing logic is needed
3. Test locally before committing

## Support

For issues or questions:
- Check existing newsletters in `/newsletters/` directory
- Review GitHub Actions logs for generation errors
- Open an issue on the repository

## License

This utility is part of the CopilotKit project and follows the same license.

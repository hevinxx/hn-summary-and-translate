<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title><xsl:value-of select="rss/channel/title"/> - RSS Feed</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        }

        .subtitle {
            font-size: 1.1em;
            opacity: 0.95;
        }

        .feed-info {
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }

        .feed-info p {
            margin: 8px 0;
            color: #495057;
        }

        .feed-info a {
            color: #667eea;
            text-decoration: none;
        }

        .feed-info a:hover {
            text-decoration: underline;
        }

        .rss-notice {
            padding: 20px 30px;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            margin: 20px 30px;
        }

        .rss-notice h3 {
            color: #856404;
            margin-bottom: 10px;
        }

        .rss-notice p {
            color: #856404;
            margin-bottom: 10px;
        }

        .rss-url {
            font-family: 'Courier New', monospace;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            word-break: break-all;
            margin: 10px 0;
        }

        .items {
            padding: 30px;
        }

        .item {
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .item:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
        }

        .item-title {
            font-size: 1.4em;
            margin-bottom: 10px;
        }

        .item-title a {
            color: #333;
            text-decoration: none;
            font-weight: bold;
        }

        .item-title a:hover {
            color: #667eea;
        }

        .item-meta {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 15px;
        }

        .item-description {
            color: #495057;
            line-height: 1.8;
            white-space: pre-wrap;
        }

        .item-links {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #dee2e6;
        }

        .item-links a {
            color: #667eea;
            text-decoration: none;
            margin-right: 20px;
            font-size: 0.9em;
        }

        .item-links a:hover {
            text-decoration: underline;
        }

        footer {
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            color: #666;
            border-top: 1px solid #dee2e6;
        }

        footer a {
            color: #667eea;
            text-decoration: none;
            font-weight: bold;
        }

        footer a:hover {
            text-decoration: underline;
        }

        @media (max-width: 600px) {
            h1 {
                font-size: 1.8em;
            }

            .item-title {
                font-size: 1.2em;
            }

            .container {
                border-radius: 0;
            }

            body {
                padding: 0;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 <xsl:value-of select="rss/channel/title"/></h1>
            <p class="subtitle"><xsl:value-of select="rss/channel/description"/></p>
        </header>

        <div class="feed-info">
            <p><strong>🔗 Website:</strong> <a href="{rss/channel/link}" target="_blank"><xsl:value-of select="rss/channel/link"/></a></p>
            <p><strong>🌐 Language:</strong> <xsl:value-of select="rss/channel/language"/></p>
            <p><strong>📅 Last Updated:</strong> <xsl:value-of select="rss/channel/lastBuildDate"/></p>
            <p><strong>⚙️ Generator:</strong> <xsl:value-of select="rss/channel/generator"/></p>
        </div>

        <div class="rss-notice">
            <h3>📡 This is an RSS Feed</h3>
            <p>RSS feeds are meant to be consumed by RSS readers and feed aggregators.</p>
            <p>Copy the URL below and paste it into your favorite RSS reader:</p>
            <div class="rss-url" id="feedUrl">
                <script>document.write(window.location.href);</script>
            </div>
            <p>Popular RSS readers: Feedly, Inoreader, NewsBlur, Reeder, NetNewsWire</p>
        </div>

        <div class="items">
            <h2 style="color: #333; margin-bottom: 20px; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                📰 Latest Articles (<xsl:value-of select="count(rss/channel/item)"/> items)
            </h2>

            <xsl:for-each select="rss/channel/item">
                <div class="item">
                    <div class="item-title">
                        <a href="{link}" target="_blank">
                            <xsl:value-of select="title"/>
                        </a>
                    </div>

                    <div class="item-meta">
                        <xsl:if test="pubDate">
                            📅 <xsl:value-of select="pubDate"/>
                        </xsl:if>
                        <xsl:if test="dc:creator">
                            | 👤 <xsl:value-of select="dc:creator"/>
                        </xsl:if>
                    </div>

                    <div class="item-description">
                        <xsl:value-of select="description" disable-output-escaping="yes"/>
                    </div>

                    <div class="item-links">
                        <a href="{link}" target="_blank">🔗 Read Article</a>
                        <xsl:if test="comments">
                            <a href="{comments}" target="_blank">💬 Hacker News Comments</a>
                        </xsl:if>
                    </div>
                </div>
            </xsl:for-each>
        </div>

        <footer>
            <p>
                <a href="https://github.com/hevinxx/hn-summary-and-translate" target="_blank">View on GitHub</a>
                |
                <a href="https://news.ycombinator.com" target="_blank">Hacker News</a>
            </p>
            <p style="margin-top: 10px; font-size: 0.9em;">
                Made with ❤️ using GitHub Actions &amp; AI
            </p>
        </footer>
    </div>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
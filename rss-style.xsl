<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:atom="http://www.w3.org/2005/Atom">

<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/rss">
<html>
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title><xsl:value-of select="channel/title"/> - RSS Feed</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: linear-gradient(135deg, #ff6600 0%, #ff8533 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }

        .header p {
            opacity: 0.95;
            font-size: 1.1em;
        }

        .feed-info {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .feed-info h2 {
            color: #ff6600;
            margin-bottom: 15px;
            font-size: 1.3em;
        }

        .feed-url {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            word-break: break-all;
            border-left: 3px solid #ff6600;
        }

        .copy-instruction {
            margin-top: 10px;
            font-size: 0.9em;
            color: #666;
        }

        .items-header {
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .items-header h2 {
            color: #333;
            font-size: 1.5em;
        }

        .item {
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .item-title {
            font-size: 1.4em;
            margin-bottom: 10px;
        }

        .item-title a {
            color: #0066cc;
            text-decoration: none;
            font-weight: 600;
        }

        .item-title a:hover {
            color: #ff6600;
            text-decoration: underline;
        }

        .item-meta {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .item-meta span {
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        .item-description {
            color: #444;
            line-height: 1.7;
            white-space: pre-wrap;
            margin-bottom: 15px;
        }

        .item-link {
            display: inline-block;
            padding: 8px 16px;
            background: #ff6600;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 0.9em;
            transition: background 0.2s;
        }

        .item-link:hover {
            background: #ff8533;
        }

        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }

        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }

            .header {
                padding: 20px;
            }

            .header h1 {
                font-size: 1.5em;
            }

            .item {
                padding: 15px;
            }

            .item-title {
                font-size: 1.2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 <xsl:value-of select="channel/title"/></h1>
            <p><xsl:value-of select="channel/description"/></p>
        </div>

        <div class="feed-info">
            <h2>🔔 Subscribe to this Feed</h2>
            <div class="feed-url">
                <xsl:value-of select="channel/atom:link[@rel='self']/@href"/>
            </div>
            <p class="copy-instruction">
                💡 Copy the URL above and add it to your favorite RSS reader (Feedly, Inoreader, NetNewsWire, etc.)
            </p>
        </div>

        <div class="items-header">
            <h2>📑 Recent Articles (<xsl:value-of select="count(channel/item)"/> items)</h2>
        </div>

        <xsl:for-each select="channel/item">
            <div class="item">
                <h3 class="item-title">
                    <a href="{link}" target="_blank">
                        <xsl:value-of select="title"/>
                    </a>
                </h3>

                <div class="item-meta">
                    <xsl:if test="pubDate">
                        <span>📅 <xsl:value-of select="pubDate"/></span>
                    </xsl:if>
                    <xsl:if test="comments">
                        <span>💬 <a href="{comments}" target="_blank" style="color: #666;">Discussion</a></span>
                    </xsl:if>
                </div>

                <div class="item-description">
                    <xsl:value-of select="description"/>
                </div>

                <a href="{link}" target="_blank" class="item-link">
                    🔗 Read Article
                </a>
            </div>
        </xsl:for-each>

        <div class="footer">
            <p>
                Generated by <strong>HN RSS Translator</strong> |
                Last updated: <xsl:value-of select="channel/lastBuildDate"/>
            </p>
            <p style="margin-top: 10px;">
                Powered by BART Summarization and Google Translate
            </p>
        </div>
    </div>
</body>
</html>
</xsl:template>

</xsl:stylesheet>

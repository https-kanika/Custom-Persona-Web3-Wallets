def generate_html_report(features, persona_markdown, output_path="persona_report.html"):
    """Generate an interactive HTML report for the wallet persona."""
    # Basic style for readability
    style = """
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; max-width: 900px; }
        h1, h2, h3 { color: #2c3e50; }
        .section { margin-bottom: 2em; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .tag { background: #3498db; color: white; padding: 4px 8px; border-radius: 12px; margin-right: 5px; display: inline-block; }
        .recommendation { background: #27ae60; color: white; padding: 6px 10px; border-radius: 6px; margin: 4px 0; }
        pre { background: #f4f4f4; padding: 10px; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }
    </style>
    """

    # Prepare classifications tags
    classifications_html = ""
    for c in features.get("classifications", []):
        classifications_html += f'<span class="tag">{c}</span> '

    # Prepare recommendations list
    recs_html = ""
    for rec in features.get("recommendations", []):
        recs_html += f'<div class="recommendation">• {rec}</div>\n'

    # Escape markdown for display inside <pre> block
    # Replace & < > for safety, keep new lines
    import html
    safe_persona_md = html.escape(persona_markdown)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Wallet Persona Report - {features.get('address')}</title>
        {style}
    </head>
    <body>
        <h1>Wallet Persona Report</h1>

        <div class="section">
            <h2>Wallet Address</h2>
            <p><strong>{features.get('address')}</strong></p>
        </div>

        <div class="section">
            <h2>Classifications</h2>
            {classifications_html or "<p>No classifications</p>"}
        </div>

        <div class="section">
            <h2>Key Metrics</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Total Networth (USD)</td><td>${features.get('total_networth', 0):,.2f}</td></tr>
                <tr><td>Native Balance</td><td>{features.get('native_balance', 0):,.4f}</td></tr>
                <tr><td>Token Balance (USD)</td><td>${features.get('token_balance_usd', 0):,.2f}</td></tr>
                <tr><td>Chain</td><td>{features.get('chain', 'unknown')}</td></tr>
                <tr><td>Token Count</td><td>{features.get('token_count', 0)}</td></tr>
                <tr><td>Unique NFT Collections</td><td>{features.get('unique_nft_collections', 0)}</td></tr>
                <tr><td>DeFi Protocols</td><td>{features.get('defi_protocols', 0)}</td></tr>
                <tr><td>Total DeFi USD</td><td>${features.get('total_defi_usd', 0):,.2f}</td></tr>
                <tr><td>Wallet Health Score</td><td>{features.get('wallet_health_score', 0)}</td></tr>
                <tr><td>Risk Score</td><td>{features.get('risk_score', 0)}</td></tr>
                <tr><td>Activity Score</td><td>{features.get('activity_score', 0)}</td></tr>
            </table>
        </div>

        <div class="section">
            <h2>Recommendations</h2>
            {recs_html or "<p>No recommendations</p>"}
        </div>

        <div class="section">
            <h2>Generated Persona Markdown</h2>
            <pre>{safe_persona_md}</pre>
        </div>

    </body>
    </html>
    """

    # Write the file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Interactive persona report generated: {output_path}")

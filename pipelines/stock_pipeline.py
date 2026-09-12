import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from tools.groq_utils import create_chat_completion
from datetime import datetime, timedelta

load_dotenv()

def run_stock_pipeline(user_query: str) -> str:

    print("\n" + "="*60)
    print("   STOCK ANALYSIS PIPELINE STARTED")
    print("="*60)

    # Step 1 - Extract stock name
    print("\n🧠 Step 1: Planner Agent extracting stock info...")
    plan_prompt = f"""
    You are a Planner Agent. Extract the stock symbol 
    or company name from this query.

    Query: {user_query}

    Reply ONLY in this format:
    COMPANY: [company name]
    SYMBOL: [stock symbol if mentioned, else UNKNOWN]
    ANALYSIS_TYPE: [short term / long term / general]
    """

    plan_response = create_chat_completion(
        messages=[{"role": "user", "content": plan_prompt}]
    )
    plan = plan_response.choices[0].message.content.strip()
    print("✅ Stock identified!")
    print(plan)

    # Step 2 - Analyze stock
    print("\n📈 Step 2: Analyzer Agent analyzing...")
    analyze_prompt = f"""
    You are a Stock Analysis Agent. Provide a detailed 
    analysis for the following stock query.

    User Query: {user_query}
    Stock Info: {plan}

    IMPORTANT: Always detect the language of the user's
    message and respond in that SAME language.
    If user writes in Hindi, respond in Hindi.
    If user writes in Japanese, respond in Japanese.
    If user writes in Tamil, respond in Tamil.
    Never switch languages unless user asks.

    Provide analysis in these sections:
    
    1. COMPANY OVERVIEW
       Brief about the company and its business
    
    2. RECENT PERFORMANCE
       How the stock has been performing recently
    
    3. STRENGTHS
       Key strengths of this stock
    
    4. RISKS
       Key risks to consider
    
    5. RECOMMENDATION
       Short term and long term recommendation
       Risk level: Low / Medium / High
    """

    analyze_response = create_chat_completion(
        messages=[{"role": "user", "content": analyze_prompt}],
        model="openai/gpt-oss-20b",
        max_tokens=800
    )
    analysis = analyze_response.choices[0].message.content.strip()
    print("✅ Analysis done!")

    # Step 3 - Generate final report
    print("\n📊 Step 3: Reporter Agent generating report...")
    now = datetime.now().strftime("%d-%m-%Y %H:%M")

    final_report = f"""
{'='*60}
        STOCK ANALYSIS REPORT
{'='*60}
Query    : {user_query}
Date     : {now}
{'='*60}

{analysis}

{'='*60}
⚠️  DISCLAIMER: This is AI generated analysis only.
    Not financial advice. Do your own research.
{'='*60}
    """
    print("✅ Report ready!")

    return final_report


def get_stock_chart(symbol: str) -> go.Figure:
    """Generate interactive stock chart using yfinance"""
    try:
        # Fetch stock data
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="3mo")

        if df.empty:
            return None

        # Create subplot with 2 rows
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(
                f'{symbol} Price (3 Months)',
                'Volume'
            ),
            row_width=[0.2, 0.7]
        )

        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name="Price",
                increasing_line_color='#00ff88',
                decreasing_line_color='#ff4444'
            ),
            row=1, col=1
        )

        # Moving averages
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['MA20'],
                name="MA20",
                line=dict(color='#FFD700', width=1.5)
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['MA50'],
                name="MA50",
                line=dict(color='#FF6B35', width=1.5)
            ),
            row=1, col=1
        )

        # Volume bars
        colors = [
            '#00ff88' if row['Close'] >= row['Open']
            else '#ff4444'
            for _, row in df.iterrows()
        ]

        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name="Volume",
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )

        # Layout
        fig.update_layout(
            title=f"{symbol} — Live Stock Chart",
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=600,
            showlegend=True,
            legend=dict(
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="#333",
                borderwidth=1
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        fig.update_xaxes(
            gridcolor='#333',
            showgrid=True
        )
        fig.update_yaxes(
            gridcolor='#333',
            showgrid=True
        )

        return fig

    except Exception as e:
        print(f"Chart error: {e}")
        return None


def get_stock_metrics(symbol: str) -> dict:
    """Get key stock metrics from yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="1d")

        current_price = hist['Close'].iloc[-1] if not hist.empty else 0
        prev_close = info.get('previousClose', 0)
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0

        return {
            "current_price": round(current_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "market_cap": info.get('marketCap', 'N/A'),
            "pe_ratio": info.get('trailingPE', 'N/A'),
            "52w_high": info.get('fiftyTwoWeekHigh', 'N/A'),
            "52w_low": info.get('fiftyTwoWeekLow', 'N/A'),
            "volume": info.get('volume', 'N/A'),
            "avg_volume": info.get('averageVolume', 'N/A'),
            "dividend_yield": info.get('dividendYield', 'N/A'),
            "name": info.get('longName', symbol)
        }
    except Exception as e:
        print(f"Metrics error: {e}")
        return {}


def get_news_sentiment(company_name: str, symbol: str) -> dict:
    """Fetch live news and analyze sentiment"""
    try:
        NEWS_KEY = os.getenv("NEWS_API_KEY")

        # Fetch news
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": company_name,
            "apiKey": NEWS_KEY,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 10,
            "from": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "ok":
            return {}

        articles = data.get("articles", [])
        if not articles:
            return {}

        # Prepare headlines for sentiment analysis
        headlines = []
        for article in articles[:8]:
            title = article.get("title", "")
            if title and "[Removed]" not in title:
                headlines.append({
                    "title": title,
                    "url": article.get("url", ""),
                    "published": article.get("publishedAt", "")[:10]
                })

        # AI Sentiment Analysis
        headlines_text = "\n".join([f"- {h['title']}" for h in headlines])

        sentiment_prompt = f"""
        Analyze the sentiment of these news headlines 
        about {company_name} stock.

        Headlines:
        {headlines_text}

        Reply ONLY in this exact format:
        POSITIVE: [number]%
        NEGATIVE: [number]%
        NEUTRAL: [number]%
        OVERALL: [BULLISH/BEARISH/NEUTRAL]
        SUMMARY: [one line summary]
        """

        from tools.groq_utils import client
        sentiment_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": sentiment_prompt}]
        )

        sentiment = sentiment_response.choices[0].message.content.strip()

        return {
            "headlines": headlines,
            "sentiment": sentiment,
            "total_articles": len(headlines)
        }

    except Exception as e:
        print(f"News error: {e}")
        return {}

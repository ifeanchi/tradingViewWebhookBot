# TradingView Webhook Bot

A Python FastAPI webhook server that receives BUY/SELL/EXIT alerts from TradingView indicators and logs them to SQLite and CSV for analysis.

## 🎯 Purpose

This bot receives trading signals from your TradingView indicator (e.g., the Zone Sweep indicator we built) and:
- ✅ Validates webhook authentication
- ✅ Logs all signals to SQLite database
- ✅ Creates CSV backup for easy analysis
- ✅ Prevents duplicate signals (10-second window)
- ✅ Provides API to query logged signals

## ⚠️ Important: Logging Only

**This bot does NOT place trades.** It only logs signals for:
- Backtesting strategy performance
- Manual review before execution
- Building trading history
- Future broker integration (coming later)

## 📁 Project Structure

```
tradingview-webhook-bot/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .env                 # Your actual secrets (gitignored)
├── signals.db           # SQLite database (auto-created)
├── trade_signals.csv    # CSV backup (auto-created)
└── README.md            # This file
```

## 🚀 Quick Start

### 1. Clone/Setup Project

```bash
cd tradingview-webhook-bot
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Copy example file
cp .env.example .env

# Generate a secure secret
openssl rand -hex 32

# Edit .env and add your secret
nano .env
```

Your `.env` file should look like:
```bash
WEBHOOK_SECRET=9d7a3b12e6f44f2ea8c5d9012345678901234567890abcdef1234567890abcdef
```

### 3. Run the Server

```bash
python main.py
```

Server will start on `http://localhost:8000`

## 🔌 API Endpoints

### 1. POST /webhook
Receive TradingView alerts

**Request Body:**
```json
{
  "secret": "YOUR_WEBHOOK_SECRET",
  "source": "Greedy Futures Indicator",
  "action": "BUY",
  "symbol": "MNQ1!",
  "price": "22500.25",
  "timeframe": "15",
  "exchange": "CME_MINI",
  "timestamp": "2026-06-08T09:45:00Z"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "id": 1,
  "action": "BUY",
  "symbol": "MNQ1!",
  "message": "Signal logged successfully"
}
```

**Response (Duplicate):**
```json
{
  "status": "ignored",
  "reason": "duplicate_detected",
  "message": "Similar signal received within 10 seconds"
}
```

### 2. GET /health
Health check

**Response:**
```json
{"status": "ok"}
```

### 3. GET /signals
Get latest 100 signals

**Response:**
```json
{
  "signals": [
    {
      "id": 1,
      "received_at": "2026-06-08T09:45:01Z",
      "source": "Greedy Futures Indicator",
      "action": "BUY",
      "symbol": "MNQ1!",
      "price": "22500.25",
      "timeframe": "15",
      "exchange": "CME_MINI",
      "alert_timestamp": "2026-06-08T09:45:00Z"
    }
  ],
  "count": 1
}
```

## 🧪 Testing

### Test with curl

```bash
# Health check
curl http://localhost:8000/health

# Valid webhook
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "YOUR_WEBHOOK_SECRET",
    "source": "Greedy Futures Indicator",
    "action": "BUY",
    "symbol": "MNQ1!",
    "price": "22500.25",
    "timeframe": "15",
    "exchange": "CME_MINI",
    "timestamp": "2026-06-08T09:45:00Z"
  }'

# Invalid secret (should return 403)
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"secret": "wrong", "action": "BUY"}'

# Get signals
curl http://localhost:8000/signals
```

## 📊 TradingView Alert Configuration

### Pine Script Alert Message

In your TradingView indicator, add this to your alert:

```pinescript
// In your indicator code
alertMessage = '{' +
    '"secret": "YOUR_WEBHOOK_SECRET",' +
    '"source": "Zone Sweep Indicator",' +
    '"action": "' + (longSignal ? "BUY" : shortSignal ? "SELL" : "EXIT") + '",' +
    '"symbol": "' + syminfo.ticker + '",' +
    '"price": "' + str.tostring(close) + '",' +
    '"timeframe": "' + timeframe.period + '",' +
    '"exchange": "' + syminfo.exchange + '",' +
    '"timestamp": "' + str.format_time(time, "yyyy-MM-dd'T'HH:mm:ss'Z'") + '"' +
    '}'

// Trigger alert
if longSignal
    alert(alertMessage, title="Long Signal")
```

### Manual Alert Setup in TradingView

1. Right-click your chart
2. Click "Add Alert"
3. Set Condition: Your indicator's signal
4. Message: (Paste the JSON below)

```json
{
  "secret": "YOUR_WEBHOOK_SECRET",
  "source": "Zone Sweep Indicator",
  "action": "{{strategy.order.action}}",
  "symbol": "{{ticker}}",
  "price": "{{close}}",
  "timeframe": "{{interval}}",
  "exchange": "{{exchange}}",
  "timestamp": "{{time}}"
}
```

**Note:** If using TradingView's {{variable}} syntax, use this instead:
```json
{"secret":"YOUR_SECRET","source":"Zone Sweep","action":"{{strategy.order.action}}","symbol":"{{ticker}}","price":"{{close}}","timeframe":"{{interval}}","exchange":"{{exchange}}","timestamp":"{{time}}"}
```

5. Webhook URL: `http://YOUR_SERVER_IP:8000/webhook`

## 🌐 Deployment

### Option 1: VPS/Cloud Server (Recommended)

**Prerequisites:**
- Ubuntu 20.04+ server
- Python 3.9+
- Domain (optional)

**Setup:**
```bash
# On your server
git clone <your-repo>
cd tradingview-webhook-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your secret
nano .env
```

**Run with Systemd:**
Create `/etc/systemd/system/tradingview-bot.service`:
```ini
[Unit]
Description=TradingView Webhook Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/tradingview-webhook-bot
Environment="PATH=/home/ubuntu/tradingview-webhook-bot/venv/bin"
ExecStart=/home/ubuntu/tradingview-webhook-bot/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable tradingview-bot
sudo systemctl start tradingview-bot
sudo systemctl status tradingview-bot
```

**With Nginx (SSL):**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Option 2: Railway/Render (Easy Deploy)

**Railway:**
1. Push code to GitHub
2. Connect Railway to repo
3. Add `WEBHOOK_SECRET` environment variable
4. Deploy

**Render:**
1. Create new Web Service
2. Connect GitHub repo
3. Set environment variables
4. Deploy

### Option 3: Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t tradingview-bot .
docker run -p 8000:8000 --env-file .env tradingview-bot
```

## 🔒 Security Best Practices

1. **Keep WEBHOOK_SECRET safe:**
   - Never commit `.env` to git
   - Use strong secret (32+ chars)
   - Rotate periodically

2. **Use HTTPS in production:**
   - TradingView requires HTTPS for webhooks
   - Use Let's Encrypt free SSL

3. **Firewall:**
   - Only open port 8000 (or 443)
   - Restrict IP if possible

4. **Database:**
   - SQLite is fine for logging
   - Back up `signals.db` regularly

## 📈 Viewing Your Data

### SQLite CLI
```bash
sqlite3 signals.db

# View last 10 signals
SELECT * FROM signals ORDER BY received_at DESC LIMIT 10;

# Count signals by action
SELECT action, COUNT(*) FROM signals GROUP BY action;

# View today's signals
SELECT * FROM signals WHERE DATE(received_at) = DATE('now');
```

### CSV Analysis
Open `trade_signals.csv` in Excel, Google Sheets, or Python pandas:
```python
import pandas as pd
df = pd.read_csv('trade_signals.csv')
print(df.groupby('action').count())
```

## 🔧 Troubleshooting

**Error: "WEBHOOK_SECRET environment variable is required"**
→ Create `.env` file with your secret

**Error: "Invalid secret"**
→ Check that TradingView alert includes correct secret

**Signals not appearing**
→ Check `/health` endpoint
→ Verify TradingView webhook URL is correct
→ Check server firewall

**Duplicates not filtering**
→ Verify `DUPLICATE_WINDOW_SECONDS` (default: 10s)
→ Check that action+symbol+timeframe+price are identical

## 📝 License

MIT License - Free to use and modify

## 🚀 Roadmap

- [ ] Add broker execution (IBKR, Alpaca)
- [ ] Telegram/Discord notifications
- [ ] Web dashboard for signal analysis
- [ ] Paper trading mode
- [ ] Risk management rules

## 💬 Support

For issues or questions, check:
1. Server logs: `journalctl -u tradingview-bot -f`
2. TradingView alert logs
3. Test with curl before TradingView

---

**Built for the Zone Sweep Trading Strategy** 🎯
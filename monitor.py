import json
import time
import urllib.request
import urllib.error
from datetime import datetime

# --- CONFIGURATION LOADER ---
def load_config(filepath="config.json"):
    with open(filepath, 'r') as f:
        return json.load(f)

# --- WEBHOOK SENDER ---
def send_discord_alert(webhook_url, message, color):
    # Colors: Red = 16711680, Green = 65280
    data = {
        "embeds": [{
            "title": "Uptime Alert",
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    
    # Prepare the POST request
    req = urllib.request.Request(webhook_url, method="POST")
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Lightweight-Monitor/1.0')
    
    try:
        urllib.request.urlopen(req, data=json.dumps(data).encode('utf-8'))
    except Exception as e:
        print(f"Failed to send Discord webhook: {e}")

# --- SITE CHECKER ---
def check_site(url):
    try:
        # We use a 10-second timeout. If it takes longer, we assume it's struggling/down.
        req = urllib.request.Request(url, headers={'User-Agent': 'Lightweight-Monitor/1.0'})
        response = urllib.request.urlopen(req, timeout=10)
        return response.getcode() in [200, 201, 202, 301, 302]
    except Exception:
        # Catch timeouts, 404s, 500s, or DNS failures
        return False

# --- MAIN LOOP ---
def main():
    config = load_config()
    
    # In-memory dictionary to track what is currently up or down.
    # We assume everything is UP on startup to avoid spamming alerts when you first turn it on.
    status_memory = {url: True for url in config['urls']} 
    
    print(f"🚀 Monitoring {len(config['urls'])} sites every {config['check_interval_seconds']} seconds...")

    try:
        while True:
            for url in config['urls']:
                is_up = check_site(url)
                was_up = status_memory[url]

                # State changed from UP to DOWN
                if not is_up and was_up:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 DOWN: {url}")
                    send_discord_alert(config['discord_webhook_url'], f"**DOWN:** {url} is unreachable!", 16711680)
                    status_memory[url] = False
                
                # State changed from DOWN to UP
                elif is_up and not was_up:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ UP: {url}")
                    send_discord_alert(config['discord_webhook_url'], f"**UP:** {url} is back online!", 65280)
                    status_memory[url] = True
                
                # No change, just log to terminal
                else:
                    status_text = "UP" if is_up else "DOWN"
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] - {status_text}: {url}")
            
            # Wait for the next cycle
            time.sleep(config['check_interval_seconds'])
            
    except KeyboardInterrupt:
        print("\nStopping monitor...")

if __name__ == "__main__":
    main()
# Ethical APK Analyzer Telegram Bot

Personal-use bot for APKs you own or are authorized to analyze.

## Features
- Owner Chat ID restriction
- APK upload
- SHA-256 hash
- JADX-based decompilation
- Search questions for likely relevant source/layout files
- Basic screenshot workflow

## Linux installation
```bash
sudo apt update
sudo apt install -y default-jre unzip
```

Install JADX and make the `jadx` command available in PATH.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set secrets:
```bash
export BOT_TOKEN='your_bot_token'
export OWNER_CHAT_ID='your_numeric_chat_id'
python bot.py
```

Do not hard-code your Telegram token in public source code. If your token is ever exposed, revoke it in BotFather and create a new one.

## Important
Decompiled output is reconstructed code and may not exactly match the original developer's source structure. Use only on applications you own or are explicitly authorized to test.

import os, re, json, shutil, hashlib, asyncio, subprocess
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", "0"))
WORK = Path("workspace")
WORK.mkdir(exist_ok=True)

def allowed(update):
    return update.effective_chat and update.effective_chat.id == OWNER_CHAT_ID

def run(cmd, cwd=None, timeout=180):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode == 0, (p.stdout + "\n" + p.stderr)
    except Exception as e:
        return False, str(e)

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    await update.message.reply_text(
        "APK Security Analyzer ready.\n\n"
        "1. Send an APK\n2. Wait for analysis\n3. Ask questions such as: login page ka code kahan hai?\n\n"
        "Only analyze APKs you own or are authorized to test."
    )

async def apk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    doc = update.message.document
    if not doc.file_name.lower().endswith(".apk"):
        return
    job = WORK / f"{update.effective_chat.id}_{doc.file_unique_id}"
    job.mkdir(parents=True, exist_ok=True)
    apk = job / doc.file_name
    await (await doc.get_file()).download_to_drive(apk)
    await update.message.reply_text("Scanning APK… this may take a moment.")

    report = [f"APK: {doc.file_name}", f"SHA-256: {sha256(apk)}"]
    outdir = job / "jadx"
    ok, output = run(["jadx", "-d", str(outdir), str(apk)], timeout=300)
    if ok:
        files_list = [str(p.relative_to(outdir)) for p in outdir.rglob("*") if p.is_file()]
        context.chat_data["apk_dir"] = str(outdir)
        context.chat_data["apk_name"] = doc.file_name
        context.chat_data["last_job"] = str(job)
        report += [
            "Status: Decompiled successfully",
            f"Indexed files: {len(files_list)}",
            "",
            "You can now ask questions, for example:",
            "• login page ka code kahan hai?",
            "• API URLs kahan hain?",
            "• MainActivity kahan hai?"
        ]
    else:
        report += ["Status: Basic file received, but JADX is not installed or analysis failed.",
                   "Install JADX on the server and make sure `jadx` is available in PATH."]
    await update.message.reply_text("\n".join(report))

def search_files(base, terms):
    base=Path(base)
    matches=[]
    for p in base.rglob("*"):
        if not p.is_file() or p.stat().st_size > 2_000_000: continue
        name=p.name.lower()
        score=sum(t in name for t in terms)*10
        if score:
            matches.append((score,p))
            continue
        try:
            txt=p.read_text(errors="ignore").lower()
            score=sum(txt.count(t) for t in terms)
            if score: matches.append((score,p))
        except: pass
    return sorted(matches, reverse=True, key=lambda x:x[0])[:10]

async def question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    if "apk_dir" not in context.chat_data:
        await update.message.reply_text("Pehle APK upload karein.")
        return
    q=update.message.text.lower()
    keywords = re.findall(r"[a-z0-9_]{3,}", q)
    mapping = {
        "login":["login","signin","sign_in","authentication","auth"],
        "api":["api","baseurl","retrofit","okhttp","http"],
        "main":["mainactivity","main_activity"],
        "password":["password","passwd"],
    }
    terms=[]
    for k,v in mapping.items():
        if k in q: terms += v
    terms += keywords
    terms=list(dict.fromkeys(terms))[:12]
    matches=search_files(context.chat_data["apk_dir"],terms)
    if not matches:
        await update.message.reply_text("Exact match nahi mila. Different keywords ke sath poochain.")
        return
    base=Path(context.chat_data["apk_dir"])
    lines=["Possible relevant files:"]
    for score,p in matches[:8]:
        lines.append(f"• {p.relative_to(base)}")
    lines += ["", "Note: Decompiled APK structure may differ from the original source code."]
    await update.message.reply_text("\n".join(lines))

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    if "apk_dir" not in context.chat_data:
        await update.message.reply_text("Pehle APK upload karein, phir screenshot bhejein.")
        return
    await update.message.reply_text(
        "Screenshot received. Automatic visual-to-layout matching can be added with OCR/CV. "
        "For the current version, screenshot ke saath screen ka visible text ya element name message mein likhein, "
        "phir bot relevant decompiled files search karega."
    )

def main():
    if not TOKEN or not OWNER_CHAT_ID:
        raise RuntimeError("Set BOT_TOKEN and OWNER_CHAT_ID environment variables.")
    app=ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(MessageHandler(filters.Document.ALL,apk_handler))
    app.add_handler(MessageHandler(filters.PHOTO,photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,question))
    print("Bot running...")
    app.run_polling()

if __name__=="__main__":
    main()

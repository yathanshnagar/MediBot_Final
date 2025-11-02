# 🚀 How to Use Medical Llama Chat UI

## Step 1: Make sure the server is running

Open a PowerShell terminal and run:

```powershell
cd "c:\Users\yatha\OneDrive - The University of Sydney (Students)\Desktop\try again"
.\.venv\Scripts\Activate.ps1
cd medical_llama
ollama pull {model_name}
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 2: Open the Chat UI

Simply **double-click** on this file:
```
c:\Users\yatha\OneDrive - The University of Sydney (Students)\Desktop\try again\medical_llama\chat_ui.html
```

It will open in your default browser.

## Step 3: Start Chatting!

### Example Conversation:

**You:** "I have a fever"

**AI:** "I'd like to help you assess your fever. Can you tell me:
- How long have you had the fever?
- What's your temperature if you've measured it?
- Any other symptoms like cough, headache, or body aches?"

**You:** "I've had it for 2 days, temperature is 100.5°F, and I have a mild headache"

**AI:** *[Provides full assessment with severity classification, possible conditions, and recommendations]*

---

## What You'll See:

### Left Side - Chat Interface
- 💬 Natural conversation with the AI
- AI asks follow-up questions if needed
- Once enough info → full medical assessment

### Right Side - Live Medical Report
- 🟢 **Green (Self-Care)** - Minor condition, home management
- 🟡 **Yellow (Doctor Visit)** - See GP within 24-48h
- 🔴 **Red (Emergency)** - Call 999 immediately

The report updates in **real-time** as you chat!

---

## Features:

✅ **Conversational AI** - Asks clarifying questions naturally  
✅ **Color-coded severity** - Instant visual feedback  
✅ **Possible conditions** - Lists 2-3 likely diagnoses  
✅ **Self-care advice** - Medications + actions  
✅ **Real-time updates** - Medical report syncs with chat  
✅ **Safety disclaimers** - Always included  

---

## Troubleshooting:

**If chat doesn't work:**
1. Make sure the server is running (Step 1)
2. Check http://localhost:8000/health in browser - should show `{"status":"healthy"}`
3. Open browser console (F12) to see any errors

**If AI responses are slow:**
- First response takes 5-10 seconds (model loading)
- Subsequent responses are faster (~2-3 seconds)

---

## Example Test Cases:

### Self-Care (Green 🟢)
"I have a mild sore throat for 1 day, no fever"

### Doctor Visit (Yellow 🟡)
"I've had a persistent cough for 3 weeks with night sweats"

### Emergency (Red 🔴)
"I have severe chest pain radiating to my left arm"

---

Enjoy your Medical Llama! 🦙💊

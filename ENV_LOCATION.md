# ⚠️ Important: .env File Location

## 🎯 The .env file MUST be in the backend folder

```
lazyintern/
├── backend/
│   ├── .env          ← HERE! (REQUIRED)
│   ├── api/
│   ├── core/
│   └── ...
├── dashboard/
└── ...
```

## ❌ Common Mistake

If you see this error:
```
pydantic_core._pydantic_core.ValidationError: 2 validation errors for Settings
supabase_url
  Field required [type=missing, input_value={}, input_type=dict]
```

**Problem:** The .env file is in the wrong location or missing.

## ✅ Solution

### Option 1: Copy from root to backend
```bash
copy .env backend\.env
```

### Option 2: Create directly in backend
```bash
cd backend
copy .env.example .env
notepad .env  # Add your API keys
```

## 📝 Verify Location

Check that the file exists:
```bash
dir backend\.env
```

Should show:
```
 Directory of C:\Users\DIVYAM\Desktop\lazyintern\backend

.env
```

## 🔍 Why Backend Folder?

The Python code runs from the `backend` folder and looks for `.env` in the current directory:

```python
# backend/core/config.py
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",  # Looks in current directory
        env_file_encoding="utf-8"
    )
```

When you run:
```bash
cd backend
python -m uvicorn api.app:app
```

Python looks for `.env` in the `backend` folder, not the project root.

## ✅ Quick Fix

If you get the validation error, just run:
```bash
copy .env backend\.env
```

Then restart the backend:
```bash
cd backend
python -m uvicorn api.app:app --reload --port 8000
```

Should work now! 🎉

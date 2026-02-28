# Start Dashboard - Quick Guide

## 🚀 Quick Start (2 Minutes)

### Step 1: Make Sure Backend is Running

The dashboard needs the backend API to fetch data.

**Check if backend is running:**
```bash
# You should see this window open from start_here.bat
# If not, start it manually:
cd backend
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

**Test backend:**
Open http://localhost:8000/dashboard in browser
- Should see JSON data
- If error, backend isn't running

---

### Step 2: Install Dashboard Dependencies (First Time Only)

```bash
cd backend/dashboard
npm install
```

This takes ~1 minute and only needs to be done once.

---

### Step 3: Start Dashboard

```bash
cd backend/dashboard
npm run dev
```

You should see:
```
  ▲ Next.js 15.1.4
  - Local:        http://localhost:3000
  - Network:      http://192.168.x.x:3000

 ✓ Starting...
 ✓ Ready in 2.3s
```

---

### Step 4: Open Dashboard

Open browser to: **http://localhost:3000**

You should see:
- LazyIntern Dashboard header
- 4 panels with real data
- Auto-refreshing every 30 seconds

---

## 🎯 What You'll See

### First Time (Empty Database)
```
Discovery:    0 internships
Email:        0 emails
Outreach:     0 drafts
Performance:  0% reply rate
```

This is normal! Let the pipeline run for 1-2 hours.

### After 1 Hour
```
Discovery:    25-50 internships
Email:        10-20 emails
Outreach:     5-10 drafts
Performance:  Funnel showing drop-offs
```

### After 8 Hours (Full Day)
```
Discovery:    100-200 internships
Email:        30-50 emails
Outreach:     15 emails sent (limit)
Performance:  Complete funnel, maybe 1-2 replies
```

---

## 🔧 Troubleshooting

### Dashboard Shows "Connection Error"

**Problem:** Can't connect to backend API

**Fix:**
1. Check backend is running on port 8000
2. Open http://localhost:8000/dashboard
3. Should see JSON data
4. If not, restart backend:
   ```bash
   cd backend
   python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
   ```

---

### Dashboard Shows "Loading..." Forever

**Problem:** Backend API returning errors

**Fix:**
1. Check backend logs for errors
2. Check Supabase connection
3. Run diagnostic:
   ```bash
   cd backend
   python diagnose_supabase.py
   ```
4. Should see all ✓ checkmarks

---

### Dashboard Shows All Zeros

**Problem:** Database is empty (normal on first run)

**Fix:**
1. Let pipeline run for 1-2 hours
2. Check scheduler logs for activity
3. Verify pipeline is discovering internships:
   ```sql
   SELECT COUNT(*) FROM internships;
   ```
4. Should be > 0 after first cycle

---

### Port 3000 Already in Use

**Problem:** Another app using port 3000

**Fix:**
1. Stop other app using port 3000
2. Or change dashboard port:
   ```bash
   cd backend/dashboard
   PORT=3001 npm run dev
   ```
3. Open http://localhost:3001

---

## 📊 Understanding the Data

### Discovery Panel
- Shows internships discovered
- Scrape tier success rates
- Kill rate (how many filtered out)

### Email Panel
- Shows emails extracted
- Regex (free) vs Hunter (paid)
- Validation failures

### Outreach Panel
- Shows drafts generated
- Emails/SMS sent
- Daily limits

### Performance Panel
- Shows reply rates
- Complete funnel
- Drop-off analysis

---

## 🎨 Customization

### Change Refresh Rate

Edit `backend/dashboard/app/page.tsx`:
```typescript
// Line 28
const interval = setInterval(fetchData, 30000); // 30 seconds

// Change to 60 seconds:
const interval = setInterval(fetchData, 60000);
```

### Change Backend URL

Edit `backend/dashboard/app/page.tsx`:
```typescript
// Line 18
const response = await fetch("http://localhost:8000/dashboard");

// Change to production:
const response = await fetch("https://your-api.com/dashboard");
```

---

## 🚀 Production Deployment

### Option 1: Vercel (Recommended)

```bash
cd backend/dashboard
npm run build
vercel deploy
```

### Option 2: Docker

```bash
cd backend/dashboard
docker build -t lazyintern-dashboard .
docker run -p 3000:3000 lazyintern-dashboard
```

### Option 3: Static Export

```bash
cd backend/dashboard
npm run build
# Deploy the 'out' folder to any static host
```

---

## 📱 Mobile Access

Dashboard is fully responsive. Access from phone:

1. Find your computer's IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Open on phone: `http://192.168.x.x:3000`
3. Bookmark for easy access

---

## 🎯 Daily Workflow

### Morning (5 minutes)
1. Open dashboard: http://localhost:3000
2. Check overnight activity
3. Verify limits not reached
4. Review funnel drop-offs

### Evening (5 minutes)
1. Check daily totals
2. Review reply rates
3. Adjust scoring if needed
4. Plan for tomorrow

### Weekly (30 minutes)
1. Analyze trends
2. Identify best sources
3. Optimize scoring weights
4. Review reply patterns

---

## 🎉 You're All Set!

Dashboard is now running and showing real-time data. Keep it open in a browser tab and check periodically to monitor your pipeline! 🚀

---

## 📞 Quick Commands

```bash
# Start backend
cd backend && python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

# Start dashboard
cd backend/dashboard && npm run dev

# Test backend API
curl http://localhost:8000/dashboard

# Check database
cd backend && python diagnose_supabase.py
```

---

## 🔗 Useful Links

- Dashboard: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Supabase: https://supabase.com/dashboard

---

Happy monitoring! 📊

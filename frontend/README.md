# 🎨 AI Audit Agent - Premium Frontend

## Overview

Enterprise-grade, dark-themed frontend for the AI Audit Agent fraud detection system.

---

## ✨ Features

✅ **Dark Theme Design** - Professional, calm, enterprise-grade UI  
✅ **Glassmorphism** - Subtle blur effects and transparency  
✅ **Smooth Animations** - Fade-in, slide, scale transitions  
✅ **Drag & Drop Upload** - Intuitive file selection  
✅ **Real-time Backend Integration** - Connects to FastAPI server  
✅ **Responsive Layout** - Desktop-first, mobile-friendly  
✅ **Premium Typography** - Inter font family  
✅ **Visual Results** - Charts and graphs display  

---

## 🚀 Quick Start

### Prerequisites

1. **Backend Running**  
   ```bash
   # Make sure backend is running on port 8000
   cd ../
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Modern Browser**  
   - Chrome, Firefox, Safari, or Edge
   - JavaScript enabled

### Option 1: Open Directly (Recommended)

Simply open `index.html` in your browser:

```bash
# Windows
start index.html

# macOS
open index.html

# Linux
xdg-open index.html
```

### Option 2: Use Live Server (VSCode)

1. Install "Live Server" extension in VSCode
2. Right-click `index.html`
3. Select "Open with Live Server"

### Option 3: Python HTTP Server

```bash
# Python 3
python -m http.server 3000

# Then open http://localhost:3000
```

---

## 📁 File Structure

```
frontend/
├── index.html       # Main HTML structure
├── style.css        # Premium dark theme styles
├── script.js        # Backend integration & logic
└── README.md        # This file
```

---

## 🎯 Usage

### 1. Upload Document

- **Drag & drop** a file onto the upload zone, OR
- **Click** the upload zone to browse files
- **Supported formats:** PDF, DOCX, TXT
- **Max size:** 10MB

### 2. Optional Email

- Enter email address to receive report
- Leave blank for analysis only

### 3. Analyze

- Click **"Analyze Document"** button
- Wait for AI analysis (usually 5-30 seconds)

### 4. View Results

- **Risk Level** - Low, Medium, or High
- **Summary** - Executive overview
- **Fraud Flags** - Detailed indicators
- **Visualizations** - Charts and graphs
- **Recommendations** - Action items

---

## 🎨 Design System

### Color Palette

```css
Background:     #0A0A0A (Black)
Surface:        #1E1E1E (Charcoal)
Text Primary:   #FFFFFF (White)
Text Secondary: #A0A0A0 (Silver)
Accent:         #C0C0C0 (Silver gradient)

Risk Low:       #4CAF50 (Green)
Risk Medium:    #FF9800 (Orange)
Risk High:      #F44336 (Red)
```

### Typography

- **Font Family:** Inter (Google Fonts)
- **Weights:** 300, 400, 500, 600, 700

###Animations

- Page load: Fade-in (0.6s)
- Cards: Scale-in (0.6s)
- Buttons: Hover scale + glow
- Loading: Rotating rings
- Results: Staggered slide-in

---

## 🔧 Configuration

### Backend URL

The frontend connects to:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

To change the backend URL, edit `script.js`:

```javascript
// Line 8 in script.js
const API_BASE_URL = 'http://your-server:port';
```

---

## 🐛 Troubleshooting

### "Failed to analyze document"

**Cause:** Backend not running or unreachable

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Start backend if needed
cd ../
python -m uvicorn app.main:app --reload
```

### "CORS Error"

**Cause:** CORS not properly configured

**Solution:** Backend already has CORS enabled for all origins (`allow_origins=["*"]`)

### "Visualizations not loading"

**Cause:** Static files not served

**Solution:** Backend now serves `/visualizations` directory automatically

### "File upload failed"

**Possible causes:**
1. File too large (>10MB)
2. Invalid file type (not PDF/DOCX/TXT)
3. Backend not processing multipart/form-data

**Solution:** Check file meets requirements and backend is properly configured

---

## 📊 Browser Compatibility

✅ Chrome 90+  
✅ Firefox 88+  
✅ Safari 14+  
✅ Edge 90+  

**Required features:**
- CSS Grid
- CSS Backdrop Filter (for glassmorphism)
- Fetch API
- FormData API

---

## 🎭 Demo Workflow

**For Hackathon Presentation:**

1. **Open frontend** in browser
2. **Demonstrate drag & drop** - Upload sample PDF
3. **Show loading animation** - Professional waiting state
4. **Present results** - Risk level, flags, visualizations
5. **Highlight features:**
   - Dark premium theme
   - Smooth animations
   - Clear data presentation
   - Professional design

**Sample Documents:** Use files from `../examples/` or create test documents with suspicious financial transactions.

---

## 🚀 Deployment

### GitHub Pages

```bash
# Push frontend folder to gh-pages branch
git subtree push --prefix frontend origin gh-pages
```

### Netlify/Vercel

1. Connect repository
2. Set build directory to `frontend/`
3. No build command needed (static files)
4. Update `API_BASE_URL` to production backend

### With Backend

Serve frontend from FastAPI:

```python
# In app/main.py
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

---

## 🎨 Customization

### Change Theme Colors

Edit `style.css` variables:

```css
:root {
    --color-bg-primary: #0A0A0A;  /* Change background */
    --color-accent-silver: #C0C0C0;  /* Change accent */
}
```

### Add New Animations

```css
@keyframes yourAnimation {
    from { /* start state */ }
    to { /* end state */ }
}

.your-element {
    animation: yourAnimation 0.5s ease;
}
```

### Modify Layout

All sections are in `index.html`:
- Header: Lines 16-30
- Upload: Lines 33-98
- Loading: Lines 101-119
- Results: Lines 122-187
- Error: Lines 190-200

---

## 📚 Tech Stack

**Pure Frontend:**
- HTML5
- CSS3 (Grid, Flexbox, Animations)
- Vanilla JavaScript (ES6+)

**No frameworks or libraries** (except Google Fonts for typography)

**Why no frameworks?**
- Faster load times
- No build process
- Easy to understand and modify
- Perfect for demos and prototypes

---

## 💡 Best Practices Used

✅ **Semantic HTML** - Proper tags for accessibility  
✅ **CSS Variables** - Easy theme customization  
✅ **Mobile-first** - Responsive breakpoints  
✅ **Performance** - Optimized animations (CSS only)  
✅ **Error Handling** - Graceful API failure handling  
✅ **Code Comments** - Well-documented code  
✅ **Modular** - Separated concerns (HTML/CSS/JS)  

---

## 📝 Notes

- Frontend is **fully functional** with running backend
- Designed for **hackathon demos** and presentations
- **Enterprise-grade** UI suitable for production
- **No authentication** (as per requirements)
- Focus on **fraud detection**, not user management

---

## 🆘 Support

For issues:
1. Check browser console for errors
2. Verify backend is running: `http://localhost:8000/docs`
3. Test backend directly: `curl http://localhost:8000/health`
4. Check CORS is enabled in backend

---

**Built with:** Pure HTML, CSS, JavaScript  
**Design:** Dark premium theme with glassmorphism  
**Status:** ✅ Production-ready for hackathon demo  

**Open `index.html` and start analyzing! 🚀**

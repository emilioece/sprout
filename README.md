# Sprout

Team: Plant Power

Team Members: Salma Gitesatani, Jullianna Grace Facchin, Emilio Lopez, Ivan Esparza-Loera,  Eduardo Luis

> **Sprout** is a desktop application that helps non-technical gardeners create and manage a personal plant collection without feeling overwhelmed. Whether users already know their plants' needs or are just getting started, Sprout organizes care into a clear, actionable schedule.

---

## Overview

Managing plant care can quickly become overwhelming for non-technical gardeners. Sprout simplifies plant parenting by transforming care requirements into actionable schedules. Powered by **Gemini 3.5 Flash**, Sprout automatically generates customized watering intervals, light requirements, fertilizing routines, and repotting guides as soon as a plant is added.

---

## Features

* **Collection Management:** Catalog plants with nicknames, species, locations, and photos.
* **Automated Care Plans:** Real-time countdowns for watering, repotting, and fertilizing tasks.
* **Mobile QR Photo Sync:** Seamlessly upload plant photos directly from your smartphone to your desktop app over local Wi-Fi.
* **Symptom Diagnostic Guide:** Identify plant issues like yellowing leaves or drooping stems and get immediate care advice.
* **Light / Dark Theme:** Dynamically toggle between light and dark modes across the desktop UI.
* **Secure Authentication:** User registration and login powered by secure password hashing.

---

## Tech Stack

### **Frontend (Desktop)**
* **Python 3.10+ (only up to Python 3.13)**
* **Kivy:** Framework for cross-platform desktop UI design
* **Requests:** Synchronous HTTP communication with the API
* **QRCode & Pillow:** Rendering temporary QR codes on-screen for mobile pairing

### **Backend (API & AI)**
* **FastAPI:** Asynchronous RESTful API framework
* **Uvicorn:** ASGI server implementation
* **Google GenAI (Gemini 3.5 Flash):** AI-powered care advice and interval generation
* **Pydantic & Passlib:** Request validation and password hashing

### **Database & Storage**
* **SQLite:** Lightweight, embedded relational database (`sprout.db`)
* **SQLAlchemy:** Python Object-Relational Mapper (ORM)

---

## Installation & Setup

### **Prerequisites**
* Python **3.10+** installed on your system.
* Git installed.

### **1. Clone the Repository into Preferred IDE**
*Windows*

Terminal 1
```bash
git clone https://github.com/emilioece/sprout.git sprout
cd sprout
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env-example .env
```
Terminal 2
```bash
cd sprout
.venv\Scripts\activate
cd backend
uvicorn app.main:app --reload --host 0.0.0.0
```

Terminal 3
```bash
cd sprout
.venv\Scripts\activate
cd desktop-new\app
python main.py
```

*Mac*

Terminal 1
```bash
git clone https://github.com/emilioece/sprout.git sprout
cd sprout
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env-example .env
```
Terminal 2
```bash
cd sprout
source .venv/bin/activate
cd backend
uvicorn app.main:app --reload --host 0.0.0.0
```

Terminal 3
```bash
cd sprout
source .venv/bin/activate
cd desktop-new/app
python main.py
```


## How to Use

### 1. Account Setup & Authentication
* **Launch the App:** Open the desktop client. An authentication modal will appear automatically upon startup.
* **Register:** Switch to the **Register** tab, provide your email address and password, and create your account.
* **Sign In:** Enter your credentials in the **Login** tab to access your personalized collection.

---

### 2. Adding Plants to Your Collection
* **Start Creation:** Click **"Add your first plant"** on the empty state dashboard or click the **"+"** button in the navigation header.
* **Enter Details:** Input your plant's data:
  * **Nickname:**
  * **Upload Photo** 
  * **Location:**
* **Save:** Submit the form. Sprout automatically retrieves care guidelines (watering intervals, lighting requirements, and repotting recommendations) and adds the plant to your collection.

---

### 3. Tracking Care & Watering Tasks
* **Check Schedule:** Navigate to the **Dashboard** or **Schedule** tab to view upcoming and overdue care tasks.
* **Mark Watered:** Locate a plant that requires attention and click the **Water** button.
* **Automatic Recalculation:** The application updates the plant's `last_watered_at` timestamp, recalculates the remaining days until the next watering cycle, and displays a confirmation toast.

---

### 4. Uploading Plant Photos
You can add photos to your plant entries using two different methods:

* **Direct Disk Upload:**
  1. Open a plant's details view and select **Upload Photo**.
  2. Browse your local files for a `.jpg`, `.png`, or `.webp` image (up to 5 MB) and select it.
* **Mobile QR Sync:**
  1. Click **Upload via Phone** on a plant's menu.
  2. Scan the on-screen QR code using your mobile device's camera.
  3. Select a photo on your phone and upload it over your local Wi-Fi connection.
  4. The desktop app will automatically detect the file and refresh the plant photo.

---

### 5. Using the Symptom Guide & App Themes
* **Diagnosing Issues:** Open the **Symptoms** tab to view common plant health issues (such as yellowing leaves or drooping) alongside recommended treatments.
* **Theme Switching:** Click the **Dark Mode** / **Light Mode** toggle in the sidebar navigation to change visual themes.

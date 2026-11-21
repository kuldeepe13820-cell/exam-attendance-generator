# 📋 Exam Attendance Sheet Generator (Form EX-12)
### Professional Multi-Course Excel Workbook & A4 Landscape Print Ready Application

A lightweight, automated web application tailored for universities and academic institutions (such as Chandigarh University) to generate official examination theory attendance sheets (Form EX-12).

---

## 🌟 Key Features

1. **One-Click Switch: 7 UIDs vs 8 UIDs per Sheet**:
   - Easily switch between **7 UIDs / Sheet** and **8 UIDs / Sheet** with a single click right on the toolbar or sidebar.
   - Both formats feature **strictly equal box widths** across all 8 exam columns and dynamic row height budgeting for a 100% clean A4 Landscape 1-page fit.
   - Generates multi-course Excel `.xlsx` workbooks with independent pagination and repeating headers.

2. **Strict A4 Landscape Print Setup (Zero Spillover)**:
   - Configured with `fitToWidth = 1` and `fitToHeight = num_pages`.
   - Narrow margins (0.2 in / 5mm) and strict 180mm height budgeting guarantee that **every single attendance sheet prints on exactly 1 page**, with no table clipping and no blank trailing pages.

3. **Handwritten Exam Date & Subject Code Mode**:
   - Built-in **"✍️ Handwritten Mode"** formats examination dates as `Date: ____________` and subject code cells with dedicated space so invigilators and faculty can write dates and codes with a pen.

4. **Signature-Ready Student Rows**:
   - Formatted in standard Form EX-12 layout:
     * `* A/B No.` (Answer Book Number)
     * `OMR No.`
     * `Signature` (Enlarged row height for student physical signatures)
   - Invigilator signature grid and Centre Superintendent verification footer.

5. **Batch Multi-File & Bifurcation Sheet Upload**:
   - Drag & drop multiple Excel/CSV files simultaneously.
   - Automatically detects Course Name, Section, Semester, Subject Codes, and Student Roll Numbers (UIDs).

6. **Official Institutional Logo Integration**:
   - Embeds high-resolution university emblems (Chandigarh University official logo included) into both web print previews and downloadable Excel files.

---

## 🚀 Quick Start Guide

### 1. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/kuldeepe13820-cell/exam-attendance-generator.git
cd exam-attendance-generator
pip install -r requirements.txt
```

### 2. Run the Application
Start the Flask web server:
```bash
python3 app.py
# or using the shell script
./start.sh
```

Open your browser and navigate to:
👉 **[http://127.0.0.1:5001](http://127.0.0.1:5001)**

---

## 🌐 Network & Cloud Deployment

### Run on Local Wi-Fi Network
Because the server listens on `0.0.0.0:5001`, any device on the same local network (laptops, phones, lab PCs) can access the app by browsing to:
```
http://<YOUR_LOCAL_IP>:5001
```

### Deploy to Render / Railway (Free 24/7 Cloud Hosting)
1. Sign in to [Render.com](https://render.com) using GitHub.
2. Click **New Web Service** and select this repository (`exam-attendance-generator`).
3. Set the configuration:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. Click **Deploy Web Service** to receive a public URL accessible from anywhere.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).

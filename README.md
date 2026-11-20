# 📋 Exam Attendance Sheet Generator (Form EX-12)
### Course-Wise Multi-Sheet Excel & A4 Landscape Print Ready App

Yeh application Chandigarh University aur anya institutes ke examination attendance sheet (Form EX-12) format ke according design ki gayi hai.

---

## 🚀 App Kaise Open / Run Karein:
Server abhi **running** hai:
👉 **[http://127.0.0.1:5001](http://127.0.0.1:5001)**

Agar future me dobara start karna ho:
```bash
./start.sh
# ya fir
python3 app.py
```

---

## ✨ Features & Capabilities

1. **Course-Wise Multiple Sheets (Ek hi Excel File me)**:
   - Aap jitne chahein courses (jaise `CSE/IOT`, `CSE/AI`, `ECE`, `ME`) add kar sakte hain.
   - Jab aap **"Download Excel (.xlsx)"** button click karenge, toh ek hi Excel workbook download hogi jisme **har course ki alag-alag sheet (tab)** hogi!

2. **A4 Landscape Margin & Print Setup**:
   - Excel file me page setup pehle se **A4 Landscape** mode me set hai.
   - Narrow margins (0.25 inch) set hain taaki sabhi 8 exam dates and subjects bina cut hue 1 page width par fit aayein.
   - Automatic row page breaks hain taaki har 8 students ke baad agla page clean start ho.
   - Web App me bhi **"Print Sheets (A4)"** button hai jisse direct browser print dialog se A4 Landscape me perfect print out nikal sakte hain (`window.print()` with `@page { size: A4 landscape }`).

3. **Baccho ke Signature ke Liye Proper Space**:
   - Har student ke liye 3 rows hain:
     * `* A/B No.` (Answer Book Number)
     * `OMR No.`
     * `Signature` (Student Signature row ki height 26-28pt rakhi gayi hai taaki bacche araam se pen se sign kar sakein).

4. **Logo Option**:
   - Header me University / College Logo ka poora support hai.
   - Aap apna custom logo (PNG / JPG / WebP) upload kar sakte hain ya built-in Chandigarh University Emblem use kar sakte hain.
   - Logo web print preview me aur Excel (.xlsx) file ke header me auto-embed ho jata hai.

5. **1-Click Bifurcation Sheet & Excel Import**:
   - Folder me rakhi `24BCS_WD_CT-717_24CSP-304_Bifurcation_Sheet.xlsx` ko ek click me load karne ke liye button diya gaya hai.
   - Kisi bhi student list ya Excel/CSV ko drag-and-drop karke UIDs auto-extract ki ja sakti hain.

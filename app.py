import os
import json
import base64
from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename
import excel_generator

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64MB max for batch uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DEFAULT_LOGO = 'static/default_logo.png'

SAMPLE_DATA = {
    "settings": {
        "institute_name": "CHANDIGARH UNIVERSITY, GHARUAN (MOHALI)",
        "exam_title": "ATTENDANCE SHEET FOR THEORY (REGULAR) EXAMINATION MAY-JUNE 2024",
        "form_code": "EX-12",
        "centre_block": "B1 (Morning)",
        "shift_time": "9:30 AM - 12:30 PM",
        "show_logo": True,
        "logo_path": DEFAULT_LOGO,
        "logo_url": "/static/default_logo.png",
        "students_per_page": 8,
        "fill_empty_slots": True,
        "handwritten_mode": True
    },
    "courses": [
        {
            "id": "c_1",
            "course_name": "CSE/IOT",
            "semester": "5",
            "dates": ["", "", "", "", "", "", "", ""],
            "sub_codes": ["", "", "", "", "", "", "", ""],
            "students": [
                "22BCS1001", "22BCS1002", "22BCS1003", "22BCS1004",
                "22BCS1005", "22BCS1006", "22BCS1007", "22BCS1008"
            ]
        },
        {
            "id": "c_2",
            "course_name": "CSE/AI",
            "semester": "5",
            "dates": ["", "", "", "", "", "", "", ""],
            "sub_codes": ["", "", "", "", "", "", "", ""],
            "students": [
                "22AIM1001", "22AIM1002", "22AIM1003", "22AIM1004",
                "22AIM1005", "22AIM1006", "22AIM1007", "22AIM1008",
                "22AIM1009", "22AIM1010", "22AIM1011", "22AIM1012",
                "22AIM1013", "22AIM1014", "22AIM1015", "22AIM1016"
            ]
        },
        {
            "id": "c_3",
            "course_name": "ECE",
            "semester": "4",
            "dates": ["", "", "", "", "", "", "", ""],
            "sub_codes": ["", "", "", "", "", "", "", ""],
            "students": [
                "22ECE2001", "22ECE2002", "22ECE2003", "22ECE2004",
                "22ECE2005", "22ECE2006", "22ECE2007", "22ECE2008"
            ]
        }
    ]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sample_data', methods=['GET'])
def get_sample_data():
    return jsonify(SAMPLE_DATA)

@app.route('/api/load_local_bifurcation', methods=['GET'])
def load_local_bifurcation():
    target_file = '24BCS_WD_CT-717_24CSP-304_Bifurcation_Sheet.xlsx'
    if os.path.exists(target_file):
        with open(target_file, 'rb') as f:
            bytes_data = f.read()
        courses = excel_generator.parse_uploaded_spreadsheet(bytes_data, target_file)
        if courses:
            for i, c in enumerate(courses):
                c['id'] = f"bifur_{i+1}"
                c['dates'] = ["", "", "", "", "", "", "", ""]
                c['sub_codes'] = ["", "", "", "", "", "", "", ""]
            return jsonify({
                "success": True,
                "filename": target_file,
                "courses": courses
            })
    return jsonify({"success": False, "error": "Bifurcation sheet file not found on disk."}), 404

@app.route('/api/upload_multiple_files', methods=['POST'])
def upload_multiple_files():
    """
    Accepts multiple uploaded files (Excel / CSV) and parses each file into course sheets.
    """
    files = request.files.getlist('files')
    if not files:
        files = request.files.getlist('file')
    
    if not files or len(files) == 0:
        return jsonify({"success": False, "error": "No files uploaded."}), 400

    mode = request.form.get('mode', 'replace')  # 'replace' or 'append'
    parsed_courses = []
    file_summaries = []

    for f_idx, file in enumerate(files):
        if not file or file.filename == '':
            continue
        filename = secure_filename(file.filename)
        file_bytes = file.read()
        try:
            courses = excel_generator.parse_uploaded_spreadsheet(file_bytes, filename)
            for c_idx, c in enumerate(courses):
                c['id'] = f"course_{f_idx+1}_{c_idx+1}_{os.urandom(3).hex()}"
                if not c.get('dates') or len(c['dates']) < 8:
                    c['dates'] = ["", "", "", "", "", "", "", ""]
                if not c.get('sub_codes') or len(c['sub_codes']) < 8:
                    c['sub_codes'] = ["", "", "", "", "", "", "", ""]
                parsed_courses.append(c)
                file_summaries.append({
                    "filename": filename,
                    "course_name": c['course_name'],
                    "students_count": len(c['students'])
                })
        except Exception as err:
            print(f"Error parsing {filename}: {err}")

    if not parsed_courses:
        return jsonify({
            "success": False,
            "error": "No student UIDs found in uploaded files. Please ensure files contain UID or Roll No column."
        }), 400

    return jsonify({
        "success": True,
        "mode": mode,
        "files_processed": len(files),
        "total_courses": len(parsed_courses),
        "total_students": sum(len(c['students']) for c in parsed_courses),
        "courses": parsed_courses,
        "file_summaries": file_summaries
    })

@app.route('/api/upload_file', methods=['POST'])
def upload_file():
    # Reuse multiple files endpoint logic
    return upload_multiple_files()

@app.route('/api/upload_logo', methods=['POST'])
def upload_logo():
    if 'logo' not in request.files:
        return jsonify({"success": False, "error": "No logo file provided"}), 400
    file = request.files['logo']
    if file.filename == '':
        return jsonify({"success": False, "error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
    rel_path = f"static/uploads/{filename}"

    return jsonify({
        "success": True,
        "logo_path": rel_path,
        "logo_url": f"/static/uploads/{filename}"
    })

@app.route('/api/generate_excel', methods=['POST'])
def generate_excel():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Missing payload"}), 400

        excel_stream = excel_generator.generate_attendance_workbook(data)
        
        form = data.get('settings', {}).get('form_code', 'EX-12')
        courses_count = len(data.get('courses', []))
        download_name = f"Exam_Attendance_Sheets_{form}_{courses_count}_Courses.xlsx"

        return send_file(
            excel_stream,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=download_name
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting Exam Attendance Sheet App on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)

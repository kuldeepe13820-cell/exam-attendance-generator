import os
import io
import re
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.pagebreak import Break
from openpyxl.drawing.image import Image as XLImage
from PIL import Image as PILImage

# Border definitions
thin_side = Side(border_style='thin', color='000000')
medium_side = Side(border_style='medium', color='000000')

table_border = Border(top=thin_side, left=thin_side, right=thin_side, bottom=thin_side)

def apply_range_style(ws, cell_range, border=None, font=None, alignment=None, fill=None):
    """Apply styling across a merged or contiguous range of cells."""
    for row in ws[cell_range]:
        for cell in row:
            if border is not None:
                cell.border = border
            if font is not None:
                cell.font = font
            if alignment is not None:
                cell.alignment = alignment
            if fill is not None:
                cell.fill = fill

def sanitize_sheet_title(title, existing_titles):
    """Ensure sheet title is valid in Excel and unique (max 31 chars, no forbidden chars)."""
    clean = re.sub(r'[\\/*?\[\]:]', '-', str(title)).strip()
    if not clean:
        clean = "Course"
    clean = clean[:28]
    base = clean
    counter = 1
    while clean.lower() in [t.lower() for t in existing_titles]:
        clean = f"{base[:25]}_{counter}"
        counter += 1
    return clean

def build_course_sheet(ws, course_data, global_settings, logo_path=None):
    """
    Builds a complete, print-ready course attendance sheet in ws.
    Includes A4 Landscape page setup, exact EX-12 header, student signature rows,
    invigilator block, and superintendent footer.
    Row heights are strictly budgeted to guarantee 1 single page per 8 students!
    """
    students = course_data.get('students', [])
    students_per_page = int(global_settings.get('students_per_page', 8))
    fill_empty = global_settings.get('fill_empty_slots', True)

    total_students = len(students)
    if total_students == 0:
        num_pages = 1
    else:
        num_pages = (total_students + students_per_page - 1) // students_per_page

    # 1. Page Setup for A4 Landscape - EXACT 1 PAGE FIT
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_A4  # 9
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = num_pages
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    
    # Margins in inches (narrow margins for A4 landscape: 0.2 inch)
    ws.page_margins.left = 0.2
    ws.page_margins.right = 0.2
    ws.page_margins.top = 0.2
    ws.page_margins.bottom = 0.2
    ws.page_margins.header = 0.1
    ws.page_margins.footer = 0.1
    ws.print_options.horizontalCentered = True
    ws.print_options.verticalCentered = True

    # 2. Column Dimensions (A to J = 10 columns)
    ws.column_dimensions['A'].width = 15.5  # UID No.
    ws.column_dimensions['B'].width = 13.0  # Semester / Label
    for c in ['C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']:
        ws.column_dimensions[c].width = 13.0  # 8 exam dates & codes

    # Extract global settings
    institute_name = global_settings.get('institute_name', 'CHANDIGARH UNIVERSITY, GHARUAN (MOHALI)').strip()
    exam_title = global_settings.get('exam_title', 'ATTENDANCE SHEET FOR THEORY (REGULAR) EXAMINATION MAY-JUNE 2024').strip()
    form_code = global_settings.get('form_code', 'EX-12').strip()
    centre_block = global_settings.get('centre_block', 'B1 (Morning)').strip()
    shift_time = global_settings.get('shift_time', '9:30 AM - 12:30 PM').strip()
    show_logo = global_settings.get('show_logo', True)
    handwritten_mode = global_settings.get('handwritten_mode', True)

    course_name = course_data.get('course_name', 'CSE/IOT').strip()
    semester = str(course_data.get('semester', '5')).strip()
    
    # 8 exam columns
    dates = course_data.get('dates', [])
    while len(dates) < 8:
        dates.append('')
    dates = dates[:8]

    sub_codes = course_data.get('sub_codes', [])
    while len(sub_codes) < 8:
        sub_codes.append('')
    sub_codes = sub_codes[:8]

    current_row = 1
    header_fill = PatternFill(start_color='F3F4F6', end_color='F3F4F6', fill_type='solid')

    for page_idx in range(num_pages):
        R = current_row

        if page_idx > 0:
            ws.row_breaks.append(Break(id=R - 1))

        # --- Row R: Form Code (EX-12) & Top padding (14 pt) ---
        ws.row_dimensions[R].height = 14
        cell_ex = ws.cell(R, 10, form_code)
        cell_ex.font = Font(name='Arial', size=10, bold=True)
        cell_ex.alignment = Alignment(horizontal='right', vertical='center')

        # Add Logo on top left if enabled (scale nicely for Chandigarh University rectangular emblem)
        if show_logo and logo_path and os.path.exists(logo_path):
            try:
                xl_img = XLImage(logo_path)
                xl_img.height = 36
                xl_img.width = 65
                ws.add_image(xl_img, f'A{R}')
            except Exception as e:
                print(f"Warning: could not add logo to Excel sheet: {e}")

        # --- Row R+1: University Name (18 pt) ---
        R_uni = R + 1
        ws.row_dimensions[R_uni].height = 18
        ws.merge_cells(f'A{R_uni}:J{R_uni}')
        cell_uni = ws.cell(R_uni, 1, institute_name)
        cell_uni.font = Font(name='Arial', size=12.5, bold=True, color='8B0000' if 'CHANDIGARH' in institute_name else '111827')
        cell_uni.alignment = Alignment(horizontal='center', vertical='center')

        # --- Row R+2: Exam Title (14 pt) ---
        R_exam = R + 2
        ws.row_dimensions[R_exam].height = 14
        ws.merge_cells(f'A{R_exam}:J{R_exam}')
        cell_title = ws.cell(R_exam, 1, exam_title)
        cell_title.font = Font(name='Arial', size=9.5, bold=True)
        cell_title.alignment = Alignment(horizontal='center', vertical='center')

        # --- Row R+3: Course/Branch | Centre/Block | Shift Time (14 pt) ---
        R_info = R + 3
        ws.row_dimensions[R_info].height = 14
        
        ws.merge_cells(f'A{R_info}:C{R_info}')
        c_branch = ws.cell(R_info, 1, f"Course/Branch: {course_name}")
        c_branch.font = Font(name='Arial', size=9.0, bold=True)
        c_branch.alignment = Alignment(horizontal='left', vertical='center')

        ws.merge_cells(f'D{R_info}:G{R_info}')
        c_centre = ws.cell(R_info, 4, f"Centre/Block No: {centre_block}")
        c_centre.font = Font(name='Arial', size=9.0, bold=True)
        c_centre.alignment = Alignment(horizontal='center', vertical='center')

        ws.merge_cells(f'H{R_info}:J{R_info}')
        c_shift = ws.cell(R_info, 8, f"Shift Time: {shift_time}")
        c_shift.font = Font(name='Arial', size=9.0, bold=True)
        c_shift.alignment = Alignment(horizontal='right', vertical='center')

        # --- Row R+4: Table Header 1 (UID No., Semester, Dates) (18 pt) ---
        R_h1 = R + 4
        ws.row_dimensions[R_h1].height = 18
        
        R_h2 = R + 5
        ws.row_dimensions[R_h2].height = 22

        ws.merge_cells(f'A{R_h1}:A{R_h2}')
        c_uid = ws.cell(R_h1, 1, 'UID No.')
        c_uid.font = Font(name='Arial', size=9.5, bold=True)
        c_uid.alignment = Alignment(horizontal='center', vertical='center')

        c_sem = ws.cell(R_h1, 2, f"Semester: {semester}")
        c_sem.font = Font(name='Arial', size=8.5, bold=True)
        c_sem.alignment = Alignment(horizontal='center', vertical='center')

        # Dates in columns C to J
        for idx in range(8):
            col_num = 3 + idx
            d_val = dates[idx].strip() if idx < len(dates) else ''
            
            if handwritten_mode or not d_val:
                d_text = "Date: ____________"
            else:
                d_text = f"Date: {d_val}"

            c_date = ws.cell(R_h1, col_num, d_text)
            c_date.font = Font(name='Arial', size=8.0, bold=True)
            c_date.alignment = Alignment(horizontal='center', vertical='center')

        # --- Row R+5: Table Header 2 (Sub Codes) (22 pt) ---
        ws.cell(R_h2, 2, '')
        for idx in range(8):
            col_num = 3 + idx
            sc_val = sub_codes[idx].strip() if idx < len(sub_codes) else ''
            
            if handwritten_mode or not sc_val:
                sc_text = "Sub Code:\n"
            else:
                sc_text = f"Sub Code:\n{sc_val}"

            c_sc = ws.cell(R_h2, col_num, sc_text)
            c_sc.font = Font(name='Arial', size=8.0, bold=True)
            c_sc.alignment = Alignment(horizontal='center', vertical='top', wrap_text=True)

        apply_range_style(ws, f'A{R_h1}:J{R_h2}', border=table_border, fill=header_fill)

        # --- Students (8 students per page block) ---
        page_start_student = page_idx * students_per_page
        for s_idx in range(students_per_page):
            student_global_idx = page_start_student + s_idx
            student_uid = ""
            if student_global_idx < total_students:
                student_uid = str(students[student_global_idx]).strip()
            elif not fill_empty:
                break

            sr = R_h2 + 1 + (s_idx * 3)
            ws.row_dimensions[sr].height = 13.0
            ws.row_dimensions[sr + 1].height = 13.0
            ws.row_dimensions[sr + 2].height = 21.0  # signature row

            # Merge UID column across the 3 rows
            ws.merge_cells(f'A{sr}:A{sr + 2}')
            uid_cell = ws.cell(sr, 1, student_uid)
            uid_cell.font = Font(name='Arial', size=9.0, bold=True)
            uid_cell.alignment = Alignment(horizontal='center', vertical='center')

            # Row 1: * A/B No.
            c_ab = ws.cell(sr, 2, '* A/B No.')
            c_ab.font = Font(name='Arial', size=8.0)
            c_ab.alignment = Alignment(horizontal='left', vertical='center')

            # Row 2: OMR No.
            c_omr = ws.cell(sr + 1, 2, 'OMR No.')
            c_omr.font = Font(name='Arial', size=8.0)
            c_omr.alignment = Alignment(horizontal='left', vertical='center')

            # Row 3: Signature
            c_sig = ws.cell(sr + 2, 2, 'Signature')
            c_sig.font = Font(name='Arial', size=8.5, bold=True)
            c_sig.alignment = Alignment(horizontal='left', vertical='center')

            apply_range_style(ws, f'A{sr}:J{sr + 2}', border=table_border)

        # --- Footer 1: Invigilator's Signature & Emp.ID (20 pt) ---
        actual_students_drawn = students_per_page if fill_empty else min(students_per_page, max(1, total_students - page_start_student))
        R_inv = R_h2 + 1 + (actual_students_drawn * 3)
        ws.row_dimensions[R_inv].height = 20.0

        ws.merge_cells(f'A{R_inv}:B{R_inv}')
        c_inv = ws.cell(R_inv, 1, "Invigilator's Signature & Emp.ID :-")
        c_inv.font = Font(name='Arial', size=8.5, bold=True)
        c_inv.alignment = Alignment(horizontal='left', vertical='center')

        for idx in range(8):
            col_num = 3 + idx
            ws.cell(R_inv, col_num, '')

        apply_range_style(ws, f'A{R_inv}:J{R_inv}', border=table_border, fill=header_fill)

        # --- Footer 2: Note & Centre Supdt. Sign (14 pt) ---
        R_sup = R_inv + 1
        ws.row_dimensions[R_sup].height = 14.0

        ws.merge_cells(f'A{R_sup}:D{R_sup}')
        c_note = ws.cell(R_sup, 1, "Note: *A/B stands for Answer Book No.")
        c_note.font = Font(name='Arial', size=7.5, italic=True)
        c_note.alignment = Alignment(horizontal='left', vertical='center')

        ws.merge_cells(f'E{R_sup}:I{R_sup}')
        c_sup = ws.cell(R_sup, 5, "Centre Supdt. Name & Sign.: _____________________________________________")
        c_sup.font = Font(name='Arial', size=8.0)
        c_sup.alignment = Alignment(horizontal='center', vertical='center')

        c_empid = ws.cell(R_sup, 10, "Emp. ID__________")
        c_empid.font = Font(name='Arial', size=8.0)
        c_empid.alignment = Alignment(horizontal='right', vertical='center')

        current_row = R_sup + 2

    return ws

def generate_attendance_workbook(data):
    wb = openpyxl.Workbook()
    default_ws = wb.active
    
    settings = data.get('settings', {})
    courses = data.get('courses', [])
    logo_path = settings.get('logo_path', 'static/default_logo.png')

    if not courses:
        courses = [{
            "course_name": "Course-1",
            "semester": "1",
            "dates": [],
            "sub_codes": [],
            "students": []
        }]

    existing_titles = []
    first_sheet = True

    for course_data in courses:
        raw_name = course_data.get('course_name', 'Course')
        sheet_title = sanitize_sheet_title(raw_name, existing_titles)
        existing_titles.append(sheet_title)

        if first_sheet:
            ws = default_ws
            ws.title = sheet_title
            first_sheet = False
        else:
            ws = wb.create_sheet(title=sheet_title)

        build_course_sheet(ws, course_data, settings, logo_path=logo_path)

    output_stream = io.BytesIO()
    wb.save(output_stream)
    output_stream.seek(0)
    return output_stream

def clean_name_from_filename(filename):
    """Derive clean course/section name from filename."""
    base = os.path.splitext(filename)[0]
    base = re.sub(r'(_Bifurcation_Sheet|_Attendance_Sheet|_Student_List|_List)', '', base, flags=re.IGNORECASE)
    base = base.replace('__', '_').strip('_ ')
    return base[:25] if base else "Course"

def parse_uploaded_spreadsheet(file_bytes, filename):
    courses_found = []
    filename_lower = filename.lower()
    fallback_name = clean_name_from_filename(filename)

    if filename_lower.endswith('.csv'):
        import csv
        content = file_bytes.decode('utf-8', errors='ignore')
        reader = csv.reader(content.splitlines())
        uids = []
        for row in reader:
            for cell in row:
                c = cell.strip()
                if re.match(r'^[0-9]{2}[A-Za-z]{2,5}[0-9]{3,6}$', c) or (len(c) >= 5 and c.isalnum() and any(ch.isdigit() for ch in c)):
                    uids.append(c)
        
        if uids:
            # Preserve order and deduplicate
            seen = set()
            clean_uids = [x for x in uids if not (x in seen or seen.add(x))]
            courses_found.append({
                "course_name": fallback_name,
                "semester": "5",
                "dates": ["", "", "", "", "", "", "", ""],
                "sub_codes": ["", "", "", "", "", "", "", ""],
                "students": clean_uids
            })

    elif filename_lower.endswith(('.xlsx', '.xlsm', '.xls')):
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        
        for sheetname in wb.sheetnames:
            ws = wb[sheetname]
            course_name = ""
            semester = "5"
            uids = []
            sub_code = ""

            # 1. Check Row 1 for Bifurcation Header details
            r1_val = str(ws.cell(1, 1).value or '')
            if 'Bifurcation' in r1_val or 'Internal Marks' in r1_val or 'Section:' in r1_val:
                parts = [p.strip() for p in r1_val.split('|')]
                for p in parts:
                    if 'Sem:' in p:
                        semester = p.replace('Sem:', '').strip()
                    if 'Section:' in p:
                        course_name = p.replace('Section:', '').strip()
                    elif 'Program:' in p and not course_name:
                        course_name = p.replace('Program:', '').strip()
                    if '(' in p and ')' in p:
                        match = re.search(r'\((.*?)\)', p)
                        if match:
                            sub_code = match.group(1).strip()

            # 2. If course_name not extracted from Row 1, check sheetname or filename
            if not course_name:
                sheet_lower = sheetname.strip().lower()
                if sheet_lower not in ['sheet1', 'sheet 1', 'bifurcation sheet', 'bifurcation']:
                    course_name = sheetname.strip()
                else:
                    course_name = fallback_name

            # 3. Locate UID column
            uid_col = 2  # default Col B
            header_row = 1
            found_header = False
            for r in range(1, min(10, ws.max_row + 1)):
                for c in range(1, min(15, ws.max_column + 1)):
                    val = str(ws.cell(r, c).value or '').strip().upper()
                    if val in ['UID', 'UID NO', 'UID NO.', 'ROLL NO', 'ROLL NO.', 'STUDENT ID', 'REG NO']:
                        uid_col = c
                        header_row = r
                        found_header = True
                        break
                if found_header:
                    break

            # 4. Extract UIDs
            for r in range(header_row + 1, ws.max_row + 1):
                val = ws.cell(r, uid_col).value
                if val is not None:
                    s_val = str(val).strip()
                    if s_val and s_val.lower() not in ['uid', 'roll no', 'total', 'average', 'none', 's.no.', 's.no']:
                        uids.append(s_val)

            # If still empty, scan columns for student ID patterns
            if not uids:
                for c in range(1, min(5, ws.max_column + 1)):
                    col_uids = []
                    for r in range(1, ws.max_row + 1):
                        cell_v = str(ws.cell(r, c).value or '').strip()
                        if re.match(r'^[0-9]{2}[A-Za-z]{2,5}[0-9]{3,6}$', cell_v):
                            col_uids.append(cell_v)
                    if len(col_uids) > len(uids):
                        uids = col_uids

            seen = set()
            clean_uids = [x for x in uids if not (x in seen or seen.add(x))]

            if clean_uids:
                sub_codes = [sub_code] if sub_code else [""]
                while len(sub_codes) < 8:
                    sub_codes.append("")
                courses_found.append({
                    "course_name": course_name[:25],
                    "semester": semester,
                    "dates": ["", "", "", "", "", "", "", ""],
                    "sub_codes": sub_codes,
                    "students": clean_uids
                })

    return courses_found

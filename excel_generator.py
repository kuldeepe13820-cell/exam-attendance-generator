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

def natural_sort_key(s):
    """Sort strings with numbers naturally (e.g. CT-2 before CT-10, 24BCS1001 before 24BCS1002)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s or ''))]

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
        clean = f"{base[:24]}_{counter}"
        counter += 1
    return clean

def build_course_sheet(ws, course_data, global_settings, logo_path=None):
    """
    Builds a complete, print-ready course attendance sheet in ws.
    Includes A4 Landscape page setup, exact EX-12 header, student signature rows,
    invigilator block, and superintendent footer.
    Default: 7 UIDs per sheet with IDENTICAL box widths and generous signature space!
    """
    students = course_data.get('students', [])
    students_per_page = int(global_settings.get('students_per_page', 7))
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
    
    # Margins in inches (narrow 0.15 in margins for maximum printable width)
    ws.page_margins.left = 0.15
    ws.page_margins.right = 0.15
    ws.page_margins.top = 0.15
    ws.page_margins.bottom = 0.15
    ws.page_margins.header = 0.1
    ws.page_margins.footer = 0.1
    ws.print_options.horizontalCentered = True
    ws.print_options.verticalCentered = True

    # 2. Column Dimensions - EXPANDED EQUAL BOX WIDTHS FOR ALL 8 EXAM COLUMNS
    ws.column_dimensions['A'].width = 14.5  # UID No.
    ws.column_dimensions['B'].width = 12.0  # Semester / Label
    # Identical width for all 8 exam columns C to J - WIDER (14.2 each!)
    for c in ['C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']:
        ws.column_dimensions[c].width = 14.2

    # Extract global settings
    institute_name = global_settings.get('institute_name', 'CHANDIGARH UNIVERSITY, GHARUAN (MOHALI)').strip()
    exam_title = global_settings.get('exam_title', 'ATTENDANCE SHEET FOR THEORY (REGULAR) EXAMINATION MAY-JUNE 2024').strip()
    form_code = global_settings.get('form_code', 'EX-12').strip()
    centre_block = global_settings.get('centre_block', 'B1 (Morning)').strip()
    shift_time = global_settings.get('shift_time', '9:30 AM - 12:30 PM').strip()
    show_logo = global_settings.get('show_logo', True)
    handwritten_mode = global_settings.get('handwritten_mode', True)

    course_name = course_data.get('course_name', 'CSE').strip()
    section = course_data.get('section', '').strip()
    semester = str(course_data.get('semester', '5')).strip()

    # Build Header Course line with Section if available
    if section and section.lower() not in course_name.lower():
        course_display = f"{course_name} (Section: {section})"
    else:
        course_display = course_name
    
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

        # --- Row R: Form Code (EX-12) & Top padding (11 pt compact) ---
        ws.row_dimensions[R].height = 11
        cell_ex = ws.cell(R, 10, form_code)
        cell_ex.font = Font(name='Arial', size=9, bold=True)
        cell_ex.alignment = Alignment(horizontal='right', vertical='center')

        # Add Logo on top left if enabled (compact 25 pt height)
        if show_logo and logo_path and os.path.exists(logo_path):
            try:
                xl_img = XLImage(logo_path)
                xl_img.height = 25
                xl_img.width = 50
                ws.add_image(xl_img, f'A{R}')
            except Exception as e:
                print(f"Warning: could not add logo to Excel sheet: {e}")

        # --- Row R+1: University Name (15 pt compact) ---
        R_uni = R + 1
        ws.row_dimensions[R_uni].height = 15
        ws.merge_cells(f'A{R_uni}:J{R_uni}')
        cell_uni = ws.cell(R_uni, 1, institute_name)
        cell_uni.font = Font(name='Arial', size=11.0, bold=True, color='8B0000' if 'CHANDIGARH' in institute_name else '111827')
        cell_uni.alignment = Alignment(horizontal='center', vertical='center')

        # --- Row R+2: Exam Title (12 pt compact) ---
        R_exam = R + 2
        ws.row_dimensions[R_exam].height = 12
        ws.merge_cells(f'A{R_exam}:J{R_exam}')
        cell_title = ws.cell(R_exam, 1, exam_title)
        cell_title.font = Font(name='Arial', size=8.5, bold=True)
        cell_title.alignment = Alignment(horizontal='center', vertical='center')

        # --- Row R+3: Course/Branch | Centre/Block | Shift Time (12 pt compact) ---
        R_info = R + 3
        ws.row_dimensions[R_info].height = 12
        
        ws.merge_cells(f'A{R_info}:C{R_info}')
        c_branch = ws.cell(R_info, 1, f"Course/Branch: {course_display}")
        c_branch.font = Font(name='Arial', size=8.5, bold=True)
        c_branch.alignment = Alignment(horizontal='left', vertical='center')

        ws.merge_cells(f'D{R_info}:G{R_info}')
        c_centre = ws.cell(R_info, 4, f"Centre/Block No: {centre_block}")
        c_centre.font = Font(name='Arial', size=8.5, bold=True)
        c_centre.alignment = Alignment(horizontal='center', vertical='center')

        ws.merge_cells(f'H{R_info}:J{R_info}')
        c_shift = ws.cell(R_info, 8, f"Shift Time: {shift_time}")
        c_shift.font = Font(name='Arial', size=8.5, bold=True)
        c_shift.alignment = Alignment(horizontal='right', vertical='center')

        # --- Row R+4: Table Header 1 (UID No., Semester, Dates) (17 pt) ---
        R_h1 = R + 4
        ws.row_dimensions[R_h1].height = 17
        
        R_h2 = R + 5
        ws.row_dimensions[R_h2].height = 22

        ws.merge_cells(f'A{R_h1}:A{R_h2}')
        c_uid = ws.cell(R_h1, 1, 'UID No.')
        c_uid.font = Font(name='Arial', size=9.0, bold=True)
        c_uid.alignment = Alignment(horizontal='center', vertical='center')

        c_sem = ws.cell(R_h1, 2, f"Semester: {semester}")
        c_sem.font = Font(name='Arial', size=8.0, bold=True)
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

        # --- Students (Configurable 7 or 8 UIDs per sheet page - EXPANDED HEIGHTS) ---
        if students_per_page == 7:
            row_ab_h = 15.0
            row_omr_h = 15.0
            row_sig_h = 27.0  # Extra roomy signature box for 7 UIDs!
            inv_h = 23.0
        elif students_per_page == 8:
            row_ab_h = 14.0
            row_omr_h = 14.0
            row_sig_h = 22.5  # Taller signature box for 8 UIDs!
            inv_h = 21.0
        else:
            row_ab_h = 13.5
            row_omr_h = 13.5
            row_sig_h = max(18.0, 26.0 - (students_per_page - 7) * 2)
            inv_h = 20.0

        page_start_student = page_idx * students_per_page
        for s_idx in range(students_per_page):
            student_global_idx = page_start_student + s_idx
            student_uid = ""
            if student_global_idx < total_students:
                student_uid = str(students[student_global_idx]).strip()
            elif not fill_empty:
                break

            sr = R_h2 + 1 + (s_idx * 3)
            ws.row_dimensions[sr].height = row_ab_h
            ws.row_dimensions[sr + 1].height = row_omr_h
            ws.row_dimensions[sr + 2].height = row_sig_h

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

        # --- Footer 1: Invigilator's Signature & Emp.ID ---
        actual_students_drawn = students_per_page if fill_empty else min(students_per_page, max(1, total_students - page_start_student))
        R_inv = R_h2 + 1 + (actual_students_drawn * 3)
        ws.row_dimensions[R_inv].height = inv_h

        ws.merge_cells(f'A{R_inv}:B{R_inv}')
        c_inv = ws.cell(R_inv, 1, "Invigilator's Signature & Emp.ID :-")
        c_inv.font = Font(name='Arial', size=8.5, bold=True)
        c_inv.alignment = Alignment(horizontal='left', vertical='center')

        for idx in range(8):
            col_num = 3 + idx
            ws.cell(R_inv, col_num, '')

        apply_range_style(ws, f'A{R_inv}:J{R_inv}', border=table_border, fill=header_fill)

        # --- Footer 2: Note & Centre Supdt. Sign (16 pt) ---
        R_sup = R_inv + 1
        ws.row_dimensions[R_sup].height = 16.0

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
    """
    Generates a full openpyxl Workbook with multiple sheets course-wise and section-wise.
    """
    wb = openpyxl.Workbook()
    default_ws = wb.active
    
    settings = data.get('settings', {})
    courses = data.get('courses', [])
    logo_path = settings.get('logo_path', 'static/default_logo.png')

    if not courses:
        courses = [{
            "course_name": "Course-1",
            "section": "Sec-1",
            "semester": "1",
            "dates": [],
            "sub_codes": [],
            "students": []
        }]

    existing_titles = []
    first_sheet = True

    for course_data in courses:
        raw_name = course_data.get('course_name', 'Course')
        section = course_data.get('section', '')
        
        # Build concise tab name (e.g. CSE_CT-717 (G1) or CT-717)
        if section:
            sec_clean = re.sub(r'24BCS_WD_', '', section).strip()
            course_short = raw_name.split('-')[0].strip()
            if course_short.lower() not in sec_clean.lower():
                tab_base = f"{course_short}_{sec_clean}"
            else:
                tab_base = sec_clean
        else:
            tab_base = raw_name

        sheet_title = sanitize_sheet_title(tab_base, existing_titles)
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

def clean_section_value(val):
    """Cleans and standardizes extracted section strings."""
    if val is None:
        return ''
    s = str(val).strip()
    s = re.sub(r'^(?:section|sec|class|batch)\s*[:=\-–—]?\s*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'[\r\n\t]+', ' ', s).strip()
    if s.lower() in ['none', 'null', 'undefined', 'nan', 'na', '-', '--', 'nil', 'n/a', '']:
        return ''
    return s

def is_section_label(val):
    """Checks whether a cell text represents a section label."""
    if not val:
        return False
    s = str(val).strip().lower()
    s_clean = re.sub(r'[:=\-–—\.]+$', '', s).strip()
    return s_clean in [
        'section', 'sec', 'class', 'class/sec', 'class / sec',
        'section name', 'sec name', 'section no', 'section no.',
        'sec no', 'sec id', 'sec_id', 'branch/sec', 'branch / sec',
        'batch/sec', 'student section'
    ]

def normalize_col_header(val):
    """Strips whitespace, hyphens, underscores and slashes for flexible column matching."""
    if not val:
        return ''
    return re.sub(r'[\s_.\-/]+', '', str(val)).upper()

def is_uid_col_header(val):
    """Checks whether a table column header represents student UID / Roll No."""
    if not val:
        return False
    s = normalize_col_header(val)
    return s in ['UID', 'UIDNO', 'ROLLNO', 'ROLL', 'STUDENTID', 'REGNO', 'REGISTRATIONNO', 'ENROLLMENTNO', 'CANDIDATEID']

def is_section_col_header(val):
    """Checks whether a table column header represents student Section (e.g. StudentSection, Section, Sec)."""
    if not val:
        return False
    s = normalize_col_header(val)
    if s in [
        'SECTION', 'SEC', 'STUDENTSECTION', 'SECTIONNAME', 'SECTIONNO',
        'SECTIONID', 'CLASSSECTION', 'BRANCHSECTION', 'BATCHSECTION',
        'CLASS', 'SECT', 'SECTION_NAME'
    ]:
        return True
    if any(k in s for k in ['STUDENTSECTION', 'SECTIONNAME', 'SECTIONNO']):
        return True
    if re.search(r'\b(sec|section)\b', str(val), re.IGNORECASE) and not re.search(r'\b(semester|sem|second|secondary)\b', str(val), re.IGNORECASE):
        return True
    return False

def is_group_col_header(val):
    """Checks whether a table column header represents Group / Batch (e.g. studentGroup, Group)."""
    if not val:
        return False
    s = normalize_col_header(val)
    return s in [
        'GROUP', 'GRP', 'BATCH', 'STUDENTGROUP', 'GROUPNAME',
        'LABGROUP', 'LABBATCH', 'SUBGROUP'
    ] or any(k in s for k in ['STUDENTGROUP', 'GROUPNAME'])

def is_sub_code_col_header(val):
    """Checks whether a table column header represents Subject Code (e.g. SubjectCode)."""
    if not val:
        return False
    s = normalize_col_header(val)
    return s in ['SUBJECTCODE', 'SUBCODE', 'PAPERCODE', 'COURSECODE']

def is_sub_name_col_header(val):
    """Checks whether a table column header represents Subject Name (e.g. SubjectName)."""
    if not val:
        return False
    s = normalize_col_header(val)
    return s in ['SUBJECTNAME', 'SUBNAME', 'PAPERNAME', 'SUBJECTTITLE', 'SUBJECT', 'PAPER']

def is_course_col_header(val):
    """Checks whether a table column header represents Course / Program (e.g. ProgramName, Course)."""
    if not val:
        return False
    s = normalize_col_header(val)
    return s in ['PROGRAMNAME', 'COURSENAME', 'BRANCHNAME', 'PROGRAM', 'COURSE', 'BRANCH', 'DEGREE', 'DISCIPLINE']

def is_status_col_header(val):
    """Checks whether a table column header represents Student Status / Eligibility (e.g. STATUS)."""
    if not val:
        return False
    s = normalize_col_header(val)
    return s in ['STATUS', 'STUDENTSTATUS', 'EXAMSTATUS', 'ELIGIBILITY']

def is_remarks_col_header(val):
    """Checks whether a table column header represents Remarks (e.g. Remarks)."""
    if not val:
        return False
    s = normalize_col_header(val)
    return s in ['REMARKS', 'REMARK', 'NOTE', 'REASON']

def is_suspension_col_header(val):
    """Checks whether a table column header represents Suspension Status."""
    if not val:
        return False
    s = normalize_col_header(val)
    return s in ['SUSPENSIONSTATUS', 'SUSPENDEDSTATUS', 'SUSPENSION']

def normalize_course_name(val):
    """Normalizes long degree names like 'Bachelor of Engineering (Computer Science and Engineering)' to 'CSE'."""
    if not val:
        return 'CSE'
    s = str(val).strip().upper()
    if 'COMPUTER SCIENCE' in s or 'CSE' in s or 'CS201' in s or 'BCS' in s or 'SOFTWARE' in s:
        if 'ARTIFICIAL INTELLIGENCE' in s or 'AIML' in s or 'AI' in s or 'CS202' in s:
            return 'CSE-AI'
        if 'IOT' in s or 'INTERNET OF THINGS' in s:
            return 'CSE-IOT'
        if 'DATA SCIENCE' in s:
            return 'CSE-DS'
        return 'CSE'
    if 'ELECTRONICS' in s or 'ECE' in s:
        return 'ECE'
    if 'ELECTRICAL' in s or 'EE' in s:
        return 'EE'
    if 'MECHANICAL' in s or 'ME' in s:
        return 'ME'
    if 'CIVIL' in s or 'CE' in s:
        return 'CE'
    if 'BCA' in s:
        return 'BCA'
    if 'MCA' in s:
        return 'MCA'
    clean = str(val).strip()
    return clean if len(clean) <= 15 else 'CSE'

def is_valid_student_uid(uid_str):
    """Validates that a string is a real student UID and not a header/footer line."""
    if not uid_str:
        return False
    s = str(uid_str).strip()
    if len(s) < 2 or len(s) > 40:
        return False
    s_lower = s.lower()
    invalid_keywords = [
        'uid', 'roll no', 'total', 'average', 'none', 's.no.', 's.no',
        'serial no', 'signature', 'invigilator', 'emp.id', 'centre',
        'center', 'supdt', 'superintendent', 'sub code', 'semester',
        'answer book', 'date:', 'marks', 'max marks', 'grand total',
        'sub total', 'theory', 'practical', 'candidate name', 'student name'
    ]
    if any(k in s_lower for k in invalid_keywords):
        return False
    return True

def extract_section_from_text(text):
    """Extracts a section code from any text snippet (header, sheet name, filename)."""
    if not text:
        return ''
    t = str(text).strip()
    
    # 1. Label pattern: e.g. 'Section: 24BCS_WD_CT-717', 'Sec: CT-717', 'Class/Sec: CT-701'
    m_lbl = re.search(r'(?:section|sec|class(?:\s*/\s*sec)?)\s*[:=\-–—]\s*([A-Za-z0-9_\-]+(?:\s+[A-Za-z0-9_\-]+)*)', t, re.IGNORECASE)
    if m_lbl:
        val = m_lbl.group(1).strip()
        val = re.split(r'\s*(?:\||,|;|\n|\t|Group|Grp|Sem|Subject|Paper|Course|Branch)\b', val, flags=re.IGNORECASE)[0].strip()
        val = clean_section_value(val)
        if val and val.lower() not in ['name', 'no', 'id', 'select', 'choose']:
            return val

    # Remove content in parentheses if it's subject code like (24CSP-304)
    t_clean = re.sub(r'\([A-Za-z0-9_\-]+\)', '', t).strip()

    # 2. Full CU style section: 24BCS_WD_CT-717 or 24BCS-WD-CT-717 or 24BCS_CT-717
    m_full = re.search(r'(?<![A-Za-z0-9])(\d{2}[A-Za-z]{3,4}(?:[-_][A-Za-z]{2,4})?[-_]CT[-_]?\d{2,4})(?![A-Za-z0-9])', t_clean, re.IGNORECASE)
    if m_full:
        return m_full.group(1).strip()

    # 3. CT section: CT-717, CT_717, CT717
    m_ct = re.search(r'(?<![A-Za-z0-9])(CT[-_]?\d{2,4})(?![A-Za-z0-9])', t_clean, re.IGNORECASE)
    if m_ct:
        return m_ct.group(1).replace('_', '-').upper().strip()

    # 4. Sec-A, Section-B, Sec-1, Section-12, Section A, Sec 1
    m_sec = re.search(r'(?<![A-Za-z0-9])(Sec(?:tion)?[-_ ]?(?:[A-Za-z]|\d{1,4}))(?![A-Za-z0-9])', t_clean, re.IGNORECASE)
    if m_sec:
        return m_sec.group(1).replace('_', '-').strip()

    # 5. Branch + Sec: e.g. CSE-717, CSE-A, CSE_B
    m_br = re.search(r'(?<![A-Za-z0-9])([A-Za-z]{2,5}[-_](?:[A-Za-z]|\d{2,4}))(?![A-Za-z0-9])', t_clean)
    if m_br:
        val = m_br.group(1).replace('_', '-').strip()
        # Avoid subject codes like 24CSP-304
        if not re.search(r'^\d{2}[A-Z]{3}-\d+$', val, re.IGNORECASE):
            return val

    return ''

def clean_name_from_filename(filename):
    """Derive clean course/section name from filename."""
    base = os.path.splitext(filename)[0]
    base = re.sub(r'(_Bifurcation_Sheet|_Attendance_Sheet|_Student_List|_List)', '', base, flags=re.IGNORECASE)
    base = base.replace('__', '_').strip('_ ')
    return base if base else "Course"

def parse_single_file(file_bytes, filename):
    """
    Parses an individual Excel or CSV file into rich student entries with:
    - Subject Name & Subject Code
    - Course / Program
    - Section (auto-detected across headers, adjacent cells, table columns, sheet names, & filenames)
    - Group (e.g. Group 1, Group 2, G1, G2, etc.)
    - Semester
    - Student UID and Name
    """
    entries = []
    filename_lower = filename.lower()
    fn_clean = clean_name_from_filename(filename)

    # 1. Guess section from filename
    fn_section = extract_section_from_text(fn_clean) or extract_section_from_text(filename)

    # 2. Guess subject code from filename (e.g. 24CSP-304, 22CST-201)
    fn_code_match = re.search(r'(?<![A-Za-z0-9])([A-Za-z0-9]{2,5}[-_][A-Za-z0-9]{2,5})(?![A-Za-z0-9])', fn_clean)
    fn_sub_code = fn_code_match.group(1).strip() if fn_code_match else ''

    # 3. Guess group from filename if present (e.g. Group-1, Grp1, G1, G2)
    fn_grp_match = re.search(r'\b(Group[-_ ]?[A-Za-z0-9]+|Grp[-_ ]?[A-Za-z0-9]+|G[12])\b', fn_clean, re.IGNORECASE)
    fn_group = fn_grp_match.group(1).strip() if fn_grp_match else ''

    # 4. Guess course from filename
    fn_course = "CSE" if any(k in fn_clean.upper() for k in ['BCS', 'CSE', 'CS201']) else \
                "CSE-AI" if 'AIM' in fn_clean.upper() else \
                "ECE" if 'ECE' in fn_clean.upper() else \
                "BCA" if 'BCA' in fn_clean.upper() else \
                "MCA" if 'MCA' in fn_clean.upper() else \
                fn_clean

    if filename_lower.endswith(('.csv', '.tsv', '.txt')):
        import csv
        content = file_bytes.decode('utf-8', errors='ignore')
        lines = content.splitlines()
        delim = '\t' if (lines and '\t' in lines[0]) else ','
        reader = list(csv.reader(lines, delimiter=delim))
        
        uid_col = 0
        name_col = None
        group_col = None
        course_col = None
        sec_col = None
        sub_code_col = None
        sub_name_col = None
        status_col = None
        remarks_col = None
        suspension_col = None
        start_row = 0
        csv_section = fn_section
        csv_course = fn_course
        csv_sem = '5'
        csv_subject = ''
        csv_sub_code = fn_sub_code

        # Scan first 10 rows for header metadata and adjacent cells
        for r_idx, row in enumerate(reader[:10]):
            for c_idx, cell in enumerate(row):
                c_str = str(cell).strip()
                sec_match = extract_section_from_text(c_str)
                if sec_match and not csv_section:
                    csv_section = sec_match
                if is_section_label(c_str) and c_idx + 1 < len(row):
                    adj = clean_section_value(row[c_idx + 1])
                    if adj and not csv_section:
                        csv_section = adj
                if any(k in c_str.upper() for k in ['SEM:', 'SEMESTER:']):
                    csv_sem = re.sub(r'Sem(?:ester)?\s*[:=\-–—]?\s*', '', c_str, flags=re.IGNORECASE).strip()
                if any(k in c_str.upper() for k in ['PROGRAM:', 'COURSE:', 'BRANCH:']):
                    csv_course = re.sub(r'(Program|Course|Branch)\s*[:=\-–—]?\s*', '', c_str, flags=re.IGNORECASE).strip()

            # Column header check
            has_uid = False
            for c_idx, cell in enumerate(row):
                if is_uid_col_header(cell):
                    uid_col = c_idx
                    start_row = r_idx + 1
                    has_uid = True
                elif normalize_col_header(cell) in ['NAME', 'STUDENTNAME', 'CANDIDATENAME']:
                    name_col = c_idx
                elif is_group_col_header(cell):
                    group_col = c_idx
                elif is_section_col_header(cell):
                    sec_col = c_idx
                elif is_sub_code_col_header(cell):
                    sub_code_col = c_idx
                elif is_sub_name_col_header(cell):
                    sub_name_col = c_idx
                elif is_course_col_header(cell):
                    course_col = c_idx
                elif is_status_col_header(cell):
                    status_col = c_idx
                elif is_remarks_col_header(cell):
                    remarks_col = c_idx
                elif is_suspension_col_header(cell):
                    suspension_col = c_idx
            if has_uid:
                break

        for row in reader[start_row:]:
            if len(row) <= uid_col:
                continue
            uid = str(row[uid_col]).strip()
            if not is_valid_student_uid(uid):
                continue
            
            raw_c = str(row[course_col]).strip() if course_col is not None and len(row) > course_col else csv_course
            c_name = normalize_course_name(raw_c) if raw_c else fn_course
            
            row_sec = ''
            if sec_col is not None and len(row) > sec_col:
                row_sec = clean_section_value(row[sec_col])
            s_name = row_sec or csv_section or fn_section or 'Sec-1'
            
            g_name = str(row[group_col]).strip() if group_col is not None and len(row) > group_col else fn_group
            row_code = str(row[sub_code_col]).strip() if sub_code_col is not None and len(row) > sub_code_col else (fn_sub_code or csv_sub_code)
            row_sname = str(row[sub_name_col]).strip() if sub_name_col is not None and len(row) > sub_name_col else ''
            
            # Clean code out of title if title is e.g. "Database Management System (25CSH-204)"
            if row_sname and '(' in row_sname and ')' in row_sname:
                m = re.match(r'^(.*?)\s*\(([A-Za-z0-9_\-]+)\)$', row_sname)
                if m:
                    row_sname = m.group(1).strip()
                    if not row_code:
                        row_code = m.group(2).strip()

            s_name_student = str(row[name_col]).strip() if name_col is not None and len(row) > name_col else ''
            row_status = str(row[status_col]).strip() if status_col is not None and len(row) > status_col else 'Clear'
            row_remarks = str(row[remarks_col]).strip() if remarks_col is not None and len(row) > remarks_col else ''
            row_suspension = str(row[suspension_col]).strip() if suspension_col is not None and len(row) > suspension_col else ''

            if row_sname and row_code:
                subj_disp = f"{row_sname} ({row_code})"
            elif row_sname:
                subj_disp = row_sname
            elif row_code:
                subj_disp = row_code
            else:
                subj_disp = c_name or "General"

            entries.append({
                'course': c_name or fn_course,
                'section': s_name,
                'semester': csv_sem,
                'subject_title': row_sname or row_code or '',
                'sub_code': row_code,
                'subject': subj_disp,
                'group': g_name,
                'uid': uid,
                'name': s_name_student,
                'status': row_status,
                'remarks': row_remarks,
                'suspension': row_suspension
            })

    elif filename_lower.endswith(('.xlsx', '.xlsm', '.xls')):
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        
        for sheetname in wb.sheetnames:
            ws = wb[sheetname]
            course_name = ""
            section_name = ""
            semester = "5"
            subject_title = ""
            sub_code = fn_sub_code
            sheet_group = fn_group

            # Check sheetname for section or group hints
            sh_sec = extract_section_from_text(sheetname)
            if sh_sec:
                section_name = sh_sec
            sh_grp_match = re.search(r'\b(Group[-_ ]?[A-Za-z0-9]+|Grp[-_ ]?[A-Za-z0-9]+|G[12])\b', sheetname, re.IGNORECASE)
            if sh_grp_match:
                sheet_group = sh_grp_match.group(1).strip()

            # Inspect first 10 rows across columns 1 to 25 for header metadata & adjacent cells
            for r_top in range(1, min(11, ws.max_row + 1)):
                for c_top in range(1, min(26, ws.max_column + 1)):
                    cell_val = str(ws.cell(r_top, c_top).value or '').strip()
                    if not cell_val:
                        continue

                    # 1. Check for pipe-delimited header line: e.g. "Bifurcation Sheet | ... | Section: 24BCS_WD_CT-717"
                    if '|' in cell_val:
                        parts = [p.strip() for p in cell_val.split('|')]
                        # Priority 1: Check parts for explicit Section label
                        for p in parts:
                            if re.search(r'\bsec(?:tion)?\s*[:=\-–—]', p, re.IGNORECASE):
                                sec_from_p = re.sub(r'.*?\bsec(?:tion)?\s*[:=\-–—]\s*', '', p, flags=re.IGNORECASE).strip()
                                sec_clean = clean_section_value(sec_from_p)
                                if sec_clean:
                                    section_name = sec_clean
                                    break

                        # Process remaining metadata in parts
                        for p in parts:
                            if any(k in p.lower() for k in ['sem:', 'semester:']):
                                semester = re.sub(r'Sem(?:ester)?\s*[:=\-–—]?\s*', '', p, flags=re.IGNORECASE).strip()
                            elif any(k in p.lower() for k in ['program:', 'branch:', 'course:']):
                                p_val = re.sub(r'(Program|Branch|Course)\s*[:=\-–—]?\s*', '', p, flags=re.IGNORECASE).strip()
                                course_name = normalize_course_name(p_val)
                            elif '(' in p and ')' in p:
                                m = re.match(r'^(.*?)\s*\((.*?)\)', p)
                                if m:
                                    subject_title = m.group(1).strip()
                                    sub_code = m.group(2).strip()
                                else:
                                    subject_title = p
                            elif not subject_title and not any(k in p.lower() for k in ['internal marks', 'bifurcation sheet', 'marks']):
                                subject_title = p

                    # 2. Check individual cell for Section
                    if not section_name:
                        direct_sec = extract_section_from_text(cell_val)
                        if direct_sec:
                            section_name = direct_sec

                    # 3. Check adjacent cells (e.g. Cell A2="Section:", Cell B2="24BCS_WD_CT-717")
                    if is_section_label(cell_val) and not section_name:
                        adj_val = str(ws.cell(r_top, c_top + 1).value or '').strip()
                        if not adj_val and c_top + 2 <= ws.max_column:
                            adj_val = str(ws.cell(r_top, c_top + 2).value or '').strip()
                        adj_sec = clean_section_value(adj_val)
                        if adj_sec:
                            section_name = adj_sec

                    # 4. Check for Course/Branch in cell
                    if not course_name and any(k in cell_val.upper() for k in ['PROGRAM:', 'COURSE:', 'BRANCH:']):
                        c_val = re.sub(r'(Program|Course|Branch)\s*[:=\-–—]?\s*', '', cell_val, flags=re.IGNORECASE).strip()
                        course_name = normalize_course_name(c_val)

                    # 5. Check for Semester in cell
                    if any(k in cell_val.upper() for k in ['SEM:', 'SEMESTER:']):
                        s_val = re.sub(r'Sem(?:ester)?\s*[:=\-–—]?\s*', '', cell_val, flags=re.IGNORECASE).strip()
                        if s_val and len(s_val) <= 4:
                            semester = s_val

            # Fallbacks for section
            if not section_name:
                section_name = fn_section or (sheetname if sheetname.lower() not in ['sheet1', 'sheet 1', 'bifurcation sheet'] else 'Sec-1')

            if not course_name:
                course_name = fn_course

            # Build subject display
            if subject_title and sub_code:
                subject_display = f"{subject_title} ({sub_code})"
            elif subject_title:
                subject_display = subject_title
            elif sub_code:
                subject_display = sub_code
            else:
                subject_display = f"{course_name} Subject"

            # Check table headers for row-level columns
            uid_col = 2  # default Col B
            name_col = None
            sec_col = None
            group_col = None
            course_col = None
            sub_code_col = None
            sub_name_col = None
            status_col = None
            remarks_col = None
            suspension_col = None
            header_row = 1

            for r in range(1, min(15, ws.max_row + 1)):
                has_uid = False
                for c in range(1, min(30, ws.max_column + 1)):
                    cell_obj = ws.cell(r, c)
                    val = str(cell_obj.value or '').strip()
                    if is_uid_col_header(val):
                        uid_col = c
                        header_row = r
                        has_uid = True
                    elif normalize_col_header(val) in ['NAME', 'STUDENTNAME', 'CANDIDATENAME']:
                        name_col = c
                    elif is_group_col_header(val):
                        group_col = c
                    elif is_section_col_header(val):
                        sec_col = c
                    elif is_sub_code_col_header(val):
                        sub_code_col = c
                    elif is_sub_name_col_header(val):
                        sub_name_col = c
                    elif is_course_col_header(val):
                        course_col = c
                    elif is_status_col_header(val):
                        status_col = c
                    elif is_remarks_col_header(val):
                        remarks_col = c
                    elif is_suspension_col_header(val):
                        suspension_col = c
                if has_uid:
                    break

            # Extract student rows
            for r in range(header_row + 1, ws.max_row + 1):
                val = ws.cell(r, uid_col).value
                if val is not None:
                    s_val = str(val).strip()
                    if is_valid_student_uid(s_val):
                        if sec_col:
                            raw_sec = ws.cell(r, sec_col).value
                            row_sec = clean_section_value(raw_sec) or section_name
                        else:
                            row_sec = section_name

                        row_grp = str(ws.cell(r, group_col).value or '').strip() if group_col else sheet_group
                        
                        raw_course = str(ws.cell(r, course_col).value or '').strip() if course_col else ''
                        row_course = normalize_course_name(raw_course) if raw_course else course_name

                        row_name = str(ws.cell(r, name_col).value or '').strip() if name_col else ''
                        row_code = str(ws.cell(r, sub_code_col).value or '').strip() if sub_code_col else sub_code
                        row_sname = str(ws.cell(r, sub_name_col).value or '').strip() if sub_name_col else subject_title

                        if row_sname and '(' in row_sname and ')' in row_sname:
                            m = re.match(r'^(.*?)\s*\(([A-Za-z0-9_\-]+)\)$', row_sname)
                            if m:
                                row_sname = m.group(1).strip()
                                if not row_code:
                                    row_code = m.group(2).strip()

                        row_status = str(ws.cell(r, status_col).value or '').strip() if status_col else 'Clear'
                        row_remarks = str(ws.cell(r, remarks_col).value or '').strip() if remarks_col else ''
                        row_suspension = str(ws.cell(r, suspension_col).value or '').strip() if suspension_col else ''

                        if row_sname and row_code:
                            subj_disp = f"{row_sname} ({row_code})"
                        elif row_sname:
                            subj_disp = row_sname
                        elif row_code:
                            subj_disp = row_code
                        else:
                            subj_disp = subject_display

                        entries.append({
                            'course': row_course or course_name,
                            'section': row_sec or section_name or 'Sec-1',
                            'semester': semester,
                            'subject_title': row_sname or subject_title,
                            'sub_code': row_code or sub_code,
                            'subject': subj_disp,
                            'group': row_grp,
                            'uid': s_val,
                            'name': row_name,
                            'status': row_status,
                            'remarks': row_remarks,
                            'suspension': row_suspension
                        })

    return entries

    return entries


def parse_pasted_text(text):
    """
    Parses raw tabular text (TSV or CSV, copied from Excel / ERP / webpage).
    Supports all headers including UID, SubjectCode, SubjectName, ProgramName,
    StudentSection, studentGroup, STATUS, Remarks, suspensionstatus.
    """
    if not text or not str(text).strip():
        return []

    lines = [l.strip() for l in str(text).strip().splitlines() if l.strip()]
    if not lines:
        return []

    # Detect delimiter: tab first, then comma
    first_line = lines[0]
    delim = '\t' if '\t' in first_line else ','

    import csv
    reader = list(csv.reader(lines, delimiter=delim))
    if not reader:
        return []

    csv_bytes = '\n'.join([delim.join(r) for r in reader]).encode('utf-8')
    return parse_single_file(csv_bytes, 'Pasted_Data.csv')


def extract_metadata_from_entries(entries):
    """
    Extracts available subjects, sections, groups, and eligibility statuses
    from parsed student entries.
    """
    if not entries:
        return {
            'subjects': [],
            'sections': [],
            'groups': ['All Groups (Whole Section)'],
            'statuses': ['All Students'],
            'status_counts': {},
            'detained_count': 0,
            'clear_count': 0,
            'has_status_info': False,
            'has_explicit_groups': False,
            'total_students': 0
        }

    subjects_dict = {}
    sections_dict = {}
    groups_set = set()
    status_counts = {}
    detained_count = 0
    clear_count = 0

    for e in entries:
        subj = e.get('subject') or 'General'
        sec = e.get('section') or 'Sec-1'
        grp = e.get('group', '').strip()
        stat = (e.get('status') or 'Clear').strip()

        if subj not in subjects_dict:
            subjects_dict[subj] = {
                'id': subj,
                'title': e.get('subject_title') or subj,
                'code': e.get('sub_code') or '',
                'course': e.get('course') or '',
                'count': 0
            }
        subjects_dict[subj]['count'] += 1

        if sec not in sections_dict:
            sections_dict[sec] = {
                'id': sec,
                'subject': subj,
                'count': 0
            }
        sections_dict[sec]['count'] += 1

        if grp:
            groups_set.add(grp)

        if stat:
            norm_s = stat.title()
            status_counts[norm_s] = status_counts.get(norm_s, 0) + 1
            if norm_s.lower() in ['detained', 'detain']:
                detained_count += 1
            else:
                clear_count += 1

    subjects = list(subjects_dict.values())
    subjects.sort(key=lambda x: natural_sort_key(x['id']))

    sections = list(sections_dict.keys())
    sections.sort(key=natural_sort_key)

    explicit_groups = list(groups_set)
    explicit_groups.sort(key=natural_sort_key)

    if explicit_groups:
        groups = ['All Groups (Whole Section)'] + explicit_groups
    else:
        groups = [
            'All Groups (Whole Section)',
            'Group 1 (Batch 1)',
            'Group 2 (Batch 2)'
        ]

    statuses = ['All Students']
    if detained_count > 0:
        statuses = [
            'Clear / Eligible Only (Exclude Detained)',
            'All Students (Including Detained)',
            'Detained Only'
        ]

    return {
        'subjects': subjects,
        'sections': sections,
        'groups': groups,
        'statuses': statuses,
        'status_counts': status_counts,
        'detained_count': detained_count,
        'clear_count': clear_count,
        'has_status_info': bool(detained_count > 0),
        'has_explicit_groups': bool(explicit_groups),
        'total_students': len(entries)
    }


def filter_and_build_course(entries, subject_sel='all', section_sel='all', group_sel='all', status_sel='all'):
    """
    Filters student entries by Subject, Section, Group, and Student Eligibility Status.
    Returns a single Course Sheet object ready to render or download.
    """
    if not entries:
        return None

    filtered = []
    for e in entries:
        subj = e.get('subject') or ''
        sec = e.get('section') or ''
        stat = (e.get('status') or 'Clear').strip().lower()

        if subject_sel and subject_sel != 'all' and subj != subject_sel:
            continue
        if section_sel and section_sel != 'all' and sec != section_sel:
            continue

        # Status filtering
        if status_sel and status_sel != 'all':
            s_low = status_sel.lower()
            if 'clear' in s_low or 'eligible' in s_low:
                if stat in ['detained', 'detain', 'suspended']:
                    continue
            elif 'detained' in s_low:
                if stat not in ['detained', 'detain']:
                    continue

        filtered.append(e)

    # Sort students by UID naturally
    filtered.sort(key=lambda x: natural_sort_key(x.get('uid', '')))

    # Apply group filtering
    if group_sel and group_sel != 'all' and 'all groups' not in group_sel.lower():
        has_explicit = any(e.get('group') for e in filtered)
        if has_explicit:
            filtered = [e for e in filtered if e.get('group', '').lower() == group_sel.lower()]
        else:
            # Smart 50/50 split for lab batches
            half = (len(filtered) + 1) // 2
            if '1' in group_sel.lower() or 'g1' in group_sel.lower() or 'batch 1' in group_sel.lower():
                filtered = filtered[:half]
            elif '2' in group_sel.lower() or 'g2' in group_sel.lower() or 'batch 2' in group_sel.lower():
                filtered = filtered[half:]

    if not filtered:
        return None

    first = filtered[0]
    course_name = first.get('course') or 'CSE'
    base_section = section_sel if (section_sel and section_sel != 'all') else (first.get('section') or 'Sec-1')
    
    if group_sel and group_sel != 'all' and 'all groups' not in group_sel.lower():
        grp_short = 'G1' if ('1' in group_sel.lower() or 'g1' in group_sel.lower()) else \
                    ('G2' if ('2' in group_sel.lower() or 'g2' in group_sel.lower()) else group_sel)
        section_display = f"{base_section} ({grp_short})"
    else:
        section_display = base_section

    subj_title = first.get('subject_title') or ''
    if subj_title and subj_title.lower() not in course_name.lower():
        course_display = f"{course_name} - {subj_title}"
    else:
        course_display = course_name

    sub_code = first.get('sub_code') or ''
    semester = first.get('semester') or '5'
    uids = [e['uid'] for e in filtered]

    sub_codes = [sub_code] if sub_code else ['']
    while len(sub_codes) < 8:
        sub_codes.append('')

    return {
        'id': f"course_{os.urandom(3).hex()}",
        'course_name': course_display,
        'section': section_display,
        'semester': semester,
        'dates': ['', '', '', '', '', '', '', ''],
        'sub_codes': sub_codes[:8],
        'students': uids
    }

def group_and_sort_student_entries(entries, status_sel='all'):
    """
    Takes all raw student entries from multiple files/sheets.
    Groups them by (Course, Section).
    Sorts Course-wise (alphabetical/natural), Section-wise (natural), and Student UID-wise (natural).
    Supports optional status_sel ('clear', 'detained', 'all').
    Returns list of ready Course Sheet objects.
    """
    if not entries:
        return []

    # Optional status filter
    if status_sel and status_sel != 'all':
        s_low = status_sel.lower()
        if 'clear' in s_low or 'eligible' in s_low:
            entries = [e for e in entries if (e.get('status') or 'Clear').lower() not in ['detained', 'detain', 'suspended']]
        elif 'detained' in s_low:
            entries = [e for e in entries if (e.get('status') or '').lower() in ['detained', 'detain']]

    grouped = {}
    for item in entries:
        c_raw = (item.get('course') or 'Course').strip()
        s_raw = clean_section_value(item.get('section')) or 'Sec-1'
        
        if 'CS201' in c_raw:
            course = "CSE"
        elif 'CS202' in c_raw:
            course = "CSE-AI"
        elif any(k in c_raw.upper() for k in ['BCS', 'CSE']):
            course = "CSE"
        elif 'AIM' in c_raw.upper():
            course = "CSE-AI"
        elif 'ECE' in c_raw.upper():
            course = "ECE"
        else:
            course = c_raw

        section = s_raw
        key = (course, section)
        
        subj_title = item.get('subject_title') or ''
        sub_code = item.get('sub_code') or ''

        if key not in grouped:
            c_name_full = f"{course} - {subj_title}" if subj_title and subj_title.lower() not in course.lower() else course
            grouped[key] = {
                'course_name': c_name_full,
                'section': section,
                'semester': item.get('semester', '5'),
                'sub_codes': [sub_code] if sub_code else [],
                'students_set': set(),
                'students': []
            }
        
        uid = str(item['uid']).strip()
        if uid and uid not in grouped[key]['students_set']:
            grouped[key]['students_set'].add(uid)
            grouped[key]['students'].append(uid)

    course_list = list(grouped.values())

    # 1. Sort Courses naturally, then Sections naturally!
    course_list.sort(key=lambda x: (
        natural_sort_key(x['course_name']),
        natural_sort_key(x['section'])
    ))

    # 2. Sort UIDs naturally within each section!
    for idx, c in enumerate(course_list):
        c['students'].sort(key=natural_sort_key)
        del c['students_set']
        c['id'] = f"course_sec_{idx+1}_{os.urandom(2).hex()}"
        
        if len(c['sub_codes']) < 8:
            c['sub_codes'] = c['sub_codes'] + [''] * (8 - len(c['sub_codes']))
        c['sub_codes'] = c['sub_codes'][:8]
        c['dates'] = ['', '', '', '', '', '', '', '']

    return course_list


def parse_uploaded_spreadsheet(file_bytes, filename):
    entries = parse_single_file(file_bytes, filename)
    return group_and_sort_student_entries(entries)

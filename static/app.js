// Exam Attendance Sheet App - Frontend Logic (Course-wise & Section-wise Auto-Sort)

let appData = {
  settings: {
    institute_name: "CHANDIGARH UNIVERSITY, GHARUAN (MOHALI)",
    exam_title: "ATTENDANCE SHEET FOR THEORY (REGULAR) EXAMINATION MAY-JUNE 2024",
    form_code: "EX-12",
    centre_block: "B1 (Morning)",
    shift_time: "9:30 AM - 12:30 PM",
    show_logo: true,
    logo_path: "static/default_logo.png",
    logo_url: "/static/default_logo.png",
    students_per_page: 7,
    fill_empty_slots: true,
    handwritten_mode: true,
    print_scope: "all"
  },
  courses: [],
  activeCourseId: null,
  previewPage: 0,
  zoom: 0.85,
  rawRecords: [],
  metadata: null
};

function naturalSort(arr) {
  return arr.sort((a, b) => {
    return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
  });
}

function showToast(message, isError = false) {
  const toast = document.getElementById('toast');
  const msg = document.getElementById('toastMsg');
  msg.innerText = message;
  toast.style.background = isError ? '#991b1b' : '#1e293b';
  toast.style.display = 'flex';
  setTimeout(() => {
    toast.style.display = 'none';
  }, 3500);
}

// 1-Click Switcher for 7 vs 8 UIDs per sheet
function updateUidToggleUI(count) {
  const is7 = (count === 7);
  const is8 = (count === 8);

  const toggle7Top = document.getElementById('btnToggle7Uid');
  const toggle8Top = document.getElementById('btnToggle8Uid');
  const toggle7Side = document.getElementById('btnSideToggle7Uid');
  const toggle8Side = document.getElementById('btnSideToggle8Uid');

  if (toggle7Top) {
    toggle7Top.classList.toggle('active', is7);
    toggle7Top.innerHTML = is7 ? '✓ 7 UIDs / Sheet' : '7 UIDs / Sheet';
  }
  if (toggle8Top) {
    toggle8Top.classList.toggle('active', is8);
    toggle8Top.innerHTML = is8 ? '✓ 8 UIDs / Sheet' : '8 UIDs / Sheet';
  }
  if (toggle7Side) {
    toggle7Side.classList.toggle('active', is7);
    toggle7Side.innerHTML = is7 ? '✓ 7 UIDs / Sheet' : '7 UIDs / Sheet';
  }
  if (toggle8Side) {
    toggle8Side.classList.toggle('active', is8);
    toggle8Side.innerHTML = is8 ? '✓ 8 UIDs / Sheet' : '8 UIDs / Sheet';
  }

  const btnSample = document.getElementById('btnAddSampleStudents');
  if (btnSample) {
    btnSample.innerText = `Add ${count} Sample UIDs`;
  }
}

function setUidsPerPage(count, showNotification = true) {
  count = parseInt(count, 10);
  if (count !== 7 && count !== 8) count = 7;
  appData.settings.students_per_page = count;

  const sel = document.getElementById('selectStudentsPerPage');
  if (sel) sel.value = count;

  updateUidToggleUI(count);
  updateStudentStats();
  renderPreview();

  if (showNotification) {
    showToast(`Switched to ${count} UIDs per Sheet format`);
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await loadInitialData();
});

async function loadInitialData() {
  try {
    const res = await fetch('/api/sample_data');
    if (res.ok) {
      const data = await res.json();
      appData.settings = { ...appData.settings, ...data.settings };
      appData.courses = data.courses || [];
      if (appData.courses.length > 0) {
        appData.activeCourseId = appData.courses[0].id;
      }
      syncSettingsToInputs();
      renderCourseTabs();
      loadCourseIntoForm(appData.activeCourseId);
      renderPreview();
    }

    // Auto-detect and pre-load local bifurcation sheet data if available
    try {
      const localRes = await fetch('/api/load_local_bifurcation');
      if (localRes.ok) {
        const localData = await localRes.json();
        if (localData.success && localData.courses) {
          appData.courses = localData.courses;
          appData.activeCourseId = localData.courses[0].id;
          if (localData.metadata && localData.raw_records) {
            populateFilterDropdowns(localData.metadata, localData.raw_records);
          }
          renderCourseTabs();
          loadCourseIntoForm(appData.activeCourseId);
          renderPreview();
        }
      }
    } catch (e) {
      // Local file not mandatory
    }
  } catch (err) {
    console.error("Failed to load sample data:", err);
  }
}

function syncSettingsToInputs() {
  const s = appData.settings;
  const spp = parseInt(s.students_per_page, 10) || 7;
  document.getElementById('inputInstName').value = s.institute_name;
  document.getElementById('inputExamTitle').value = s.exam_title;
  document.getElementById('inputFormCode').value = s.form_code;
  document.getElementById('inputCentreBlock').value = s.centre_block;
  document.getElementById('inputShiftTime').value = s.shift_time;
  document.getElementById('checkShowLogo').checked = s.show_logo;
  document.getElementById('checkHandwrittenMode').checked = s.handwritten_mode;
  document.getElementById('selectStudentsPerPage').value = spp;
  updateUidToggleUI(spp);
  document.getElementById('checkFillEmpty').checked = s.fill_empty_slots;
  document.getElementById('selectPrintScope').value = s.print_scope;

  const previewImg = document.getElementById('logoPreviewImg');
  const headerImg = document.getElementById('headerLogoImg');
  if (s.logo_url) {
    previewImg.src = s.logo_url + '?t=' + Date.now();
    headerImg.src = s.logo_url + '?t=' + Date.now();
  }
}

function setupEventListeners() {
  // 1-Click Capacity Toggle Buttons (Toolbar & Sidebar)
  const bindToggle = (id, count) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        setUidsPerPage(count, true);
      });
    }
  };

  bindToggle('btnToggle7Uid', 7);
  bindToggle('btnToggle8Uid', 8);
  bindToggle('btnSideToggle7Uid', 7);
  bindToggle('btnSideToggle8Uid', 8);

  const bindChange = (id, prop) => {
    document.getElementById(id).addEventListener('input', (e) => {
      appData.settings[prop] = e.target.value;
      renderPreview();
    });
  };

  bindChange('inputInstName', 'institute_name');
  bindChange('inputExamTitle', 'exam_title');
  bindChange('inputFormCode', 'form_code');
  bindChange('inputCentreBlock', 'centre_block');
  bindChange('inputShiftTime', 'shift_time');

  document.getElementById('checkShowLogo').addEventListener('change', (e) => {
    appData.settings.show_logo = e.target.checked;
    renderPreview();
  });

  document.getElementById('checkHandwrittenMode').addEventListener('change', (e) => {
    appData.settings.handwritten_mode = e.target.checked;
    renderPreview();
    showToast(e.target.checked ? "Handwritten mode ON: Date & Sub Code ready for pen handwriting" : "Handwritten mode OFF");
  });

  document.getElementById('btnMakeBlankDates').addEventListener('click', () => {
    const c = getActiveCourse();
    if (!c) return;
    c.dates = ["", "", "", "", "", "", "", ""];
    c.sub_codes = ["", "", "", "", "", "", "", ""];
    appData.settings.handwritten_mode = true;
    document.getElementById('checkHandwrittenMode').checked = true;
    renderDatesTable(c);
    renderPreview();
    showToast("Cleared Dates & Subject Codes for handwriting");
  });

  document.getElementById('selectStudentsPerPage').addEventListener('change', (e) => {
    setUidsPerPage(parseInt(e.target.value, 10), true);
  });

  document.getElementById('checkFillEmpty').addEventListener('change', (e) => {
    appData.settings.fill_empty_slots = e.target.checked;
    renderPreview();
  });

  document.getElementById('selectPrintScope').addEventListener('change', (e) => {
    appData.settings.print_scope = e.target.value;
  });

  // Course & Section Inputs
  document.getElementById('inputCourseName').addEventListener('input', () => {
    saveFormToActiveCourse();
    renderCourseTabs();
    renderPreview();
  });

  document.getElementById('inputSection').addEventListener('input', () => {
    saveFormToActiveCourse();
    renderCourseTabs();
    renderPreview();
  });

  document.getElementById('inputSemester').addEventListener('input', () => {
    saveFormToActiveCourse();
    renderPreview();
  });

  document.getElementById('inputUids').addEventListener('input', () => {
    saveFormToActiveCourse();
    updateStudentStats();
    renderCourseTabs();
    renderPreview();
  });

  // Sort UIDs numerically button
  document.getElementById('btnSortUids').addEventListener('click', () => {
    const c = getActiveCourse();
    if (!c || !c.students || c.students.length === 0) return;
    c.students = naturalSort(c.students);
    document.getElementById('inputUids').value = c.students.join('\n');
    renderPreview();
    showToast("Sorted student UIDs numerically");
  });

  document.getElementById('btnAddCourse').addEventListener('click', addNewCourse);
  document.getElementById('btnDuplicateCourse').addEventListener('click', duplicateCurrentCourse);
  document.getElementById('btnDeleteCourse').addEventListener('click', deleteCurrentCourse);
  document.getElementById('btnAddSampleStudents').addEventListener('click', addSampleStudents);
  document.getElementById('btnClearStudents').addEventListener('click', () => {
    document.getElementById('inputUids').value = '';
    saveFormToActiveCourse();
    updateStudentStats();
    renderCourseTabs();
    renderPreview();
  });
  document.getElementById('btnAutoDates').addEventListener('click', autoFillDates);

  document.getElementById('logoFileInput').addEventListener('change', handleLogoUpload);
  document.getElementById('btnResetLogo').addEventListener('click', () => {
    appData.settings.logo_path = 'static/default_logo.png';
    appData.settings.logo_url = '/static/default_logo.png';
    appData.settings.show_logo = true;
    syncSettingsToInputs();
    renderPreview();
    showToast("Reset to Chandigarh University Official Logo");
  });
  document.getElementById('btnRemoveLogo').addEventListener('click', () => {
    appData.settings.logo_path = '';
    appData.settings.logo_url = '';
    appData.settings.show_logo = false;
    syncSettingsToInputs();
    renderPreview();
    showToast("Logo removed");
  });

  // Multiple File Upload & Drag & Drop
  const dropZone = document.getElementById('dropZone');
  const multiInput = document.getElementById('multiFileInput');

  dropZone.addEventListener('click', () => multiInput.click());

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = '#166534';
    dropZone.style.background = '#dcfce7';
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = '#86efac';
    dropZone.style.background = 'white';
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = '#86efac';
    dropZone.style.background = 'white';
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleMultiFileUpload(e.dataTransfer.files);
    }
  });

  multiInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleMultiFileUpload(e.target.files);
    }
  });

  document.getElementById('btnLoadLocalBifurcation').addEventListener('click', loadLocalBifurcation);
  document.getElementById('btnLoadSample').addEventListener('click', loadInitialData);

  document.getElementById('zoomSelect').addEventListener('change', (e) => {
    appData.zoom = parseFloat(e.target.value);
    applyZoom();
  });

  document.getElementById('btnPrevPage').addEventListener('click', () => {
    if (appData.previewPage > 0) {
      appData.previewPage--;
      renderPreview();
    }
  });

  document.getElementById('btnNextPage').addEventListener('click', () => {
    const course = getActiveCourse();
    const totalPages = calculatePagesForCourse(course);
    if (appData.previewPage < totalPages - 1) {
      appData.previewPage++;
      renderPreview();
    }
  });

  document.getElementById('btnShowAllPages').addEventListener('click', () => {
    if (appData.previewPage === -1) {
      appData.previewPage = 0;
      document.getElementById('btnShowAllPages').innerText = "Show All Pages";
    } else {
      appData.previewPage = -1;
      document.getElementById('btnShowAllPages').innerText = "Single Page View";
    }
    renderPreview();
  });

  document.getElementById('previewCourseSelect').addEventListener('change', (e) => {
    const cid = e.target.value;
    appData.activeCourseId = cid;
    loadCourseIntoForm(cid);
    renderCourseTabs();
    appData.previewPage = 0;
    renderPreview();
  });

  // Auto-Filter: Subject, Section & Group Selectors
  const subjSelect = document.getElementById('filterSubjectSelect');
  if (subjSelect) {
    subjSelect.addEventListener('change', () => {
      updateSectionDropdownForSubject();
      updateFilterPreviewCount();
      applyFilterToSheet(false);
    });
  }

  const secSelect = document.getElementById('filterSectionSelect');
  if (secSelect) {
    secSelect.addEventListener('change', () => {
      updateFilterPreviewCount();
      applyFilterToSheet(false);
    });
  }

  const grpSelect = document.getElementById('filterGroupSelect');
  if (grpSelect) {
    grpSelect.addEventListener('change', () => {
      updateFilterPreviewCount();
      applyFilterToSheet(false);
    });
  }

  const btnApply = document.getElementById('btnApplySelection');
  if (btnApply) {
    btnApply.addEventListener('click', (e) => {
      e.preventDefault();
      applyFilterToSheet(false);
    });
  }

  const btnAllTabs = document.getElementById('btnGenerateAllTabs');
  if (btnAllTabs) {
    btnAllTabs.addEventListener('click', (e) => {
      e.preventDefault();
      generateAllSectionsTabs();
    });
  }

  document.getElementById('btnDownloadExcel').addEventListener('click', downloadExcel);
  document.getElementById('btnDownloadExcelTop').addEventListener('click', downloadExcel);
  document.getElementById('btnPrintTop').addEventListener('click', triggerPrint);
  document.getElementById('btnPrintCurrent').addEventListener('click', triggerPrint);
}

function getActiveCourse() {
  return appData.courses.find(c => c.id === appData.activeCourseId) || appData.courses[0];
}

function calculatePagesForCourse(course) {
  if (!course) return 1;
  const count = (course.students || []).length;
  const spp = appData.settings.students_per_page || 8;
  if (count === 0) return 1;
  return Math.ceil(count / spp);
}

function renderCourseTabs() {
  const container = document.getElementById('courseTabsContainer');
  const previewSelect = document.getElementById('previewCourseSelect');
  container.innerHTML = '';
  previewSelect.innerHTML = '';

  appData.courses.forEach(c => {
    const tab = document.createElement('button');
    tab.className = `course-tab-btn ${c.id === appData.activeCourseId ? 'active' : ''}`;
    const studentCount = (c.students || []).length;
    
    // Label with Section
    const label = c.section ? `${c.course_name} (${c.section})` : (c.course_name || 'Course');
    tab.innerHTML = `<span>${label}</span> <span class="course-badge">${studentCount}</span>`;
    
    tab.addEventListener('click', () => {
      saveFormToActiveCourse();
      appData.activeCourseId = c.id;
      appData.previewPage = 0;
      loadCourseIntoForm(c.id);
      renderCourseTabs();
      renderPreview();
    });
    container.appendChild(tab);

    const opt = document.createElement('option');
    opt.value = c.id;
    opt.innerText = `${label} - ${studentCount} students`;
    opt.selected = (c.id === appData.activeCourseId);
    previewSelect.appendChild(opt);
  });
}

function loadCourseIntoForm(courseId) {
  const course = appData.courses.find(c => c.id === courseId);
  if (!course) return;

  document.getElementById('inputCourseName').value = course.course_name || '';
  document.getElementById('inputSection').value = course.section || '';
  document.getElementById('inputSemester').value = course.semester || '5';
  document.getElementById('inputUids').value = (course.students || []).join('\n');

  renderDatesTable(course);
  updateStudentStats();
}

function renderDatesTable(course) {
  const tbody = document.getElementById('datesTableBody');
  tbody.innerHTML = '';

  const dates = course.dates || [];
  const subCodes = course.sub_codes || [];

  for (let i = 0; i < 8; i++) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="text-align: center; font-weight: bold; color: #64748b;">${i + 1}</td>
      <td>
        <input type="text" class="form-control date-input" data-index="${i}" value="${dates[i] || ''}" placeholder="Handwritten / Blank">
      </td>
      <td>
        <input type="text" class="form-control subcode-input" data-index="${i}" value="${subCodes[i] || ''}" placeholder="Handwritten / Blank">
      </td>
    `;
    tbody.appendChild(tr);
  }

  tbody.querySelectorAll('.date-input').forEach(input => {
    input.addEventListener('input', (e) => {
      const idx = parseInt(e.target.dataset.index, 10);
      const c = getActiveCourse();
      if (!c.dates) c.dates = [];
      while (c.dates.length < 8) c.dates.push('');
      c.dates[idx] = e.target.value.trim();
      renderPreview();
    });
  });

  tbody.querySelectorAll('.subcode-input').forEach(input => {
    input.addEventListener('input', (e) => {
      const idx = parseInt(e.target.dataset.index, 10);
      const c = getActiveCourse();
      if (!c.sub_codes) c.sub_codes = [];
      while (c.sub_codes.length < 8) c.sub_codes.push('');
      c.sub_codes[idx] = e.target.value.trim();
      renderPreview();
    });
  });
}

function saveFormToActiveCourse() {
  const course = getActiveCourse();
  if (!course) return;

  course.course_name = document.getElementById('inputCourseName').value.trim() || 'Course';
  course.section = document.getElementById('inputSection').value.trim();
  course.semester = document.getElementById('inputSemester').value.trim() || '5';

  const rawUids = document.getElementById('inputUids').value;
  course.students = rawUids
    .split(/[\n,;\t]+/)
    .map(u => u.trim())
    .filter(u => u.length > 0);
}

function updateStudentStats() {
  const course = getActiveCourse();
  if (!course) return;
  const count = (course.students || []).length;
  const spp = appData.settings.students_per_page || 8;
  const pages = calculatePagesForCourse(course);
  document.getElementById('studentStatsBadge').innerText = `${count} Students (${pages} ${pages === 1 ? 'Page' : 'Pages'})`;
}

function addNewCourse() {
  saveFormToActiveCourse();
  const newNum = appData.courses.length + 1;
  const newCourse = {
    id: `c_${Date.now()}`,
    course_name: `CSE`,
    section: `CT-${700 + newNum}`,
    semester: '5',
    dates: ["", "", "", "", "", "", "", ""],
    sub_codes: ["", "", "", "", "", "", "", ""],
    students: [
      `24BCS${1000 + newNum}1`, `24BCS${1000 + newNum}2`, `24BCS${1000 + newNum}3`, `24BCS${1000 + newNum}4`,
      `24BCS${1000 + newNum}5`, `24BCS${1000 + newNum}6`, `24BCS${1000 + newNum}7`, `24BCS${1000 + newNum}8`
    ]
  };
  appData.courses.push(newCourse);
  appData.activeCourseId = newCourse.id;
  appData.previewPage = 0;
  renderCourseTabs();
  loadCourseIntoForm(newCourse.id);
  renderPreview();
  showToast(`Added new sheet: ${newCourse.course_name} (${newCourse.section})`);
}

function duplicateCurrentCourse() {
  saveFormToActiveCourse();
  const current = getActiveCourse();
  if (!current) return;

  const clone = JSON.parse(JSON.stringify(current));
  clone.id = `c_${Date.now()}`;
  clone.section = current.section ? `${current.section}-Copy` : 'Copy';
  appData.courses.push(clone);
  appData.activeCourseId = clone.id;
  renderCourseTabs();
  loadCourseIntoForm(clone.id);
  renderPreview();
  showToast(`Duplicated: ${clone.course_name} (${clone.section})`);
}

function deleteCurrentCourse() {
  if (appData.courses.length <= 1) {
    showToast("At least one sheet is required!", true);
    return;
  }
  const current = getActiveCourse();
  const label = current.section ? `${current.course_name} (${current.section})` : current.course_name;
  if (!confirm(`Delete sheet for "${label}"?`)) return;

  appData.courses = appData.courses.filter(c => c.id !== current.id);
  appData.activeCourseId = appData.courses[0].id;
  appData.previewPage = 0;
  renderCourseTabs();
  loadCourseIntoForm(appData.activeCourseId);
  renderPreview();
  showToast("Sheet deleted");
}

function addSampleStudents() {
  const current = getActiveCourse();
  if (!current) return;
  const count = appData.settings.students_per_page || 7;
  const basePrefix = "24BCS";
  const startNum = 1000 + Math.floor(Math.random() * 9000);
  const newBatch = [];
  for (let i = 0; i < count; i++) {
    newBatch.push(`${basePrefix}${startNum + i}`);
  }
  const currentUids = document.getElementById('inputUids').value.trim();
  document.getElementById('inputUids').value = currentUids ? `${currentUids}\n${newBatch.join('\n')}` : newBatch.join('\n');
  saveFormToActiveCourse();
  updateStudentStats();
  renderCourseTabs();
  renderPreview();
  showToast(`Added ${count} sample student UIDs`);
}

function autoFillDates() {
  const course = getActiveCourse();
  if (!course) return;
  
  const dates = [];
  const subCodes = [];
  let d = new Date(2024, 4, 20);
  for (let i = 0; i < 8; i++) {
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    dates.push(`${day}-${month}-${year}`);
    subCodes.push(`SUB-10${i + 1}`);
    d.setDate(d.getDate() + 2);
    if (d.getDay() === 0) d.setDate(d.getDate() + 1);
  }
  course.dates = dates;
  course.sub_codes = subCodes;
  appData.settings.handwritten_mode = false;
  document.getElementById('checkHandwrittenMode').checked = false;
  renderDatesTable(course);
  renderPreview();
  showToast("Auto-filled examination dates & codes");
}

async function handleLogoUpload(e) {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('logo', file);

  try {
    showToast("Uploading logo...");
    const res = await fetch('/api/upload_logo', {
      method: 'POST',
      body: formData
    });
    const result = await res.json();
    if (result.success) {
      appData.settings.logo_path = result.logo_path;
      appData.settings.logo_url = result.logo_url;
      appData.settings.show_logo = true;
      syncSettingsToInputs();
      renderPreview();
      showToast("Custom logo uploaded successfully!");
    } else {
      showToast(result.error || "Failed to upload logo", true);
    }
  } catch (err) {
    showToast("Upload failed", true);
  }
}

// Handle Multiple Files Upload with Course-Wise and Section-Wise Auto-Sorting
async function handleMultiFileUpload(fileList) {
  if (!fileList || fileList.length === 0) return;

  const mode = document.querySelector('input[name="uploadMode"]:checked').value || 'replace';
  const formData = new FormData();
  for (let i = 0; i < fileList.length; i++) {
    formData.append('files', fileList[i]);
  }
  formData.append('mode', mode);

  showToast(`Processing ${fileList.length} file(s) course-wise & section-wise...`);

  try {
    const res = await fetch('/api/upload_multiple_files', {
      method: 'POST',
      body: formData
    });

    const result = await res.json();
    if (!res.ok || !result.success) {
      showToast(result.error || "Failed to parse files", true);
      return;
    }

    if (mode === 'replace') {
      appData.courses = result.courses;
    } else {
      result.courses.forEach(c => appData.courses.push(c));
    }

    if (appData.courses.length > 0) {
      appData.activeCourseId = appData.courses[0].id;
    }

    appData.previewPage = 0;
    renderCourseTabs();
    loadCourseIntoForm(appData.activeCourseId);
    renderPreview();

    if (result.metadata && result.raw_records) {
      populateFilterDropdowns(result.metadata, result.raw_records);
    }

    const statusBadge = document.getElementById('uploadStatusBadge');
    statusBadge.style.display = 'block';
    statusBadge.innerHTML = `✅ <b>${result.files_processed} file(s)</b> processed: <b>${result.total_courses} sheet(s)</b> auto-grouped by <b>Course</b> & sorted <b>Section-wise</b> (${result.total_students} students total)!`;

    showToast(`Success: Created ${result.total_courses} course-section sheets from ${result.files_processed} files!`);
  } catch (err) {
    showToast("Error uploading files", true);
  }
}

async function loadLocalBifurcation() {
  try {
    showToast("Loading bifurcation sheet from workspace...");
    const res = await fetch('/api/load_local_bifurcation');
    const result = await res.json();
    if (result.success && result.courses) {
      const mode = document.querySelector('input[name="uploadMode"]:checked').value || 'replace';
      if (mode === 'replace') {
        appData.courses = result.courses;
      } else {
        result.courses.forEach(c => appData.courses.push(c));
      }
      appData.activeCourseId = result.courses[0].id;
      appData.previewPage = 0;
      if (result.metadata && result.raw_records) {
        populateFilterDropdowns(result.metadata, result.raw_records);
      }
      renderCourseTabs();
      loadCourseIntoForm(appData.activeCourseId);
      renderPreview();
      showToast(`Loaded ${result.courses[0].course_name} (${result.courses[0].section}) with ${result.courses[0].students.length} students!`);
    } else {
      showToast(result.error || "File not found", true);
    }
  } catch (err) {
    showToast("Could not load local file", true);
  }
}

// =========================================================================
// AUTO-FETCH & FILTER: SUBJECT, SECTION & GROUP SELECTION LOGIC
// =========================================================================

function populateFilterDropdowns(metadata, records) {
  if (!records || records.length === 0) return;
  appData.rawRecords = records;
  appData.metadata = metadata;

  const subjSelect = document.getElementById('filterSubjectSelect');
  const secSelect = document.getElementById('filterSectionSelect');
  const grpSelect = document.getElementById('filterGroupSelect');

  if (!subjSelect || !secSelect || !grpSelect) return;

  // 1. Populate Subjects Dropdown
  subjSelect.innerHTML = '';
  const subjects = metadata.subjects || [];
  if (subjects.length === 0) {
    subjSelect.innerHTML = '<option value="all">All Subjects</option>';
  } else {
    if (subjects.length > 1) {
      subjSelect.innerHTML += '<option value="all">All Subjects (Combined)</option>';
    }
    subjects.forEach((s, idx) => {
      const opt = document.createElement('option');
      opt.value = s.id;
      const count = records.filter(r => (r.subject || r.course) === s.id).length || s.count;
      opt.innerText = `${s.display || s.title || s.id} (${count} students)`;
      if (idx === 0) opt.selected = true;
      subjSelect.appendChild(opt);
    });
  }

  // 2. Populate Sections Dropdown
  updateSectionDropdownForSubject();

  // 3. Populate Groups Dropdown
  grpSelect.innerHTML = '';
  const groups = metadata.groups || ['All Groups (Whole Section)'];
  groups.forEach((g, idx) => {
    const opt = document.createElement('option');
    opt.value = g;
    opt.innerText = g;
    if (idx === 0) opt.selected = true;
    grpSelect.appendChild(opt);
  });

  // Highlight the Auto-Filter box
  const box = document.getElementById('autoFilterBox');
  if (box) {
    box.style.borderColor = '#2563eb';
    box.style.background = '#f0f9ff';
  }

  updateFilterPreviewCount();
}

function updateSectionDropdownForSubject() {
  const subjSelect = document.getElementById('filterSubjectSelect');
  const secSelect = document.getElementById('filterSectionSelect');
  if (!subjSelect || !secSelect) return;

  const selectedSubj = subjSelect.value;
  secSelect.innerHTML = '';

  let availableSections = [];
  if (appData.rawRecords && appData.rawRecords.length > 0) {
    const matching = (selectedSubj === 'all') 
      ? appData.rawRecords 
      : appData.rawRecords.filter(r => (r.subject || r.course) === selectedSubj);

    const secCounts = {};
    matching.forEach(r => {
      const s = r.section || 'Sec-1';
      secCounts[s] = (secCounts[s] || 0) + 1;
    });

    availableSections = Object.keys(secCounts).sort((a, b) => {
      return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
    }).map(s => ({ name: s, count: secCounts[s] }));
  }

  if (availableSections.length === 0) {
    secSelect.innerHTML = '<option value="all">All Sections</option>';
  } else {
    if (availableSections.length > 1) {
      secSelect.innerHTML += '<option value="all">All Sections</option>';
    }
    availableSections.forEach((sec, idx) => {
      const opt = document.createElement('option');
      opt.value = sec.name;
      opt.innerText = `${sec.name} (${sec.count} students)`;
      if (idx === 0) opt.selected = true;
      secSelect.appendChild(opt);
    });
  }
}

function getFilteredStudents() {
  if (!appData.rawRecords || appData.rawRecords.length === 0) {
    const active = getActiveCourse();
    return (active && active.students) ? active.students.map(u => ({ uid: u })) : [];
  }

  const subjSelect = document.getElementById('filterSubjectSelect');
  const secSelect = document.getElementById('filterSectionSelect');
  const grpSelect = document.getElementById('filterGroupSelect');

  const subjSel = subjSelect ? subjSelect.value : 'all';
  const secSel = secSelect ? secSelect.value : 'all';
  const grpSel = grpSelect ? grpSelect.value : 'all';

  let filtered = appData.rawRecords.filter(r => {
    const rSubj = r.subject || r.course || '';
    const rSec = r.section || '';
    if (subjSel !== 'all' && rSubj !== subjSel) return false;
    if (secSel !== 'all' && rSec !== secSel) return false;
    return true;
  });

  // Sort by UID naturally
  filtered = filtered.sort((a, b) => {
    return (a.uid || '').localeCompare(b.uid || '', undefined, { numeric: true, sensitivity: 'base' });
  });

  // Group filtering
  if (grpSel && grpSel !== 'all' && !grpSel.toLowerCase().includes('all groups')) {
    const hasExplicit = filtered.some(r => r.group && r.group.trim());
    if (hasExplicit) {
      filtered = filtered.filter(r => (r.group || '').toLowerCase() === grpSel.toLowerCase());
    } else {
      // Smart 50/50 split for lab batches
      const half = Math.ceil(filtered.length / 2);
      if (grpSel.includes('1') || grpSel.toLowerCase().includes('g1') || grpSel.toLowerCase().includes('batch 1')) {
        filtered = filtered.slice(0, half);
      } else if (grpSel.includes('2') || grpSel.toLowerCase().includes('g2') || grpSel.toLowerCase().includes('batch 2')) {
        filtered = filtered.slice(half);
      }
    }
  }

  return filtered;
}

function updateFilterPreviewCount() {
  const filtered = getFilteredStudents();
  const count = filtered.length;
  const badge = document.getElementById('filterStatsBadge');
  const countBadge = document.getElementById('filterCountBadge');
  const summaryText = document.getElementById('filterSummaryText');

  const spp = appData.settings.students_per_page || 7;
  const pages = Math.ceil(count / spp) || 1;

  if (badge) {
    badge.style.display = 'inline-block';
    badge.innerText = `${count} Students`;
  }
  if (countBadge) {
    countBadge.innerText = `${count} Students (${pages} ${pages === 1 ? 'Page' : 'Pages'})`;
  }

  const subjSelect = document.getElementById('filterSubjectSelect');
  const secSelect = document.getElementById('filterSectionSelect');
  const grpSelect = document.getElementById('filterGroupSelect');

  const subjSel = subjSelect ? subjSelect.value : 'all';
  const secSel = secSelect ? secSelect.value : 'all';
  const grpSel = grpSelect ? grpSelect.value : 'all';

  const subjLabel = subjSel === 'all' ? 'All Subjects' : (subjSel.length > 25 ? subjSel.substring(0, 25) + '...' : subjSel);
  const secLabel = secSel === 'all' ? 'All Secs' : secSel;
  const grpLabel = grpSel.includes('1') ? 'Group 1' : (grpSel.includes('2') ? 'Group 2' : 'All Groups');

  if (summaryText) {
    summaryText.innerHTML = `<b>${subjLabel}</b> &bull; <b>${secLabel}</b> &bull; <b>${grpLabel}</b>`;
  }
}

function applyFilterToSheet(asNewCourse = false) {
  const filtered = getFilteredStudents();
  if (filtered.length === 0) {
    showToast("No students found matching your selected Subject, Section, and Group.", true);
    return;
  }

  const first = filtered[0];
  const secSelect = document.getElementById('filterSectionSelect');
  const grpSelect = document.getElementById('filterGroupSelect');

  const secSel = secSelect ? secSelect.value : 'all';
  const grpSel = grpSelect ? grpSelect.value : 'all';

  const baseSec = first.section || (secSel !== 'all' ? secSel : 'Sec-1');
  let secDisplay = baseSec;
  if (grpSel && grpSel !== 'all' && !grpSel.toLowerCase().includes('all groups')) {
    const grpShort = (grpSel.includes('1') || grpSel.toLowerCase().includes('g1')) ? 'Group 1' :
                     ((grpSel.includes('2') || grpSel.toLowerCase().includes('g2')) ? 'Group 2' : grpSel);
    secDisplay = `${baseSec} (${grpShort})`;
  }

  let courseDisplay = first.course || 'CSE';
  if (first.subject_title && !courseDisplay.toLowerCase().includes(first.subject_title.toLowerCase())) {
    courseDisplay = `${courseDisplay} - ${first.subject_title}`;
  }

  const subCode = first.sub_code || '';
  const semester = first.semester || '5';
  const uids = filtered.map(r => r.uid);

  const subCodes = [subCode];
  while (subCodes.length < 8) subCodes.push('');

  let targetCourse;
  if (asNewCourse || appData.courses.length === 0) {
    targetCourse = {
      id: `course_${Date.now()}`,
      course_name: courseDisplay,
      section: secDisplay,
      semester: semester,
      dates: ['', '', '', '', '', '', '', ''],
      sub_codes: subCodes,
      students: uids
    };
    appData.courses.push(targetCourse);
    appData.activeCourseId = targetCourse.id;
  } else {
    targetCourse = getActiveCourse();
    targetCourse.course_name = courseDisplay;
    targetCourse.section = secDisplay;
    targetCourse.semester = semester;
    if (subCode) targetCourse.sub_codes[0] = subCode;
    targetCourse.students = uids;
  }

  appData.previewPage = 0;
  loadCourseIntoForm(appData.activeCourseId);
  renderCourseTabs();
  renderPreview();
  showToast(`✅ Generated sheet for ${courseDisplay} | ${secDisplay} (${uids.length} UIDs)!`);
}

function generateAllSectionsTabs() {
  if (!appData.rawRecords || appData.rawRecords.length === 0) {
    showToast("Please upload an Excel file first.", true);
    return;
  }

  const secSelect = document.getElementById('filterSectionSelect');
  let sections = [];
  if (secSelect) {
    for (let opt of secSelect.options) {
      if (opt.value && opt.value !== 'all') sections.push(opt.value);
    }
  }

  if (sections.length === 0) {
    applyFilterToSheet(false);
    return;
  }

  appData.courses = [];
  sections.forEach((sec, idx) => {
    const secStudents = appData.rawRecords.filter(r => r.section === sec);
    if (secStudents.length === 0) return;

    const first = secStudents[0];
    let courseDisplay = first.course || 'CSE';
    if (first.subject_title && !courseDisplay.toLowerCase().includes(first.subject_title.toLowerCase())) {
      courseDisplay = `${courseDisplay} - ${first.subject_title}`;
    }

    const subCode = first.sub_code || '';
    const subCodes = [subCode];
    while (subCodes.length < 8) subCodes.push('');

    const uids = naturalSort(secStudents.map(r => r.uid));

    appData.courses.push({
      id: `sec_course_${idx + 1}_${Date.now()}`,
      course_name: courseDisplay,
      section: sec,
      semester: first.semester || '5',
      dates: ['', '', '', '', '', '', '', ''],
      sub_codes: subCodes,
      students: uids
    });
  });

  if (appData.courses.length > 0) {
    appData.activeCourseId = appData.courses[0].id;
  }
  appData.previewPage = 0;
  loadCourseIntoForm(appData.activeCourseId);
  renderCourseTabs();
  renderPreview();
  showToast(`Generated ${appData.courses.length} Section sheets as separate tabs!`);
}

function applyZoom() {
  const wrapper = document.getElementById('paperWrapper');
  wrapper.style.transform = `scale(${appData.zoom})`;
}

// Render the Live A4 Landscape Preview
function renderPreview() {
  const wrapper = document.getElementById('paperWrapper');
  const course = getActiveCourse();
  if (!course) return;

  const totalPages = calculatePagesForCourse(course);
  
  const indicator = document.getElementById('pageIndicatorText');
  if (appData.previewPage === -1) {
    indicator.innerText = `All Pages (1 to ${totalPages})`;
  } else {
    if (appData.previewPage >= totalPages) appData.previewPage = totalPages - 1;
    if (appData.previewPage < 0) appData.previewPage = 0;
    indicator.innerText = `Page ${appData.previewPage + 1} of ${totalPages}`;
  }

  wrapper.innerHTML = '';

  const pagesToRender = (appData.previewPage === -1) 
    ? Array.from({ length: totalPages }, (_, i) => i) 
    : [appData.previewPage];

  pagesToRender.forEach(pIdx => {
    const pageHtml = generatePageHtml(course, pIdx, totalPages);
    wrapper.appendChild(pageHtml);
  });

  applyZoom();
}

function generatePageHtml(course, pageIndex, totalPages) {
  const s = appData.settings;
  const spp = s.students_per_page || 7;
  const pageContainer = document.createElement('div');
  pageContainer.className = `sheet-page layout-${spp}uid`;

  const dates = course.dates || [];
  const subCodes = course.sub_codes || [];
  const students = course.students || [];

  const startIdx = pageIndex * spp;
  const pageStudents = students.slice(startIdx, startIdx + spp);

  const logoHtml = (s.show_logo && s.logo_url) 
    ? `<img src="${s.logo_url}" alt="Chandigarh University Logo" style="max-height: 100%; max-width: 100%; object-fit: contain;">` 
    : '';

  let tableRowsHtml = '';

  let dateThs = '';
  let subCodeThs = '';
  for (let i = 0; i < 8; i++) {
    const rawDate = dates[i] ? dates[i].trim() : '';
    const rawCode = subCodes[i] ? subCodes[i].trim() : '';

    const isHandwritten = s.handwritten_mode || !rawDate;
    const isCodeHandwritten = s.handwritten_mode || !rawCode;

    let dateContent = '';
    if (isHandwritten) {
      dateContent = `
        <div style="font-size: 7.5pt; font-weight: bold;">Date:</div>
        <div style="height: 10px; border-bottom: 1px dotted #475569; margin: 2px 2px 0;"></div>
      `;
    } else {
      dateContent = `<div style="font-size: 7.5pt; font-weight: bold;">Date: ${rawDate}</div>`;
    }

    let subCodeContent = '';
    if (isCodeHandwritten) {
      subCodeContent = `
        <div style="font-size: 7.5pt; font-weight: bold;">Sub Code:</div>
        <div style="height: 15px; border-bottom: 1px dotted #475569; margin: 2px 2px 0;"></div>
      `;
    } else {
      subCodeContent = `<div style="font-size: 7.5pt; font-weight: bold; line-height: 1.15;">Sub Code:<br><b>${rawCode}</b></div>`;
    }

    dateThs += `<th class="th-exam-col" style="vertical-align: middle;">${dateContent}</th>`;
    subCodeThs += `<th class="th-exam-col" style="vertical-align: top; padding-top: 2px;">${subCodeContent}</th>`;
  }

  // Student rows
  for (let sIdx = 0; sIdx < spp; sIdx++) {
    const uid = pageStudents[sIdx] || (s.fill_empty_slots ? '' : null);
    if (uid === null) continue;

    tableRowsHtml += `
      <tr class="row-ab">
        <td class="td-uid" rowspan="3">${uid}</td>
        <td class="td-label">* A/B No.</td>
        ${'<td></td>'.repeat(8)}
      </tr>
      <tr class="row-omr">
        <td class="td-label">OMR No.</td>
        ${'<td></td>'.repeat(8)}
      </tr>
      <tr class="row-sig">
        <td class="td-label sig-label">Signature</td>
        ${'<td></td>'.repeat(8)}
      </tr>
    `;
  }

  // Build course + section display line
  let courseDisplay = course.course_name || 'Course';
  if (course.section && !courseDisplay.includes(course.section)) {
    courseDisplay = `${courseDisplay} (Section: ${course.section})`;
  }

  pageContainer.innerHTML = `
    <!-- Top Row: Logo & EX-12 Form Code -->
    <div class="sheet-top-row">
      <div class="sheet-logo-area">
        ${logoHtml}
      </div>
      <div class="sheet-form-code">${s.form_code}</div>
    </div>

    <!-- University Name -->
    <div class="sheet-inst-title">${s.institute_name}</div>

    <!-- Exam Title -->
    <div class="sheet-exam-title">${s.exam_title}</div>

    <!-- Course / Block / Shift info strip -->
    <div class="sheet-info-strip">
      <div>Course/Branch: <u>${courseDisplay}</u></div>
      <div>Centre/Block No: <u>${s.centre_block}</u></div>
      <div>Shift Time: <u>${s.shift_time}</u></div>
    </div>

    <!-- 10-Column Attendance Table -->
    <table class="exam-table">
      <thead>
        <tr>
          <th class="th-uid" rowspan="2">UID No.</th>
          <th class="th-sem">Semester: ${course.semester || '5'}</th>
          ${dateThs}
        </tr>
        <tr>
          <th></th>
          ${subCodeThs}
        </tr>
      </thead>
      <tbody>
        ${tableRowsHtml}
      </tbody>
    </table>

    <!-- Footer: Invigilator Signatures -->
    <table class="sheet-invigilator-row">
      <tr>
        <td class="sheet-invigilator-label">Invigilator's Signature &amp; Emp.ID :-</td>
        ${'<td class="sheet-invigilator-col"></td>'.repeat(8)}
      </tr>
    </table>

    <!-- Footer: Superintendent & Notes -->
    <div class="sheet-bottom-strip">
      <div class="sheet-bottom-note">Note: *A/B stands for Answer Book No.</div>
      <div class="sheet-bottom-centre">Centre Supdt. Name &amp; Sign.: _____________________________________________</div>
      <div class="sheet-bottom-empid">Emp. ID__________</div>
    </div>
  `;

  return pageContainer;
}

// Download Excel (.xlsx) file
async function downloadExcel() {
  saveFormToActiveCourse();

  showToast("Generating Multi-Sheet Excel workbook...");
  try {
    const payload = {
      settings: appData.settings,
      courses: appData.courses
    };

    const res = await fetch('/api/generate_excel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      showToast(err.error || "Excel generation failed", true);
      return;
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Exam_Attendance_Sheets_${appData.settings.form_code}_${appData.courses.length}_Sheets_SectionWise.xlsx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    showToast("Excel workbook downloaded successfully!");
  } catch (err) {
    showToast("Error downloading Excel file", true);
  }
}

// Print sheets using Browser Print Dialog with exact A4 Landscape layout
function triggerPrint() {
  saveFormToActiveCourse();
  const wrapper = document.getElementById('paperWrapper');
  wrapper.style.transform = 'none';

  const printScope = appData.settings.print_scope;

  if (printScope === 'all') {
    wrapper.innerHTML = '';
    appData.courses.forEach(course => {
      const totalPages = calculatePagesForCourse(course);
      for (let p = 0; p < totalPages; p++) {
        wrapper.appendChild(generatePageHtml(course, p, totalPages));
      }
    });
  } else {
    const currentCourse = getActiveCourse();
    const totalPages = calculatePagesForCourse(currentCourse);
    wrapper.innerHTML = '';
    for (let p = 0; p < totalPages; p++) {
      wrapper.appendChild(generatePageHtml(currentCourse, p, totalPages));
    }
  }

  setTimeout(() => {
    window.print();
    renderPreview();
  }, 150);
}

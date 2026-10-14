/**
 * Student Skill & Placement Tracker - Interactive Client Scripts
 */

// Theme Manager: Handles Dark / Light mode toggle, system preference detection & localStorage
function initThemeManager() {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const labelText = themeToggleBtn ? themeToggleBtn.querySelector('.theme-label-text') : null;

    function getStoredOrSystemTheme() {
        const savedTheme = localStorage.getItem('skilltrack_theme');
        if (savedTheme === 'dark' || savedTheme === 'light') {
            return savedTheme;
        }
        return (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';
    }

    function applyTheme(theme, savePreference = true, animate = false) {
        if (animate) {
            document.documentElement.classList.add('theme-transition');
        }

        document.documentElement.setAttribute('data-bs-theme', theme);
        document.documentElement.setAttribute('data-theme', theme);

        if (savePreference) {
            localStorage.setItem('skilltrack_theme', theme);
        }

        if (themeToggleBtn) {
            const isDark = theme === 'dark';
            themeToggleBtn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
            themeToggleBtn.setAttribute('title', isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode');
            if (labelText) {
                labelText.textContent = isDark ? 'Dark' : 'Light';
            }
        }

        // Notify other components (e.g., Chart.js) of theme change
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: theme } }));

        if (animate) {
            setTimeout(function () {
                document.documentElement.classList.remove('theme-transition');
            }, 350);
        }
    }

    // Set initial toggle state on page load without animation delay
    const initialTheme = document.documentElement.getAttribute('data-bs-theme') || getStoredOrSystemTheme();
    applyTheme(initialTheme, false, false);

    // Toggle button click listener
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function () {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme') || 'light';
            const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(nextTheme, true, true);
        });
    }

    // Listen to OS system color scheme changes (only if user hasn't explicitly chosen)
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
            if (!localStorage.getItem('skilltrack_theme')) {
                applyTheme(e.matches ? 'dark' : 'light', false, true);
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // 0. Initialize Dark/Light Theme System
    initThemeManager();

    // 1. Auto-dismiss bootstrap alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // 2. Demo Login Credential Autofill Helper (Extremely helpful for Viva!)
    const fillStudentBtn = document.getElementById('fill-student-login');
    const fillAdminBtn = document.getElementById('fill-admin-login');

    if (fillStudentBtn) {
        fillStudentBtn.addEventListener('click', function () {
            const emailInput = document.getElementById('email');
            const passInput = document.getElementById('password');
            if (emailInput && passInput) {
                emailInput.value = 'student@college.edu';
                passInput.value = 'student123';
            }
        });
    }

    if (fillAdminBtn) {
        fillAdminBtn.addEventListener('click', function () {
            const emailInput = document.getElementById('email');
            const passInput = document.getElementById('password');
            if (emailInput && passInput) {
                emailInput.value = 'admin@placement.edu';
                passInput.value = 'admin123';
            }
        });
    }

    // 3. Resume File Validation (.pdf only)
    const resumeForm = document.getElementById('resume-upload-form');
    if (resumeForm) {
        resumeForm.addEventListener('submit', function (e) {
            const fileInput = document.getElementById('resume_file');
            if (fileInput && fileInput.files.length > 0) {
                const fileName = fileInput.files[0].name;
                const extension = fileName.split('.').pop().toLowerCase();
                if (extension !== 'pdf') {
                    e.preventDefault();
                    alert('Invalid file format! Please upload a PDF file (.pdf) only.');
                }
            }
        });
    }

    // 4. Interactive Skill Gap Analyzer
    const jobSelect = document.getElementById('gap-job-selector');
    if (jobSelect) {
        jobSelect.addEventListener('change', function () {
            const jobId = this.value;
            if (jobId) {
                loadSkillGapAnalysis(jobId);
            } else {
                resetSkillGapView();
            }
        });

        // If job already preselected in select box
        if (jobSelect.value) {
            loadSkillGapAnalysis(jobSelect.value);
        }
    }
});

/**
 * Fetches skill gap analysis from API and updates the UI dynamically
 */
function loadSkillGapAnalysis(jobId) {
    const resultCard = document.getElementById('skill-gap-result');
    const loadingSpinner = document.getElementById('gap-loading-spinner');
    const placeholder = document.getElementById('gap-placeholder');

    if (loadingSpinner) loadingSpinner.classList.remove('d-none');
    if (placeholder) placeholder.classList.add('d-none');

    fetch('/api/skill-gap/' + jobId)
        .then(response => {
            if (!response.ok) throw new Error('Network error loading skill gap data');
            return response.json();
        })
        .then(data => {
            if (loadingSpinner) loadingSpinner.classList.add('d-none');
            if (resultCard) resultCard.classList.remove('d-none');

            // Set titles
            document.getElementById('gap-job-title').textContent = data.job_title;
            document.getElementById('gap-job-company').textContent = data.company;

            // Set Match Percentage Circle & Progress
            const pct = data.match_percentage;
            const scoreEl = document.getElementById('gap-percentage');
            scoreEl.textContent = pct + '%';

            const scoreCircle = document.getElementById('gap-score-circle');
            scoreCircle.className = 'match-score-circle';
            if (pct >= 70) {
                scoreCircle.classList.add('match-score-high');
            } else if (pct >= 40) {
                scoreCircle.classList.add('match-score-med');
            } else {
                scoreCircle.classList.add('match-score-low');
            }

            // Render Matched Skills
            const matchedContainer = document.getElementById('gap-matched-skills');
            matchedContainer.innerHTML = '';
            if (data.matched_skills && data.matched_skills.length > 0) {
                data.matched_skills.forEach(skill => {
                    const tag = document.createElement('span');
                    tag.className = 'skill-tag matched';
                    tag.innerHTML = `<i class="fa-solid fa-check me-1"></i> ${skill.name} <small class="text-muted ms-1">(${skill.proficiency})</small>`;
                    matchedContainer.appendChild(tag);
                });
            } else {
                matchedContainer.innerHTML = '<span class="text-muted small">No direct skill matches found for this role.</span>';
            }

            // Render Missing Skills
            const missingContainer = document.getElementById('gap-missing-skills');
            missingContainer.innerHTML = '';
            if (data.missing_skills && data.missing_skills.length > 0) {
                data.missing_skills.forEach(skill => {
                    const tag = document.createElement('span');
                    tag.className = 'skill-tag missing';
                    tag.innerHTML = `<i class="fa-solid fa-xmark me-1"></i> ${skill}`;
                    missingContainer.appendChild(tag);
                });
            } else {
                missingContainer.innerHTML = '<span class="text-success small fw-semibold"><i class="fa-solid fa-circle-check me-1"></i> Excellent! No missing required skills.</span>';
            }

            // Recommendation
            const recEl = document.getElementById('gap-recommendation');
            recEl.textContent = data.recommendation;

            // Apply CTA link
            const applyBtn = document.getElementById('gap-apply-btn');
            if (applyBtn) {
                applyBtn.setAttribute('data-job-id', data.job_id);
            }
        })
        .catch(err => {
            console.error('Error fetching skill gap:', err);
            if (loadingSpinner) loadingSpinner.classList.add('d-none');
            alert('Failed to calculate skill gap. Please try again.');
        });
}

function resetSkillGapView() {
    const resultCard = document.getElementById('skill-gap-result');
    const placeholder = document.getElementById('gap-placeholder');
    if (resultCard) resultCard.classList.add('d-none');
    if (placeholder) placeholder.classList.remove('d-none');
}

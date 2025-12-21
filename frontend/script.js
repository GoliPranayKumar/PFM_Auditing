/* ========================================
   AI AUDIT AGENT - FRONTEND LOGIC
   Backend Integration & User Interactions
   ======================================== */

// ========================================
// CONFIGURATION
// ========================================
const API_BASE_URL = 'http://localhost:8000';
const API_ENDPOINT = `${API_BASE_URL}/api/v1/upload/analyze`;

// ========================================
// DOM ELEMENTS
// ========================================
const elements = {
    // Upload Section
    dropzone: document.getElementById('dropzone'),
    fileInput: document.getElementById('fileInput'),
    selectedFile: document.getElementById('selectedFile'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    removeFileBtn: document.getElementById('removeFileBtn'),
    emailInput: document.getElementById('emailInput'),
    analyzeBtn: document.getElementById('analyzeBtn'),

    // Sections
    uploadSection: document.getElementById('uploadSection'),
    loadingSection: document.getElementById('loadingSection'),
    resultsSection: document.getElementById('resultsSection'),
    errorSection: document.getElementById('errorSection'),

    // Results
    riskBadge: document.getElementById('riskBadge'),
    riskValue: document.getElementById('riskValue'),
    flagsCount: document.getElementById('flagsCount'),
    flaggedAmount: document.getElementById('flaggedAmount'),
    summaryText: document.getElementById('summaryText'),
    flagsList: document.getElementById('flagsList'),
    flagsSection: document.getElementById('flagsSection'),
    visualizationsSection: document.getElementById('visualizationsSection'),
    vizGrid: document.getElementById('vizGrid'),
    recommendationsList: document.getElementById('recommendationsList'),
    recommendationsSection: document.getElementById('recommendationsSection'),
    emailStatus: document.getElementById('emailStatus'),
    emailStatusText: document.getElementById('emailStatusText'),

    // Error & Actions
    errorText: document.getElementById('errorText'),
    retryBtn: document.getElementById('retryBtn'),
    newAnalysisBtn: document.getElementById('newAnalysisBtn')
};

// ========================================
// STATE MANAGEMENT
// ========================================
let selectedFileData = null;

// ========================================
// FILE UPLOAD HANDLING
// ========================================

// Dropzone click handler
elements.dropzone.addEventListener('click', () => {
    elements.fileInput.click();
});

// File input change
elements.fileInput.addEventListener('change', (e) => {
    handleFileSelection(e.target.files[0]);
});

// Drag & drop handlers
elements.dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.dropzone.classList.add('dragover');
});

elements.dropzone.addEventListener('dragleave', () => {
    elements.dropzone.classList.remove('dragover');
});

elements.dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.dropzone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    handleFileSelection(file);
});

// Remove file handler
elements.removeFileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    clearFileSelection();
});

/**
 * Handle file selection
 */
function handleFileSelection(file) {
    if (!file) return;

    // Validate file type
    const validTypes = ['.pdf', '.docx', '.txt'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

    if (!validTypes.includes(fileExtension)) {
        showError('Invalid file type. Please upload PDF, DOCX, or TXT files.');
        return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showError('File too large. Maximum size is 10MB.');
        return;
    }

    // Store file
    selectedFileData = file;

    // Update UI
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = formatFileSize(file.size);
    elements.selectedFile.style.display = 'flex';
    elements.dropzone.style.display = 'none';
    elements.analyzeBtn.disabled = false;
}

/**
 * Clear file selection
 */
function clearFileSelection() {
    selectedFileData = null;
    elements.fileInput.value = '';
    elements.selectedFile.style.display = 'none';
    elements.dropzone.style.display = 'block';
    elements.analyzeBtn.disabled = true;
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// ========================================
// ANALYZE DOCUMENT
// ========================================
elements.analyzeBtn.addEventListener('click', analyzeDocument);

async function analyzeDocument() {
    if (!selectedFileData) return;

    // Show loading state
    showSection('loading');
    animateLoadingSteps();

    // Prepare form data
    const formData = new FormData();
    formData.append('file', selectedFileData);

    // Add email if provided
    const email = elements.emailInput.value.trim();
    if (email) {
        formData.append('recipient_email', email);
        console.log('Email will be sent to:', email);
    }

    try {
        // Make API request
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Server error: ${response.status}`);
        }

        const data = await response.json();

        // Display results
        displayResults(data);

    } catch (error) {
        console.error('Analysis error:', error);
        showError(error.message || 'Failed to analyze document. Please try again.');
    }
}

// ========================================
// LOADING ANIMATION
// ========================================
let loadingInterval;

function animateLoadingSteps() {
    const steps = document.querySelectorAll('.step');
    let currentStep = 0;

    // Clear any existing interval
    if (loadingInterval) clearInterval(loadingInterval);

    // Activate first step
    steps[0].classList.add('active');

    // Cycle through steps
    loadingInterval = setInterval(() => {
        steps[currentStep].classList.remove('active');
        currentStep = (currentStep + 1) % steps.length;
        steps[currentStep].classList.add('active');
    }, 2000);
}

// ========================================
// DISPLAY RESULTS
// ========================================
function displayResults(data) {
    if (!data || !data.analysis) {
        showError('Invalid response from server');
        return;
    }

    const analysis = data.analysis;

    // Risk level
    const riskLevel = (analysis.risk_level || 'Medium').toLowerCase();
    elements.riskBadge.className = `risk-badge ${riskLevel}`;
    elements.riskValue.textContent = analysis.risk_level || 'Medium';

    // Stats
    elements.flagsCount.textContent = analysis.list_of_flags?.length || 0;
    elements.flaggedAmount.textContent = formatCurrency(analysis.total_flagged_amount || 0);

    // Summary
    elements.summaryText.textContent = analysis.summary || 'No summary available.';

    // Fraud flags
    if (analysis.list_of_flags && analysis.list_of_flags.length > 0) {
        displayFraudFlags(analysis.list_of_flags);
        elements.flagsSection.style.display = 'block';
    } else {
        elements.flagsSection.style.display = 'none';
    }

    // Visualizations
    if (analysis.visualizations && Object.keys(analysis.visualizations).length > 0) {
        displayVisualizations(analysis.visualizations);
        elements.visualizationsSection.style.display = 'block';
    } else {
        elements.visualizationsSection.style.display = 'none';
    }

    // Recommendations
    if (analysis.recommendations && analysis.recommendations.length > 0) {
        displayRecommendations(analysis.recommendations);
        elements.recommendationsSection.style.display = 'block';
    } else {
        elements.recommendationsSection.style.display = 'none';
    }

    // Email status
    if (analysis.email_sent && analysis.email_sent.success) {
        elements.emailStatusText.textContent = analysis.email_sent.message || 'Email sent successfully';
        elements.emailStatus.style.display = 'flex';
    } else {
        elements.emailStatus.style.display = 'none';
    }

    // Show results section
    showSection('results');
}

/**
 * Display fraud flags
 */
function displayFraudFlags(flags) {
    elements.flagsList.innerHTML = '';

    flags.forEach((flag, index) => {
        const flagItem = document.createElement('div');
        flagItem.className = `flag-item ${(flag.severity || 'medium').toLowerCase()}`;
        flagItem.style.animationDelay = `${index * 0.1}s`;

        flagItem.innerHTML = `
            <div class="flag-header">
                <div class="flag-category">${formatCategory(flag.category)}</div>
                <div class="flag-severity ${flag.severity?.toLowerCase() || 'medium'}">
                    ${flag.severity || 'Medium'}
                </div>
            </div>
            <div class="flag-description">${flag.description || ''}</div>
            <div class="flag-evidence">${flag.evidence || ''}</div>
            <div class="flag-meta">
                <span>Confidence: ${Math.round((flag.confidence || 0) * 100)}%</span>
                ${flag.amount_involved ? `<span>Amount: ${formatCurrency(flag.amount_involved)}</span>` : ''}
            </div>
        `;

        elements.flagsList.appendChild(flagItem);
    });
}

/**
 * Display visualizations
 */
function displayVisualizations(visualizations) {
    elements.vizGrid.innerHTML = '';

    Object.entries(visualizations).forEach(([key, path]) => {
        const vizItem = document.createElement('div');
        vizItem.className = 'viz-item';

        // Convert backend path to accessible URL
        const imageUrl = `${API_BASE_URL}/${path.replace(/\\/g, '/')}`;

        vizItem.innerHTML = `
            <img src="${imageUrl}" alt="${formatCategory(key)}" 
                 onerror="this.parentElement.style.display='none'">
        `;

        elements.vizGrid.appendChild(vizItem);
    });
}

/**
 * Display recommendations
 */
function displayRecommendations(recommendations) {
    elements.recommendationsList.innerHTML = '';

    recommendations.forEach((rec, index) => {
        const li = document.createElement('li');
        li.textContent = rec;
        li.style.animationDelay = `${index * 0.1}s`;
        elements.recommendationsList.appendChild(li);
    });
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

/**
 * Format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * Format category name
 */
function formatCategory(category) {
    if (!category) return '';
    return category
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

/**
 * Show specific section
 */
function showSection(sectionName) {
    // Clear loading interval
    if (loadingInterval) {
        clearInterval(loadingInterval);
        loadingInterval = null;
    }

    // Hide all sections
    elements.uploadSection.style.display = 'none';
    elements.loadingSection.style.display = 'none';
    elements.resultsSection.style.display = 'none';
    elements.errorSection.style.display = 'none';

    // Show requested section
    switch (sectionName) {
        case 'upload':
            elements.uploadSection.style.display = 'block';
            break;
        case 'loading':
            elements.loadingSection.style.display = 'block';
            break;
        case 'results':
            elements.resultsSection.style.display = 'block';
            break;
        case 'error':
            elements.errorSection.style.display = 'block';
            break;
    }
}

/**
 * Show error message
 */
function showError(message) {
    elements.errorText.textContent = message;
    showSection('error');
}

// ========================================
// ACTION BUTTONS
// ========================================

// New analysis button
elements.newAnalysisBtn.addEventListener('click', () => {
    clearFileSelection();
    elements.emailInput.value = '';
    showSection('upload');
});

// Retry button
elements.retryBtn.addEventListener('click', () => {
    showSection('upload');
});

// ========================================
// SCROLL TO TOP
// ========================================
document.getElementById('scrollToTop')?.addEventListener('click', (e) => {
    e.preventDefault();
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

// ========================================
// INITIALIZATION
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('AI Audit Agent Frontend Initialized');
    console.log('Backend URL:', API_BASE_URL);

    // Show upload section by default
    showSection('upload');
});

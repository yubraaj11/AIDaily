const API_BASE_URL = "http://localhost:8000/ai-daily/v1";
const MAX_SUMMARY_LENGTH = 500;
const SUMMARY_PLACEHOLDER = "Detailed summary will appear here after clicking 'View Details' or 'Summarize Paper' on a paper.";

// DOM Elements
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeBtn = document.querySelector('.close-btn');
const apiKeyInput = document.getElementById('apiKeyInput');
const saveApiKeyBtn = document.getElementById('saveApiKeyBtn');
const clearApiKeyBtn = document.getElementById('clearApiKeyBtn');
const todayPaperContainer = document.getElementById('todayPaperContainer');
const loadingState = document.getElementById('loadingState');
const recentPapersContainer = document.getElementById('recentPapersContainer');
const loadingRecent = document.getElementById('loadingRecent');
const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');
const timeFilterRadios = document.querySelectorAll('input[name="timeFilter"]');

// State variables
let apiKey = localStorage.getItem('aiDailyApiKey') || '';
let selectedPaperId = '';

// Initialize marked.js for markdown parsing
if (typeof marked !== 'undefined') {
    marked.setOptions({
        breaks: true,
        gfm: true
    });
}

// Initialize the app
function init() {
    // Set up event listeners
    settingsBtn.addEventListener('click', openSettings);
    closeBtn.addEventListener('click', closeSettings);
    window.addEventListener('click', closeOutsideModal);
    saveApiKeyBtn.addEventListener('click', saveApiKey);
    clearApiKeyBtn.addEventListener('click', clearApiKey);
    refreshHistoryBtn.addEventListener('click', loadRecentPapers);

    // Load initial data
    loadTodayPaper();
    loadRecentPapers();

    // Add event listener for filter changes
    timeFilterRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            loadRecentPapers();
        });
    });
}

// Open settings modal
function openSettings() {
    settingsModal.style.display = 'flex';
    apiKeyInput.value = apiKey;
}

// Close settings modal
function closeSettings() {
    settingsModal.style.display = 'none';
}

// Close modal if clicked outside
function closeOutsideModal(event) {
    if (event.target === settingsModal) {
        closeSettings();
    }
}

// Save API key
function saveApiKey() {
    const newApiKey = apiKeyInput.value.trim();
    if (!newApiKey) {
        Swal.fire({
            title: 'Error!',
            text: 'Please enter a valid API key.',
            icon: 'error',
            confirmButtonText: 'OK'
        });
        return;
    }

    apiKey = newApiKey;
    localStorage.setItem('aiDailyApiKey', apiKey);
    closeSettings();
    Swal.fire({
        title: 'Success!',
        text: 'API key saved successfully. You can now use the summarization feature.',
        icon: 'success',
        confirmButtonText: 'OK'
    });
}

// Clear API key
function clearApiKey() {
    Swal.fire({
        title: 'Are you sure?',
        text: 'This will remove your saved API key and disable summarization features.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#6b7280',
        confirmButtonText: 'Yes, clear it!',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            apiKey = '';
            localStorage.removeItem('aiDailyApiKey');
            apiKeyInput.value = '';
            closeSettings();
            Swal.fire({
                title: 'Cleared!',
                text: 'Your API key has been cleared.',
                icon: 'success',
                confirmButtonText: 'OK'
            });
        }
    });
}

// Convert text to markdown HTML
function parseMarkdown(text) {
    if (typeof marked !== 'undefined') {
        return marked.parse(text);
    }
    // Fallback for basic markdown parsing if marked.js fails to load
    return text
        .replace(/### (.*$)/gm, '<h3>$1</h3>')
        .replace(/## (.*$)/gm, '<h2>$1</h2>')
        .replace(/# (.*$)/gm, '<h1>$1</h1>')
        .replace(/\*\*(.*)\*\*/gm, '<strong>$1</strong>')
        .replace(/\*(.*)\*/gm, '<em>$1</em>')
        .replace(/\n/gm, '<br>');
}

// Load today's paper
async function loadTodayPaper() {
    try {
        loadingState.style.display = 'block';
        todayPaperContainer.innerHTML = '';

        const response = await fetch(`${API_BASE_URL}/today`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();
        const papers = data.papers || [];

        if (papers.length === 0) {
            todayPaperContainer.innerHTML = '<p>No papers found for today.</p>';
            return;
        }

        const paper = papers[0];
        const title = paper.title || 'Untitled';
        const authors = formatAuthors(paper.authors || []);
        const summary = paper.summary || 'No summary available';
        const pdfUrl = paper.pdf_url || '#';
        const paperId = paper.id || '';
        const cachedDetailed = paper.summarized_text || '';

        // Create HTML content
        const paperHtml = `
            <h2 class="card-title">${title}</h2>
            <p class="card-subtitle">${authors}</p>
            <div class="abstract-container">
                <h4>Abstract</h4>
                <p>${summary}</p>
            </div>
            <div class="btn-group">
                <button class="btn btn-primary" onclick="openPDF('${pdfUrl}')">Read Full Text</button>
                <button id="summarizeBtn" class="btn btn-secondary" onclick="summarizePaper('${paperId}')">
                    Summarize Paper
                </button>
            </div>
            <div class="accordion">
                <div class="accordion-header" onclick="toggleAccordion('detailedSummary')">
                    <span>Detailed Summary</span>
                    <span id="detailedSummaryToggle" class="arrow">▼</span>
                </div>
                <div id="detailedSummary" class="accordion-body active">
                    <div id="detailedSummaryContent" class="markdown-content">
                        ${cachedDetailed ? parseMarkdown(cachedDetailed) : SUMMARY_PLACEHOLDER}
                    </div>
                </div>
            </div>
        `;

        todayPaperContainer.innerHTML = paperHtml;

        // Update buttons based on state
        updateButtonStates(pdfUrl, cachedDetailed);

    } catch (error) {
        console.error('Error fetching today\'s paper:', error);
        todayPaperContainer.innerHTML = `<p>Error loading today's paper: ${error.message}</p>`;
    } finally {
        loadingState.style.display = 'none';
    }
}

// Load recent papers
async function loadRecentPapers() {
    try {
        loadingRecent.style.display = 'block';
        recentPapersContainer.innerHTML = '';

        // Get selected filter: 7, 30, or 0 (0 = all time)
        const days = parseInt(document.querySelector('input[name="timeFilter"]:checked').value);
        let dateRangeParam = 'all';
        if (days === 7 || days === 30) dateRangeParam = days;

        // Fetch filtered history from API
        const response = await fetch(`${API_BASE_URL}/history?date_range=${dateRangeParam}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();
        const history = data.history || {};

        // Sort dates in descending order
        const sortedDates = Object.keys(history).sort((a, b) => new Date(b) - new Date(a));

        // Generate HTML for each date
        let htmlContent = '';
        for (const date of sortedDates) {
            const papers = history[date];
            if (!papers || papers.length === 0) continue;

            const formattedDate = new Date(date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            htmlContent += `<div class="date-section">
                <div class="date-header">
                    <span>📅 ${formattedDate}</span>
                </div>
            </div>`;

            // Limit to 5 papers per date
            for (const paper of papers.slice(0, 5)) {
                const title = paper.title || 'Untitled';
                const authors = formatAuthors(paper.authors || []);
                const pid = paper.id || '';
                const pdfUrl = paper.pdf_url || '#';

                htmlContent += `
                    <div class="paper-card">
                        <div class="paper-info">
                            <div class="paper-title">${title}</div>
                            <div class="paper-authors">${authors}</div>
                        </div>
                        <div class="paper-actions">
                            <button class="paper-btn paper-btn-primary" onclick="viewPaperDetails('${pid}')">View Details</button>
                            <button class="paper-btn paper-btn-success" onclick="openPDF('${pdfUrl}')">Read Full Text</button>
                        </div>
                    </div>
                `;
            }
        }

        if (htmlContent === '') {
            htmlContent = '<p>No recent papers available.</p>';
        }

        recentPapersContainer.innerHTML = htmlContent;

    } catch (error) {
        console.error('Error fetching recent papers:', error);
        recentPapersContainer.innerHTML = `<p>Error loading recent papers: ${error.message}</p>`;
    } finally {
        loadingRecent.style.display = 'none';
    }
}


// Format authors list
function formatAuthors(authors) {
    if (!authors || authors.length === 0) return 'Unknown authors';
    if (authors.length === 1) return authors[0];
    if (authors.length === 2) return `${authors[0]} and ${authors[1]}`;
    return `${authors[0]} et al.`;
}

// Toggle accordion
function toggleAccordion(id) {
    const element = document.getElementById(id);
    const toggle = document.getElementById(`${id}Toggle`);

    if (element.classList.contains('active')) {
        element.classList.remove('active');
        toggle.textContent = '▼';
    } else {
        element.classList.add('active');
        toggle.textContent = '▲';
    }
}

// Update button states
function updateButtonStates(pdfUrl, hasSummary) {
    const readFullBtn = document.querySelector('.btn-primary');
    const summarizeBtn = document.getElementById('summarizeBtn');

    if (readFullBtn) {
        const hasPdf = pdfUrl && pdfUrl !== '#' && pdfUrl !== '';
        readFullBtn.disabled = !hasPdf;
        if (!hasPdf) {
            readFullBtn.style.opacity = '0.5';
            readFullBtn.style.cursor = 'not-allowed';
        } else {
            readFullBtn.style.opacity = '1';
            readFullBtn.style.cursor = 'pointer';
        }
    }

    if (summarizeBtn) {
        const canSummarize = apiKey && pdfUrl && pdfUrl !== '#' && pdfUrl !== '';
        summarizeBtn.disabled = !canSummarize;
        if (!canSummarize) {
            summarizeBtn.style.opacity = '0.5';
            summarizeBtn.style.cursor = 'not-allowed';
            if (!apiKey) {
                summarizeBtn.innerHTML = '🔑 API Key Required';
            } else if (!pdfUrl || pdfUrl === '#' || pdfUrl === '') {
                summarizeBtn.innerHTML = '📄 No PDF Available';
            }
        } else {
            summarizeBtn.style.opacity = '1';
            summarizeBtn.style.cursor = 'pointer';
            summarizeBtn.innerHTML = hasSummary ? 'Re-summarize Paper' : 'Summarize Paper';
        }
    }
}

// View paper details
async function viewPaperDetails(paperId) {
    try {
        selectedPaperId = paperId;
        const response = await fetch(`${API_BASE_URL}/paper/${paperId}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();
        const paper = data.paper || {};

        const title = paper.title || 'Untitled';
        const authors = formatAuthors(paper.authors || []);
        const summary = paper.summary || 'No summary available';
        const pdfUrl = paper.pdf_url || '#';
        const cachedDetailed = paper.summarized_text || '';

        // Update today's paper section
        const paperHtml = `
            <h2 class="card-title">${title}</h2>
            <p class="card-subtitle">${authors}</p>
            <div class="abstract-container">
                <h4>Abstract</h4>
                <p>${summary}</p>
            </div>
            <div class="btn-group">
                <button class="btn btn-primary" onclick="openPDF('${pdfUrl}')">Read Full Text</button>
                <button id="summarizeBtn" class="btn btn-secondary" onclick="summarizePaper('${paperId}')">
                    Summarize Paper
                </button>
            </div>
            <div class="accordion">
                <div class="accordion-header" onclick="toggleAccordion('detailedSummary')">
                    <span>Detailed Summary</span>
                    <span id="detailedSummaryToggle" class="arrow">▼</span>
                </div>
                <div id="detailedSummary" class="accordion-body active">
                    <div id="detailedSummaryContent" class="markdown-content">
                        ${cachedDetailed ? parseMarkdown(cachedDetailed) : SUMMARY_PLACEHOLDER}
                    </div>
                </div>
            </div>
        `;

        todayPaperContainer.innerHTML = paperHtml;

        // Update buttons based on state
        updateButtonStates(pdfUrl, !!cachedDetailed);

        // Scroll to top
        todayPaperContainer.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        console.error('Error loading paper details:', error);
        Swal.fire({
            title: 'Error!',
            text: `Error loading paper details: ${error.message}`,
            icon: 'error',
            confirmButtonText: 'OK'
        });
    }
}

// Summarize paper
async function summarizePaper(paperId) {
    if (!apiKey) {
        Swal.fire({
            title: 'API Key Required',
            text: 'Please enter your Gemini API key in the settings to use the summarization feature.',
            icon: 'warning',
            confirmButtonText: 'Open Settings',
            showCancelButton: true,
            cancelButtonText: 'Cancel'
        }).then((result) => {
            if (result.isConfirmed) {
                openSettings();
            }
        });
        return;
    }

    if (!paperId) {
        Swal.fire({
            title: 'Error!',
            text: 'Paper ID is required for summarization.',
            icon: 'error',
            confirmButtonText: 'OK'
        });
        return;
    }

    const summarizeBtn = document.getElementById('summarizeBtn');
    const originalBtnContent = summarizeBtn.innerHTML;

    try {
        // Show loading state
        summarizeBtn.disabled = true;
        summarizeBtn.innerHTML = '<span class="loading-spinner"></span>Generating Summary...';

        const response = await fetch(`${API_BASE_URL}/summarize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                api_key: apiKey,
                paper_id: paperId
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const summarizedText = data.paper?.summarized_text || 'No summary available';

        // Update the detailed summary content with markdown parsing
        const detailedSummaryContent = document.getElementById('detailedSummaryContent');
        if (detailedSummaryContent) {
            detailedSummaryContent.innerHTML = parseMarkdown(summarizedText);
        }

        // Show the accordion if it's hidden
        const detailedSummary = document.getElementById('detailedSummary');
        const detailedSummaryToggle = document.getElementById('detailedSummaryToggle');
        if (detailedSummary && !detailedSummary.classList.contains('active')) {
            detailedSummary.classList.add('active');
            if (detailedSummaryToggle) {
                detailedSummaryToggle.textContent = '▲';
            }
        }

        Swal.fire({
            title: 'Success!',
            text: 'Paper summarized successfully. The detailed summary has been updated below.',
            icon: 'success',
            confirmButtonText: 'OK'
        });

    } catch (error) {
        console.error('Error summarizing paper:', error);
        Swal.fire({
            title: 'Error!',
            text: `Failed to summarize paper: ${error.message}`,
            icon: 'error',
            confirmButtonText: 'OK'
        });
    } finally {
        // Reset button state
        if (summarizeBtn) {
            summarizeBtn.disabled = false;
            summarizeBtn.innerHTML = 'Re-summarize Paper';
        }
    }
}

// Open PDF
function openPDF(pdfUrl) {
    if (!pdfUrl || pdfUrl === '#' || pdfUrl === '') {
        Swal.fire({
            title: 'No PDF Available',
            text: 'This paper does not have a PDF link available.',
            icon: 'info',
            confirmButtonText: 'OK'
        });
        return;
    }

    try {
        window.open(pdfUrl, '_blank', 'noopener,noreferrer');
    } catch (error) {
        console.error('Error opening PDF:', error);
        Swal.fire({
            title: 'Error!',
            text: 'Unable to open PDF. Please check the URL or try again later.',
            icon: 'error',
            confirmButtonText: 'OK'
        });
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', init);

// Export functions for use in the HTML
window.viewPaperDetails = viewPaperDetails;
window.summarizePaper = summarizePaper;
window.openPDF = openPDF;
window.toggleAccordion = toggleAccordion;
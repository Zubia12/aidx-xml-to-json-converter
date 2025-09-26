/**
 * AIDX XML to JSON Converter - Frontend JavaScript
 * 
 * This script handles:
 * - Drag and drop functionality for XML files
 * - File validation and processing
 * - AJAX communication with Flask backend
 * - Side-by-side comparison display
 * - Progress tracking and user feedback
 * - Toast notifications and error handling
 */

class AIDXConverter {
    constructor() {
        // Initialize application state
        this.selectedFiles = new Map();
        this.convertedData = new Map();
        this.isProcessing = false;
        
        // Initialize DOM elements
        this.initializeElements();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize the application
        this.init();
    }

    /**
     * Initialize DOM element references
     */
    initializeElements() {
        // File upload elements
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.browseLink = document.getElementById('browseLink');
        this.fileList = document.getElementById('fileList');
        this.filesContainer = document.getElementById('filesContainer');
        
        // Action buttons
        this.convertBtn = document.getElementById('convertBtn');
        this.clearBtn = document.getElementById('clearBtn');
        
        // Comparison elements
        this.comparisonSection = document.getElementById('comparisonSection');
        this.fileSelector = document.getElementById('fileSelector');
        this.xmlContent = document.getElementById('xmlContent');
        this.jsonContent = document.getElementById('jsonContent');
        this.xmlFileSize = document.getElementById('xmlFileSize');
        this.xmlLineCount = document.getElementById('xmlLineCount');
        this.jsonFileSize = document.getElementById('jsonFileSize');
        this.jsonLineCount = document.getElementById('jsonLineCount');
        
        // Control buttons
        this.downloadJson = document.getElementById('downloadJson');
        this.copyJson = document.getElementById('copyJson');
        
        // Statistics elements
        this.statsSection = document.getElementById('statsSection');
        this.totalFiles = document.getElementById('totalFiles');
        this.successRate = document.getElementById('successRate');
        this.totalSize = document.getElementById('totalSize');
        this.processingTime = document.getElementById('processingTime');
        
        // Loading and status elements
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.loadingText = document.getElementById('loadingText');
        this.progressFill = document.getElementById('progressFill');
        this.status = document.getElementById('status');
        this.toastContainer = document.getElementById('toastContainer');
    }

    /**
     * Set up all event listeners
     */
    setupEventListeners() {
        // Drag and drop events
        this.dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
        this.dropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.dropZone.addEventListener('drop', this.handleDrop.bind(this));
        this.dropZone.addEventListener('click', () => this.fileInput.click());
        
        // File input events
        this.browseLink.addEventListener('click', (e) => {
            e.preventDefault();
            this.fileInput.click();
        });
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        
        // Action button events
        this.convertBtn.addEventListener('click', this.convertFiles.bind(this));
        this.clearBtn.addEventListener('click', this.clearAllFiles.bind(this));
        
        // Comparison events
        this.fileSelector.addEventListener('change', this.displayComparison.bind(this));
        this.downloadJson.addEventListener('click', this.downloadJsonFile.bind(this));
        this.copyJson.addEventListener('click', this.copyJsonToClipboard.bind(this));
        
        // Prevent default drag behaviors on document
        document.addEventListener('dragover', (e) => e.preventDefault());
        document.addEventListener('drop', (e) => e.preventDefault());
    }

    /**
     * Initialize the application
     */
    init() {
        this.updateStatus('Ready');
        this.showToast('Welcome to AIDX XML to JSON Converter!', 'info');
    }

    /**
     * Handle drag over events
     */
    handleDragOver(e) {
        e.preventDefault();
        this.dropZone.classList.add('drag-over');
    }

    /**
     * Handle drag leave events
     */
    handleDragLeave(e) {
        e.preventDefault();
        if (!this.dropZone.contains(e.relatedTarget)) {
            this.dropZone.classList.remove('drag-over');
        }
    }

    /**
     * Handle file drop events
     */
    handleDrop(e) {
        e.preventDefault();
        this.dropZone.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files);
        this.processFiles(files);
    }

    /**
     * Handle file selection from input
     */
    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.processFiles(files);
    }

    /**
     * Process and validate selected files
     */
    processFiles(files) {
        const xmlFiles = files.filter(file => {
            const isXML = file.name.toLowerCase().endsWith('.xml');
            if (!isXML) {
                this.showToast(`Skipped "${file.name}" - Only XML files are supported`, 'warning');
            }
            return isXML;
        });

        if (xmlFiles.length === 0) {
            this.showToast('No valid XML files selected', 'error');
            return;
        }

        // Add files to selection
        xmlFiles.forEach(file => {
            if (!this.selectedFiles.has(file.name)) {
                this.selectedFiles.set(file.name, file);
                this.showToast(`Added "${file.name}" to conversion queue`, 'success');
            } else {
                this.showToast(`"${file.name}" is already in the queue`, 'info');
            }
        });

        this.updateFileList();
        this.updateStatus(`${this.selectedFiles.size} file(s) ready for conversion`);
    }

    /**
     * Update the file list display
     */
    updateFileList() {
        if (this.selectedFiles.size === 0) {
            this.fileList.style.display = 'none';
            return;
        }

        this.fileList.style.display = 'block';
        this.filesContainer.innerHTML = '';

        this.selectedFiles.forEach((file, fileName) => {
            const fileItem = this.createFileItem(file, fileName);
            this.filesContainer.appendChild(fileItem);
        });
    }

    /**
     * Create a file item element
     */
    createFileItem(file, fileName) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        
        const fileSize = this.formatFileSize(file.size);
        
        fileItem.innerHTML = `
            <div class="file-info">
                <div class="file-icon">
                    <i class="fas fa-file-code"></i>
                </div>
                <div class="file-details">
                    <h5>${fileName}</h5>
                    <p>${fileSize} • XML File</p>
                </div>
            </div>
            <div class="file-actions">
                <button class="btn-icon" onclick="aidxConverter.removeFile('${fileName}')" title="Remove file">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        return fileItem;
    }

    /**
     * Remove a file from the selection
     */
    removeFile(fileName) {
        this.selectedFiles.delete(fileName);
        this.convertedData.delete(fileName);
        this.updateFileList();
        this.updateFileSelector();
        
        if (this.selectedFiles.size === 0) {
            this.updateStatus('Ready');
            this.comparisonSection.style.display = 'none';
            this.statsSection.style.display = 'none';
        } else {
            this.updateStatus(`${this.selectedFiles.size} file(s) ready for conversion`);
        }
        
        this.showToast(`Removed "${fileName}" from queue`, 'info');
    }

    /**
     * Clear all selected files
     */
    clearAllFiles() {
        this.selectedFiles.clear();
        this.convertedData.clear();
        this.updateFileList();
        this.updateFileSelector();
        this.comparisonSection.style.display = 'none';
        this.statsSection.style.display = 'none';
        this.updateStatus('Ready');
        this.showToast('All files cleared', 'info');
    }

    /**
     * Convert all selected files
     */
    async convertFiles() {
        if (this.selectedFiles.size === 0) {
            this.showToast('No files selected for conversion', 'warning');
            return;
        }

        if (this.isProcessing) {
            this.showToast('Conversion already in progress', 'info');
            return;
        }

        this.isProcessing = true;
        this.showLoading('Converting XML files to JSON...');
        this.updateStatus('Converting...');
        
        const startTime = Date.now();
        let successCount = 0;
        let totalSize = 0;

        try {
            const files = Array.from(this.selectedFiles.values());
            
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const progress = ((i + 1) / files.length) * 100;
                
                this.updateProgress(progress);
                this.updateLoadingText(`Processing ${file.name}...`);
                
                try {
                    const result = await this.convertSingleFile(file);
                    this.convertedData.set(file.name, result);
                    successCount++;
                    totalSize += file.size;
                } catch (error) {
                    console.error(`Error converting ${file.name}:`, error);
                    this.showToast(`Failed to convert "${file.name}": ${error.message}`, 'error');
                }
            }
            
            const endTime = Date.now();
            const processingTime = endTime - startTime;
            
            this.hideLoading();
            this.updateFileSelector();
            this.displayStatistics(successCount, files.length, totalSize, processingTime);
            
            if (successCount > 0) {
                this.comparisonSection.style.display = 'block';
                this.statsSection.style.display = 'block';
                this.showToast(`Successfully converted ${successCount}/${files.length} files`, 'success');
                this.updateStatus(`Converted ${successCount}/${files.length} files`);
            } else {
                this.showToast('No files were successfully converted', 'error');
                this.updateStatus('Conversion failed');
            }
            
        } catch (error) {
            this.hideLoading();
            this.showToast(`Conversion failed: ${error.message}`, 'error');
            this.updateStatus('Conversion failed');
        } finally {
            this.isProcessing = false;
        }
    }

    /**
     * Convert a single file using the backend API
     */
    async convertSingleFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/convert', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        return result;
    }

    /**
     * Update the file selector dropdown
     */
    updateFileSelector() {
        this.fileSelector.innerHTML = '<option value="">Select a file to view</option>';
        
        this.convertedData.forEach((data, fileName) => {
            const option = document.createElement('option');
            option.value = fileName;
            option.textContent = fileName;
            this.fileSelector.appendChild(option);
        });
    }

    /**
     * Display side-by-side comparison
     */
    async displayComparison() {
        const selectedFile = this.fileSelector.value;
        
        if (!selectedFile || !this.convertedData.has(selectedFile)) {
            this.xmlContent.innerHTML = '<code class="language-xml">Select a file to view XML content</code>';
            this.jsonContent.innerHTML = '<code class="language-json">JSON output will appear here after conversion</code>';
            return;
        }
        
        const file = this.selectedFiles.get(selectedFile);
        const convertedData = this.convertedData.get(selectedFile);
        
        try {
            // Display XML content
            const xmlText = await this.readFileAsText(file);
            this.displayXMLContent(xmlText, file.size);
            
            // Display JSON content
            this.displayJSONContent(convertedData.json_data, convertedData.json_data);
            
        } catch (error) {
            this.showToast(`Error displaying file content: ${error.message}`, 'error');
        }
    }

    /**
     * Read file as text
     */
    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }

    /**
     * Display XML content with syntax highlighting
     */
    displayXMLContent(xmlText, fileSize) {
        const lines = xmlText.split('\n').length;
        const formattedXML = this.escapeHtml(xmlText);
        
        this.xmlContent.innerHTML = `<code class="language-xml">${formattedXML}</code>`;
        this.xmlFileSize.textContent = this.formatFileSize(fileSize);
        this.xmlLineCount.textContent = `${lines} lines`;
    }

    /**
     * Display JSON content with syntax highlighting
     */
    displayJSONContent(jsonData, rawJsonString) {
        const jsonString = typeof jsonData === 'string' ? jsonData : JSON.stringify(jsonData, null, 2);
        const lines = jsonString.split('\n').length;
        const jsonSize = new Blob([jsonString]).size;
        
        const formattedJSON = this.highlightJSON(jsonString);
        
        this.jsonContent.innerHTML = `<code class="language-json">${formattedJSON}</code>`;
        this.jsonFileSize.textContent = this.formatFileSize(jsonSize);
        this.jsonLineCount.textContent = `${lines} lines`;
    }

    /**
     * Simple JSON syntax highlighting
     */
    highlightJSON(jsonString) {
        return this.escapeHtml(jsonString)
            .replace(/(".*?")\s*:/g, '<span style="color: #9f7efe;">$1</span>:')
            .replace(/:\s*(".*?")/g, ': <span style="color: #06d6a0;">$1</span>')
            .replace(/:\s*(\d+\.?\d*)/g, ': <span style="color: #ffd166;">$1</span>')
            .replace(/:\s*(true|false|null)/g, ': <span style="color: #f72585;">$1</span>');
    }

    /**
     * Escape HTML characters
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Download JSON file
     */
    downloadJsonFile() {
        const selectedFile = this.fileSelector.value;
        
        if (!selectedFile || !this.convertedData.has(selectedFile)) {
            this.showToast('No file selected for download', 'warning');
            return;
        }
        
        const convertedData = this.convertedData.get(selectedFile);
        const jsonString = JSON.stringify(convertedData.json_data, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = selectedFile.replace('.xml', '.json');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showToast(`Downloaded "${a.download}"`, 'success');
    }

    /**
     * Copy JSON to clipboard
     */
    async copyJsonToClipboard() {
        const selectedFile = this.fileSelector.value;
        
        if (!selectedFile || !this.convertedData.has(selectedFile)) {
            this.showToast('No file selected for copying', 'warning');
            return;
        }
        
        const convertedData = this.convertedData.get(selectedFile);
        const jsonString = JSON.stringify(convertedData.json_data, null, 2);
        
        try {
            await navigator.clipboard.writeText(jsonString);
            this.showToast('JSON copied to clipboard', 'success');
        } catch (error) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = jsonString;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showToast('JSON copied to clipboard', 'success');
        }
    }

    /**
     * Display conversion statistics
     */
    displayStatistics(successCount, totalCount, totalSize, processingTime) {
        const successRate = totalCount > 0 ? Math.round((successCount / totalCount) * 100) : 0;
        
        this.totalFiles.textContent = totalCount;
        this.successRate.textContent = `${successRate}%`;
        this.totalSize.textContent = this.formatFileSize(totalSize);
        this.processingTime.textContent = `${processingTime}ms`;
    }

    /**
     * Show loading overlay
     */
    showLoading(message) {
        this.loadingText.textContent = message;
        this.progressFill.style.width = '0%';
        this.loadingOverlay.style.display = 'flex';
    }

    /**
     * Hide loading overlay
     */
    hideLoading() {
        this.loadingOverlay.style.display = 'none';
    }

    /**
     * Update loading text
     */
    updateLoadingText(text) {
        this.loadingText.textContent = text;
    }

    /**
     * Update progress bar
     */
    updateProgress(percentage) {
        this.progressFill.style.width = `${percentage}%`;
    }

    /**
     * Update status indicator
     */
    updateStatus(status) {
        this.status.textContent = status;
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };
        
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="${icons[type]}"></i>
            </div>
            <div class="toast-content">
                <h4>${titles[type]}</h4>
                <p>${message}</p>
            </div>
        `;
        
        this.toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
        
        // Remove on click
        toast.addEventListener('click', () => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        });
    }

    /**
     * Format file size for display
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aidxConverter = new AIDXConverter();
});

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    if (window.aidxConverter) {
        window.aidxConverter.showToast('An unexpected error occurred', 'error');
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
    if (window.aidxConverter) {
        window.aidxConverter.showToast('An unexpected error occurred', 'error');
    }
});
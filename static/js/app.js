// =========================================
// AI LOAN APPROVAL — SIDEBAR LAYOUT JS
// =========================================

document.addEventListener("DOMContentLoaded", () => {

    // ======== SIDEBAR NAVIGATION ========
    const navItems = document.querySelectorAll(".nav-item");
    const sections = document.querySelectorAll(".content-section");

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();

            // Update active nav
            navItems.forEach(n => n.classList.remove("active"));
            item.classList.add("active");

            // Show matching section
            const target = item.getAttribute("data-section");
            sections.forEach(s => s.classList.remove("active"));
            const targetSection = document.getElementById("section-" + target);
            if (targetSection) targetSection.classList.add("active");

            // Close sidebar on mobile
            closeMobileSidebar();
        });
    });

    // ======== MOBILE SIDEBAR TOGGLE ========
    const sidebar = document.getElementById("sidebar");
    const toggle = document.getElementById("sidebarToggle");
    const overlay = document.getElementById("sidebarOverlay");

    function closeMobileSidebar() {
        sidebar.classList.remove("open");
        overlay.classList.remove("open");
    }

    toggle.addEventListener("click", () => {
        sidebar.classList.toggle("open");
        overlay.classList.toggle("open");
    });

    overlay.addEventListener("click", closeMobileSidebar);

    // ======== LIVE EMI PREVIEW ========
    const previewRate = document.getElementById("previewRate");
    const previewEMI = document.getElementById("previewEMI");
    const previewRatio = document.getElementById("previewRatio");
    const previewTotal = document.getElementById("previewTotal");

    function calcEMI(P, rate, n) {
        const r = rate / (12 * 100);
        if (r === 0) return P / n;
        return (P * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
    }

    function updatePreview() {
        const income = parseInt(document.getElementById("income").value) || 0;
        const loanAmount = parseInt(document.getElementById("loan_amount").value) || 0;
        const loanTerm = parseInt(document.getElementById("loan_term").value) || 1;
        const purpose = document.getElementById("purpose").value;

        let interest;
        if (purpose === "Home") {
            interest = income > 50000 ? 8 : 10;
        } else if (purpose === "Auto") {
            interest = 10;
        } else {
            interest = 12;
        }

        const emi = calcEMI(loanAmount, interest, loanTerm);
        const total = emi * loanTerm;
        const ratio = income > 0 ? emi / income : 0;

        previewRate.textContent = interest + "%";
        previewEMI.textContent = "₹" + Math.round(emi).toLocaleString("en-IN");
        previewTotal.textContent = "₹" + Math.round(total).toLocaleString("en-IN");
        previewRatio.textContent = (ratio * 100).toFixed(1) + "%";

        // Color-code the ratio
        if (ratio > 0.5) {
            previewRatio.style.color = "#ef4444";
        } else if (ratio > 0.35) {
            previewRatio.style.color = "#f59e0b";
        } else {
            previewRatio.style.color = "#22c55e";
        }
    }

    // Attach preview listeners to all relevant inputs
    ["income", "loan_amount", "loan_term", "purpose"].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener("input", updatePreview);
            el.addEventListener("change", updatePreview);
        }
    });

    updatePreview(); // initial calculation

    // ======== FORM SUBMISSION ========
    const form = document.getElementById("loanForm");
    const submitBtn = document.getElementById("submitBtn");
    const btnText = submitBtn.querySelector(".btn-text");
    const btnLoader = submitBtn.querySelector(".btn-loader");
    const resultPanel = document.getElementById("resultPanel");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Switch to prediction section
        navItems.forEach(n => n.classList.remove("active"));
        document.querySelector('[data-section="predict"]').classList.add("active");
        sections.forEach(s => s.classList.remove("active"));
        document.getElementById("section-predict").classList.add("active");

        // Loading state
        btnText.style.display = "none";
        btnLoader.style.display = "inline-flex";
        submitBtn.disabled = true;
        resultPanel.style.display = "none";

        // Hide instruction card
        const instructionCard = document.querySelector(".instruction-card");
        if (instructionCard) instructionCard.style.display = "none";

        const payload = {
            age: document.getElementById("age").value,
            income: document.getElementById("income").value,
            loan_amount: document.getElementById("loan_amount").value,
            credit_score: document.getElementById("credit_score").value,
            months_employed: document.getElementById("months_employed").value,
            num_credit_lines: document.getElementById("num_credit_lines").value,
            loan_term: document.getElementById("loan_term").value,
            purpose: document.getElementById("purpose").value
        };

        try {
            const resp = await fetch("/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await resp.json();
            renderResult(data);

        } catch (err) {
            renderResult({
                status: "error",
                reason: "Server unreachable. Please try again."
            });
        }

        // Reset loading
        btnText.style.display = "inline-flex";
        btnLoader.style.display = "none";
        submitBtn.disabled = false;

        // Close sidebar on mobile after submit
        closeMobileSidebar();
    });

    // ======== RENDER RESULT ========
    function renderResult(data) {
        let html = "";

        if (data.status === "approved") {
            html = `
                <div class="result-card approved">
                    <div class="result-status">
                        <div class="result-status-icon">✅</div>
                        <div class="result-status-text">
                            <h3>Loan Approved</h3>
                            <p>Congratulations! Your loan application has been approved by our AI model.</p>
                        </div>
                    </div>

                    <div class="result-metrics">
                        <div class="metric-box">
                            <div class="metric-label">Monthly EMI</div>
                            <div class="metric-value">₹${data.emi.toLocaleString("en-IN")}</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-label">Interest Rate</div>
                            <div class="metric-value">${data.interest_rate}%</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-label">EMI Ratio</div>
                            <div class="metric-value">${(data.emi_ratio * 100).toFixed(1)}%</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-label">Approval Prob.</div>
                            <div class="metric-value">${data.probability}%</div>
                        </div>
                    </div>

                    <div class="prob-bar-container">
                        <div class="prob-bar-label">
                            <span>Approval Probability</span>
                            <span>${data.probability}%</span>
                        </div>
                        <div class="prob-bar">
                            <div class="prob-bar-fill good" id="probBarFill" style="width: 0"></div>
                        </div>
                    </div>

                    ${data.details && data.details.length > 0 ? `
                        <div class="result-details">
                            <h4>Assessment Details</h4>
                            ${data.details.map(d => `
                                <div class="detail-item">
                                    <span class="check">✔</span> <span>${d}</span>
                                </div>
                            `).join("")}
                        </div>
                    ` : ""}
                </div>
            `;
        } else if (data.status === "rejected") {
            const report = data.report;

            html = `
                <div class="result-card rejected">
                    <div class="result-status">
                        <div class="result-status-icon">❌</div>
                        <div class="result-status-text">
                            <h3>Loan Rejected</h3>
                            <p>${data.reason || "Your application did not meet the approval criteria."}</p>
                        </div>
                    </div>

                    ${data.details && data.details.length > 0 ? `
                        <div class="result-details">
                            <h4>Rejection Reasons</h4>
                            ${data.details.map(d => `
                                <div class="detail-item">
                                    <span class="cross">✗</span> <span>${d}</span>
                                </div>
                            `).join("")}
                        </div>
                    ` : ""}
                </div>

                ${report ? `
                <!-- ======== REJECTION REPORT ======== -->
                <div class="rejection-report" id="rejectionReport">
                    <div class="report-header">
                        <div class="report-header-icon">📋</div>
                        <div>
                            <h3>Detailed Rejection Report</h3>
                            <p class="report-timestamp">Generated on ${new Date().toLocaleString("en-IN", { dateStyle: "long", timeStyle: "short" })}</p>
                        </div>
                    </div>

                    <!-- Summary -->
                    <div class="report-summary">
                        <div class="report-summary-icon">💡</div>
                        <p>${report.summary}</p>
                    </div>

                    <!-- Rejection Reasons -->
                    <div class="report-section">
                        <h4><span class="report-section-icon">⚠️</span> Why Was Your Loan Rejected?</h4>
                        <div class="report-reasons-grid">
                            ${report.rejection_reasons.map(r => `
                                <div class="report-reason-card">
                                    <div class="reason-title">
                                        <span class="reason-dot"></span>
                                        ${r.title}
                                    </div>
                                    <p class="reason-description">${r.description}</p>
                                    <div class="reason-comparison">
                                        <div class="comparison-item yours">
                                            <span class="comparison-label">Your Value</span>
                                            <span class="comparison-value">${r.your_value}</span>
                                        </div>
                                        <div class="comparison-arrow">→</div>
                                        <div class="comparison-item required">
                                            <span class="comparison-label">Required</span>
                                            <span class="comparison-value">${r.required}</span>
                                        </div>
                                    </div>
                                </div>
                            `).join("")}
                        </div>
                    </div>

                    <!-- Applicant Snapshot -->
                    <div class="report-section">
                        <h4><span class="report-section-icon">👤</span> Your Application Snapshot</h4>
                        <div class="snapshot-grid">
                            ${Object.entries(report.applicant_snapshot).map(([key, val]) => `
                                <div class="snapshot-item">
                                    <span class="snapshot-label">${key}</span>
                                    <span class="snapshot-value">${val}</span>
                                </div>
                            `).join("")}
                        </div>
                    </div>

                    <!-- Suggestions -->
                    <div class="report-section">
                        <h4><span class="report-section-icon">✅</span> What Can You Do Next?</h4>
                        <div class="suggestions-list">
                            ${report.suggestions.map((s, i) => `
                                <div class="suggestion-item">
                                    <span class="suggestion-number">${i + 1}</span>
                                    <span class="suggestion-text">${s}</span>
                                </div>
                            `).join("")}
                        </div>
                    </div>

                    <div class="report-footer">
                        <p>📞 Need Help? Contact our support team for personalized guidance on improving your eligibility.</p>
                    </div>
                </div>
                ` : ""}
            `;
        } else {
            html = `
                <div class="result-card error">
                    <div class="result-status">
                        <div class="result-status-icon">⚠️</div>
                        <div class="result-status-text">
                            <h3>Error</h3>
                            <p>${data.reason || "An unexpected error occurred."}</p>
                        </div>
                    </div>
                </div>
            `;
        }

        resultPanel.innerHTML = html;
        resultPanel.style.display = "block";

        // Smooth scroll to result
        resultPanel.scrollIntoView({ behavior: "smooth", block: "center" });

        // Animate probability bar
        setTimeout(() => {
            const fill = document.getElementById("probBarFill");
            if (fill && data.probability !== undefined) {
                fill.style.width = data.probability + "%";
            }
        }, 150);
    }
});

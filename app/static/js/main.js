async function fetchPosition() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error("Geolocation not supported"));
            return;
        }

        const tryOptions = [
            { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 },
            { enableHighAccuracy: false, timeout: 30000, maximumAge: 60000 }
        ];

        const runAttempt = (index) => {
            navigator.geolocation.getCurrentPosition(
                (pos) =>
                    resolve({
                        latitude: pos.coords.latitude,
                        longitude: pos.coords.longitude
                    }),
                (err) => {
                    if (index < tryOptions.length - 1) {
                        runAttempt(index + 1);
                        return;
                    }
                    reject(err);
                },
                tryOptions[index]
            );
        };

        runAttempt(0);
    });
}

async function apiPost(url, payload) {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    return { ok: res.ok, data: await res.json() };
}

function formatRadiusMessage(payload, fallbackMessage) {
    const base = payload?.error || fallbackMessage;
    const distance = payload?.distance_meters;
    const allowed = payload?.allowed_radius_meters;
    const entryWindow = payload?.allowed_entry_window_minutes;
    if (entryWindow !== undefined) {
        return `${base} (Entry window: ${entryWindow} minutes)`;
    }
    if (distance !== undefined && allowed !== undefined) {
        return `${base} (Your distance: ${distance}m, Allowed: ${allowed}m)`;
    }
    if (distance !== undefined) {
        return `${base} (Your distance: ${distance}m)`;
    }
    return base;
}

function formatGeoError(err) {
    if (err?.message?.includes("HTTPS")) {
        return err.message;
    }
    if (err?.code === 1) {
        return "📍 Location permission denied. Please allow location access and try again.";
    }
    if (err?.code === 2) {
        return "📡 Location unavailable. Please turn on GPS and try from an open area.";
    }
    if (err?.code === 3) {
        return "⏱️ Location request timed out. Please retry.";
    }
    return "❌ Unable to get GPS location. Please check your device settings.";
}

function initCharts() {
    if (window.studentChartData && document.getElementById("studentChart")) {
        new Chart(document.getElementById("studentChart"), {
            type: "line",
            data: {
                labels: window.studentChartData.labels,
                datasets: [{ label: "Minutes", data: window.studentChartData.values, borderColor: "#0d6efd", fill: false }]
            }
        });
    }

    if (window.teacherChartData && document.getElementById("teacherChart")) {
        new Chart(document.getElementById("teacherChart"), {
            type: "bar",
            data: {
                labels: window.teacherChartData.labels,
                datasets: [{ label: "Entries", data: window.teacherChartData.values, backgroundColor: "#198754" }]
            }
        });
    }
}

async function initScanForm() {
    const form = document.getElementById("scanForm");
    if (!form) return;
    const result = document.getElementById("scanResult");
    const tokenInput = document.getElementById("qrToken");
    const scannerContainer = document.getElementById("qrScanner");

    const host = window.location.hostname;
    const canUseCameraQr = window.isSecureContext || host === "localhost" || host === "127.0.0.1";

    if (scannerContainer && window.Html5QrcodeScanner && canUseCameraQr) {
        const vw = Math.max(320, window.innerWidth || 320);
        const qrSize = Math.min(300, Math.max(160, Math.floor(vw * 0.62)));
        const scanner = new Html5QrcodeScanner("qrScanner", {
            fps: 10,
            qrbox: { width: qrSize, height: qrSize }
        }, false);
        scanner.render((decodedText) => {
            tokenInput.value = decodedText;
        }, () => {});
    } else if (scannerContainer && !canUseCameraQr) {
        scannerContainer.className = "alert alert-warning small";
        scannerContainer.textContent =
            "Camera scan works only on HTTPS. Paste QR token manually below.";
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        result.textContent = "Marking attendance...";
        const qrToken = tokenInput.value.trim();
        try {
            const pos = await fetchPosition();
            const response = await apiPost("/api/scan-entry", {
                qr_token: qrToken,
                latitude: pos.latitude,
                longitude: pos.longitude
            });
            if (!response.ok) {
                result.className = "text-danger";
                result.textContent = formatRadiusMessage(
                    response.data,
                    "Failed to mark attendance."
                );
                return;
            }
            result.className = "text-success";
            result.textContent = "Thank you! Entry marked successfully.";
            localStorage.setItem("activeSessionId", String(response.data.session_id));
            localStorage.setItem("presenceCheckNonce", "0");
        } catch (err) {
            result.className = "text-danger";
            result.textContent = formatGeoError(err);
        }
    });
}

async function sendPresencePing(sessionId) {
    const pos = await fetchPosition();
    const response = await apiPost(`/api/presence/${sessionId}`, pos);
    if (!response.ok) {
        throw new Error(response.data.error || "Presence ping failed");
    }
    return response.data;
}

async function initPresenceLoop() {
    try {
        const stateRes = await fetch("/api/my-active-session");
        const state = await stateRes.json();
        if (state.active) {
            localStorage.setItem("activeSessionId", String(state.session_id));
            localStorage.setItem("presenceCheckNonce", String(state.presence_check_nonce || 0));
        }
    } catch (e) {
        // Ignore silent bootstrap failure.
    }

    const sessionId = localStorage.getItem("activeSessionId");
    if (!sessionId) return;

    const tick = async () => {
        try {
            const data = await sendPresencePing(sessionId);
            if (data.status && data.status !== "in_class") {
                localStorage.removeItem("activeSessionId");
            }
        } catch (e) {
            // Presence ping failures are tolerated temporarily.
        }

        try {
            const stateRes = await fetch("/api/my-active-session");
            const state = await stateRes.json();
            if (!state.active) {
                localStorage.removeItem("activeSessionId");
                return;
            }
            const oldNonce = Number(localStorage.getItem("presenceCheckNonce") || "0");
            const newNonce = Number(state.presence_check_nonce || 0);
            if (newNonce > oldNonce) {
                localStorage.setItem("presenceCheckNonce", String(newNonce));
                await sendPresencePing(state.session_id);
            }
        } catch (e) {
            // Ignore.
        }
    };

    tick();
    setInterval(tick, 45000);
}

async function initLiveTable() {
    const table = document.getElementById("liveStudentsTable");
    if (!table) return;
    const sessionId = table.dataset.sessionId;
    const tbody = table.querySelector("tbody");
    
    // Counter elements
    const totalCount = document.getElementById("totalStudentsCount");
    const inClassCount = document.getElementById("inClassCount");
    const exitedCount = document.getElementById("exitedCount");
    const lastUpdate = document.getElementById("lastUpdateTime");
    const liveIndicator = document.getElementById("liveIndicator");

    let refreshCount = 0;

    const refresh = async () => {
        try {
            // Pulse indicator
            if (liveIndicator) {
                liveIndicator.style.opacity = "0.5";
            }
            
            const res = await fetch(`/api/session/${sessionId}/live`);
            const payload = await res.json();
            
            tbody.innerHTML = "";
            
            let inClass = 0;
            let exited = 0;
            
            if (payload.students && payload.students.length > 0) {
                payload.students.forEach((s, index) => {
                    const statusClass = s.status === "in_class" ? "success" : "secondary";
                    const statusText = s.status === "in_class" ? "In Class" : s.status.replace(/_/g, " ");
                    
                    if (s.status === "in_class") inClass++;
                    else exited++;
                    
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${index + 1}</td>
                        <td><strong>${s.name}</strong></td>
                        <td class="small text-muted">${s.email}</td>
                        <td class="small">${formatDateTime(s.entry_time)}</td>
                        <td class="small">${formatDateTime(s.last_seen_at)}</td>
                        <td><span class="badge bg-${statusClass} status-badge">${statusText}</span></td>
                        <td><strong>${s.total_minutes}</strong> min</td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                const tr = document.createElement("tr");
                tr.innerHTML = `<td colspan="7" class="text-center text-muted">No students have marked attendance yet</td>`;
                tbody.appendChild(tr);
            }
            
            // Update counters
            if (totalCount) totalCount.textContent = payload.students.length;
            if (inClassCount) inClassCount.textContent = inClass;
            if (exitedCount) exitedCount.textContent = exited;
            if (lastUpdate) lastUpdate.textContent = new Date().toLocaleTimeString();
            
            // Restore indicator
            if (liveIndicator) {
                liveIndicator.style.opacity = "1";
            }
            
            refreshCount++;
        } catch (error) {
            console.error("Failed to refresh live data:", error);
            if (liveIndicator) {
                liveIndicator.textContent = "● ERROR";
                liveIndicator.className = "badge bg-danger";
            }
        }
    };

    const formatDateTime = (isoString) => {
        if (!isoString || isoString === "-") return "-";
        try {
            const date = new Date(isoString);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch {
            return isoString;
        }
    };

    refresh();
    setInterval(refresh, 5000); // Refresh every 5 seconds
}

async function initTeacherDashboardLive() {
    const totalEntriesEl = document.getElementById("teacherTotalEntries");
    const totalMinutesEl = document.getElementById("teacherTotalMinutes");
    const titleEl = document.getElementById("teacherActiveSessionTitle");
    const metaEl = document.getElementById("teacherActiveSessionMeta");
    const countWrapEl = document.getElementById("teacherActiveSessionCountWrap");
    const countEl = document.getElementById("teacherActiveSessionCount");
    if (!totalEntriesEl || !totalMinutesEl || !titleEl || !metaEl) return;

    const refresh = async () => {
        const res = await fetch("/api/teacher/summary");
        if (!res.ok) return;
        const data = await res.json();
        totalEntriesEl.textContent = data.total_entries;
        totalMinutesEl.textContent = data.total_minutes;

        const active = data.active_session;
        if (active && active.id) {
            titleEl.textContent = active.title || "Active";
            metaEl.innerHTML = `${active.room || ""} • <span class="badge text-bg-success">Live</span>`;
            if (countWrapEl) countWrapEl.style.display = "";
            if (countEl) countEl.textContent = active.count ?? 0;
        } else {
            titleEl.textContent = "None";
            metaEl.textContent = "No active session";
            if (countWrapEl) countWrapEl.style.display = "none";
        }
    };

    refresh();
    setInterval(refresh, 5000);
}

async function initSessionScanPage() {
    const btn = document.getElementById("markSessionAttendanceBtn");
    if (!btn) return;
    const result = document.getElementById("scanSessionResult");
    const sessionId = btn.dataset.sessionId;
    const alreadyExpired = btn.disabled;
    if (alreadyExpired) {
        return;
    }

    const markAttendance = async (autoRun = false) => {
        btn.disabled = true;
        result.className = "small mb-3";
        result.innerHTML = `
            <div class="alert alert-info">
                <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                ${autoRun ? 'Auto-marking attendance...' : 'Verifying your location...'}
            </div>
        `;
        
        try {
            const pos = await fetchPosition();
            const response = await apiPost(`/api/scan-session/${sessionId}`, pos);
            if (!response.ok) {
                result.className = "small mb-3";
                result.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>❌ Attendance Failed</strong><br>
                        ${formatRadiusMessage(response.data, "Attendance could not be marked.")}
                    </div>
                `;
                btn.disabled = false;
                return;
            }
            result.className = "small mb-3";
            result.innerHTML = `
                <div class="alert alert-success">
                    <strong>✅ Success!</strong><br>
                    Your attendance has been marked successfully. Redirecting...
                </div>
            `;
            localStorage.setItem("activeSessionId", String(response.data.session_id));
            localStorage.setItem("presenceCheckNonce", "0");
            
            // Success animation
            btn.innerHTML = '✅ Attendance Marked!';
            btn.className = 'btn btn-success w-100';
            
            setTimeout(() => {
                window.location.href = "/student/dashboard";
            }, 2000);
        } catch (e) {
            result.className = "small mb-3";
            result.innerHTML = `
                <div class="alert alert-warning">
                    <strong>⚠️ Location Error</strong><br>
                    ${formatGeoError(e)}<br>
                    <small class="text-muted">Note: Location check is disabled for demo. You can still mark attendance.</small>
                </div>
            `;
            btn.disabled = false;
        }
    };

    // Auto mark attendance immediately when scan page opens.
    markAttendance(true);

    // Keep manual retry button available if auto-mark fails.
    btn.addEventListener("click", async () => {
        await markAttendance(false);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initCharts();
    initScanForm();
    initPresenceLoop();
    initLiveTable();
    initSessionScanPage();
    initTeacherDashboardLive();
});

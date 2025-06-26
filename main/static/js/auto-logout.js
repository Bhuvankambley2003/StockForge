/**
 * Auto Logout Script
 * This script handles automatic logout after a period of inactivity.
 * Improved version with better error handling, logging, and prevention of multiple initializations.
 */

function setupAutoLogout() {
    // Prevent multiple initializations
    if (window.autoLogoutInitialized) {
        console.log("Auto logout already initialized, skipping duplicate initialization");
        return;
    }
    window.autoLogoutInitialized = true;
    
    console.log("Setting up auto logout system at:", new Date().toISOString());
    
    let inactivityTimer;
    const inactivityLimit = 60 * 60 * 1000; // 60 minutes of inactivity
    const warningTime = 5 * 60 * 1000; // 5 minutes before logout
    
    // Create a timestamp to track when the session should expire
    let sessionExpireTime = Date.now() + inactivityLimit;

    // Function to reset the timer with better logging
    function resetTimer(eventType) {
        clearTimeout(inactivityTimer);
        sessionExpireTime = Date.now() + inactivityLimit;
        
        if (eventType) {
            console.log(`Activity detected (${eventType}). Session timer reset.`);
        }
        
        // Set timer to show warning before logout
        inactivityTimer = setTimeout(showWarning, inactivityLimit - warningTime);
    }
    
    // Function to show the warning dialog
    function showWarning() {
        console.log("Showing timeout warning at:", new Date().toISOString());
        
        // Create warning dialog if it doesn't exist
        if (!document.getElementById('timeout-warning')) {
            const warningDiv = document.createElement('div');
            warningDiv.id = 'timeout-warning';
            warningDiv.style.position = 'fixed';
            warningDiv.style.top = '50%';
            warningDiv.style.left = '50%';
            warningDiv.style.transform = 'translate(-50%, -50%)';
            warningDiv.style.backgroundColor = 'var(--bg-card, white)';
            warningDiv.style.color = 'var(--text-primary, black)';
            warningDiv.style.padding = '20px';
            warningDiv.style.borderRadius = '8px';
            warningDiv.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
            warningDiv.style.zIndex = '1000';
            warningDiv.style.textAlign = 'center';
            warningDiv.style.width = '350px';
            warningDiv.style.border = '1px solid var(--border-light, #e2e8f0)';
            
            warningDiv.innerHTML = `
                <h3 style="margin-bottom: 15px; color: var(--text-primary, black);">Session Timeout Warning</h3>
                <p style="margin-bottom: 20px;">Your session will expire in 5 minutes due to inactivity.</p>
                <div>
                    <button id="stay-logged-in" class="btn btn-primary" style="margin-right: 10px; padding: 8px 16px; background-color: #3b82f6; color: white; border: none; border-radius: 4px;">Stay Logged In</button>
                    <button id="logout-now" style="padding: 8px 16px; background-color: transparent; border: 1px solid #e2e8f0; border-radius: 4px;">Logout Now</button>
                </div>
                <div id="timeout-countdown" style="margin-top: 15px; font-size: 12px; color: #64748b;"></div>
            `;
            
            document.body.appendChild(warningDiv);
            
            // Stay logged in button
            document.getElementById('stay-logged-in').addEventListener('click', function() {
                console.log("User clicked 'Stay Logged In' button");
                
                // Make an AJAX request to refresh the session
                fetch('/refresh-session/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    },
                    credentials: 'same-origin'
                })
                .then(response => {
                    if (response.ok) {
                        console.log("Session refreshed successfully");
                        // Hide the warning
                        document.getElementById('timeout-warning').style.display = 'none';
                        // Reset the timer
                        resetTimer('manual-refresh');
                    } else {
                        console.error("Failed to refresh session:", response.status);
                        // Try to reset timer anyway
                        resetTimer('manual-refresh-fallback');
                    }
                })
                .catch(error => {
                    console.error("Error refreshing session:", error);
                    // Still hide dialog and reset timer as fallback
                    document.getElementById('timeout-warning').style.display = 'none';
                    resetTimer('manual-refresh-error-fallback');
                });
            });
            
            // Logout now button
            document.getElementById('logout-now').addEventListener('click', function() {
                console.log("User clicked 'Logout Now' button");
                window.location.href = '/logout/';
            });
            
            // Start the countdown
            let secondsLeft = Math.floor(warningTime / 1000);
            const countdownElement = document.getElementById('timeout-countdown');
            
            const updateCountdown = function() {
                const minutes = Math.floor(secondsLeft / 60);
                const seconds = secondsLeft % 60;
                countdownElement.textContent = `Session expires in: ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
                
                if (secondsLeft <= 0) {
                    console.log("Countdown complete, logging out user");
                    // Redirect to logout
                    window.location.href = '/logout/';
                } else {
                    secondsLeft--;
                    setTimeout(updateCountdown, 1000);
                }
            };
            
            updateCountdown();
        } else {
            console.log("Warning dialog already exists, making visible");
            document.getElementById('timeout-warning').style.display = 'block';
        }
    }
    
    // Function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Activity detection function with event type tracking
    function activityDetected(event) {
        resetTimer(event.type);
    }
    
    // Watch for mouse, keyboard, or touch events to reset the timer
    window.addEventListener('mousemove', activityDetected);
    window.addEventListener('mousedown', activityDetected);
    window.addEventListener('keypress', activityDetected);
    window.addEventListener('scroll', activityDetected);
    window.addEventListener('touchmove', activityDetected);
    
    // Initialize the timer when the page loads
    console.log("Initializing auto-logout timer. Session will expire at:", 
                new Date(sessionExpireTime).toISOString());
    resetTimer('initial');
}

// Call the setup function when the document is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, setting up auto-logout system");
    setupAutoLogout();
});

// Add backup initialization in case the DOMContentLoaded event already fired
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    console.log("Document already loaded, setting up auto-logout system as fallback");
    setTimeout(setupAutoLogout, 100);
}
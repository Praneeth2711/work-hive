document.addEventListener('DOMContentLoaded', () => {
    // GSAP Setup & Global State
    gsap.registerPlugin(Flip);
    let isNavigating = false;
    // ... translations object ...
    
    // --- NAVIGATION LOGIC (largely unchanged) ---
    const navigateTo = (targetPageId) => {
        // ... navigation logic is the same, no changes needed
    };

    // --- EVENT LISTENERS ---
    document.body.addEventListener('click', (e) => {
        const target = e.target;
        
        // Navigation clicks
        const navTarget = target.closest('[data-target]');
        if (navTarget) {
            // Check if it's a login button to handle special logic
            if (target.closest('.login-btn')) {
                handleLogin(target.closest('.login-btn'));
            } else {
                navigateTo(navTarget.dataset.target);
            }
        }
        
        // Language Toggle (unchanged)
        const langBtn = target.closest('[data-lang]');
        if (langBtn) { /* ... */ }
    });

    // --- NEW: OTP Input Logic ---
    const otpGroups = document.querySelectorAll('.otp-group');
    otpGroups.forEach(group => {
        const inputs = group.querySelectorAll('.otp-input');
        inputs.forEach((input, index) => {
            input.addEventListener('input', () => {
                if (input.value.length === 1 && index + 1 < inputs.length) {
                    inputs[index + 1].focus();
                }
            });
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Backspace' && input.value.length === 0 && index > 0) {
                    inputs[index - 1].focus();
                }
            });
        });
    });

    // --- NEW: LOGIN BUTTON ANIMATION HANDLER ---
    const handleLogin = (button) => {
        if (button.classList.contains('is-loading')) return;
        
        // 1. Show Loading State
        button.classList.add('is-loading');

        // 2. Fake network delay (simulating login)
        setTimeout(() => {
            // 3. Show Success State
            button.classList.remove('is-loading');
            button.classList.add('is-success');

            // 4. Navigate to the next page after a short success delay
            setTimeout(() => {
                navigateTo(button.dataset.target);

                // 5. Reset button for future use
                // Important to do this *after* navigation so user doesn't see it reset
                setTimeout(() => {
                     button.classList.remove('is-success');
                }, 500);

            }, 800);
            
        }, 1500);
    };

    // --- Other Feature Logic & Initialization (unchanged) ---
    // const switchLanguage = (lang) => { /* ... */ };
    // setupVoiceRecognition(); // if you keep this feature
});
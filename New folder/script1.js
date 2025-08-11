document.addEventListener('DOMContentLoaded', () => {
    // Register the GSAP Flip plugin
    gsap.registerPlugin(Flip);

    // --- DOM & State Management ---
    const ui = {
        themeToggle: document.getElementById('theme-toggle'),
        soundToggle: document.getElementById('sound-toggle'),
        // ... (many more element references)
    };
    const sfx = {
        hover: document.getElementById('sfx-hover'),
        // ... (sound references)
    };
    let state = {
        isAnimating: false,
        isSoundMuted: false,
    };
    
    // --- 1. INITIALIZATION ---
    function init() {
        setupEventListeners();
        initialLoadAnimation();
        // Additional setup functions can be called here
    }

    // --- 2. SETUP EVENT LISTENERS ---
    function setupEventListeners() {
        ui.themeToggle.addEventListener('click', handleThemeToggle);
        ui.soundToggle.addEventListener('click', handleSoundToggle);
        
        // Add hover sounds to all interactive elements
        document.querySelectorAll('button, .role-card, a').forEach(el => {
            el.addEventListener('mouseenter', () => playSound(sfx.hover));
        });

        // Add click sounds
        // ...
        
        // Event listeners for role cards, change role, forgot password, etc.
        // ...
        
        // Listener for password strength meter
        document.querySelectorAll('.password-input').forEach(input => {
            input.addEventListener('input', handlePasswordInput);
        });
    }

    // --- 3. CORE HANDLERS & FEATURE LOGIC ---

    function handleThemeToggle() {
        const currentTheme = document.body.dataset.theme;
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.body.dataset.theme = newTheme;
        ui.themeToggle.textContent = newTheme === 'light' ? '☀️' : '🌙';
    }

    function handleSoundToggle() {
        state.isSoundMuted = !state.isSoundMuted;
        ui.soundToggle.style.opacity = state.isSoundMuted ? 0.5 : 1;
    }
    
    function playSound(audioElement) {
        if (!state.isSoundMuted) {
            audioElement.currentTime = 0;
            audioElement.play();
        }
    }

    function handlePasswordInput(event) {
        const input = event.target;
        const meter = input.closest('.password-group').querySelector('.password-strength-meter');
        // ... (logic to check password strength and update meter class/width) ...
    }

    // Handle Forgot Password link click (3D Flip)
    function handleForgotPassword() {
        const card = ui.morphContainer;
        card.classList.add('is-flipped');
        playSound(sfx.click);
    }
    
    function handleBackToLogin() {
        // ... reverses the flip ...
    }

    function handleLogin(event) {
        if (state.isAnimating) return;
        state.isAnimating = true;

        const button = event.target;
        button.classList.add('is-loading');
        playSound(sfx.click);

        // Fake network delay
        setTimeout(() => {
            // Success animation
            gsap.timeline({ onComplete: () => {
                // Here you would redirect the user
                console.log('Login successful! Redirecting...');
                state.isAnimating = false;
                button.classList.remove('is-loading');
            }})
            .to(button.closest('.login-form').querySelectorAll('.form-group, .form-title, .form-actions, .btn-change-role'), {
                opacity: 0, scale: 0.95, stagger: 0.1, duration: 0.3
            })
            .to(button, {
                width: '60px', height: '60px', borderRadius: '50%', text: '', duration: 0.4, ease: 'power4.in'
            })
            .set(button, { backgroundColor: 'var(--success)', text: '✓' }) // Show checkmark
            .to(button, { scale: 1.2, duration: 0.2, ease: 'elastic.out(1, 0.5)' });
        }, 1500);
    }

    // --- 4. ANIMATION LOGIC (Forward and Backward) ---

    // Initial load animation, role card selection, etc., remain similar
    // but now integrate calls to `playSound()` and manage the `isAnimating` state.

    // ...

    // New "Change Role" Animation (Faster)
    function handleChangeRole() {
        if (state.isAnimating) return;
        state.isAnimating = true;
        playSound(sfx.click);
        // ... (uses the faster, more direct GSAP timeline as developed in the previous step) ...
    }


    // --- KICK IT OFF ---
    init();
});
document.addEventListener('DOMContentLoaded', () => {
    const themeSwitcher = document.getElementById('theme-switcher');
    const body = document.body;
    
    // Load saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
    } else {
        body.classList.remove('dark-mode');
    }

    // Theme switcher button functionality (with icon change)
    if (themeSwitcher) { 
        themeSwitcher.addEventListener('click', () => {
            if (body.classList.contains('dark-mode')) {
                body.classList.remove('dark-mode');
                localStorage.setItem('theme', 'light');
                themeSwitcher.innerHTML = '<i class="fas fa-sun"></i>'; // Changed to only icon
            } else {
                body.classList.add('dark-mode');
                localStorage.setItem('theme', 'dark');
                themeSwitcher.innerHTML = '<i class="fas fa-moon"></i>'; // Changed to only icon
            }
        });
        // Initial icon setting on page load (only icon)
        if (body.classList.contains('dark-mode')) {
            themeSwitcher.innerHTML = '<i class="fas fa-moon"></i>';
        } else {
            themeSwitcher.innerHTML = '<i class="fas fa-sun"></i>';
        }
    }
    
    // Share button logic (example for quiz_result.html)
    const shareButton = document.getElementById('share-quiz-button');
    if (shareButton) { 
        shareButton.addEventListener('click', () => {
            const quizUrl = window.location.href; 
            const quizTitle = document.title; 
            
            if (navigator.share) {
                navigator.share({
                    title: quizTitle,
                    url: quizUrl
                }).then(() => {
                    console.log('Thanks for sharing!');
                })
                .catch(error => { 
                    console.error('Sharing failed:', error);
                });
            } else {
                navigator.clipboard.writeText(quizUrl).then(() => {
                    alert(`এই কুইজটি শেয়ার করতে নিচের লিঙ্কটি কপি করুন:\n${quizUrl}\nলিঙ্ক কপি করা হয়েছে!`);
                }).catch(err => {
                    console.error('লিঙ্ক কপি করতে ব্যর্থ:', err);
                    alert(`এই কুইজটি শেয়ার করতে নিচের লিঙ্কটি কপি করুন:\n${quizUrl}`);
                });
            }
        });
    }

    // --- Mobile Menu Toggle Logic ---
    const menuToggleIcon = document.querySelector('.menu-toggle-icon');
    const mobileMenuContainer = document.getElementById('mobile-menu');
    const desktopSearchBar = document.getElementById('desktop-search-bar'); // Desktop search bar
    const mobileOnlySearchBar = document.getElementById('mobile-search-bar'); // The search bar *inside* mobile menu

    if (menuToggleIcon && mobileMenuContainer) {
        menuToggleIcon.addEventListener('click', () => {
            mobileMenuContainer.classList.toggle('active');
            if (mobileMenuContainer.classList.contains('active')) {
                menuToggleIcon.querySelector('i').classList.replace('fa-bars', 'fa-times'); // Change to X icon
                // When menu is active, hide desktop search
                if (desktopSearchBar) desktopSearchBar.style.display = 'none';
                // Show mobileOnlySearchBar (inside menu)
                if (mobileOnlySearchBar) mobileOnlySearchBar.style.display = 'flex'; 
            } else {
                menuToggleIcon.querySelector('i').classList.replace('fa-times', 'fa-bars'); // Change back to bars
                // When menu is inactive, hide mobileOnlySearchBar
                if (mobileOnlySearchBar) mobileOnlySearchBar.style.display = 'none'; 

                // Restore desktop search bar display (only if on desktop)
                if (window.innerWidth > 600) { 
                    if (desktopSearchBar) desktopSearchBar.style.display = 'flex';
                } else { // Mobile view: desktop search bar should be hidden
                    if (desktopSearchBar) desktopSearchBar.style.display = 'none'; 
                }
            }
        });
    }

    // --- Hide/show elements based on window resize (for desktop to mobile transition) ---
    window.addEventListener('resize', () => {
        if (window.innerWidth > 600) { // Desktop view
            // Hide mobile-only elements on desktop
            if (mobileMenuContainer) mobileMenuContainer.classList.remove('active');
            if (menuToggleIcon) menuToggleIcon.querySelector('i').classList.replace('fa-times', 'fa-bars');
            
            // Ensure desktop search is visible and mobile-only search is hidden
            if (desktopSearchBar) desktopSearchBar.style.display = 'flex'; 
            if (mobileOnlySearchBar) mobileOnlySearchBar.style.display = 'none'; 
            
            // Revert theme switcher icon
            if (themeSwitcher) {
                if (body.classList.contains('dark-mode')) {
                    themeSwitcher.innerHTML = '<i class="fas fa-moon"></i>';
                } else {
                    themeSwitcher.innerHTML = '<i class="fas fa-sun"></i>';
                }
            }
        } else { // Mobile view (<= 600px)
            // Ensure desktop search is hidden
            if (desktopSearchBar) desktopSearchBar.style.display = 'none'; 
            // Show burger icon
            if (menuToggleIcon) menuToggleIcon.style.display = 'block'; 
            // Ensure mobile-only search bar is hidden by default (unless active)
            if (mobileOnlySearchBar && mobileOnlySearchBar.style.display !== 'flex') {
                mobileOnlySearchBar.style.display = 'none';
            }
        }
    });

});
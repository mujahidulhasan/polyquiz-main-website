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
    const desktopSearchBar = document.getElementById('desktop-search-bar');
    const mobileSearchIcon = document.querySelector('.mobile-search-icon'); // Standalone search icon in header
    const mobileOnlySearchBar = document.getElementById('mobile-search-bar'); // The search bar *inside* mobile menu
    const headerLogoImage = document.querySelector('.header-logo-image'); // Get the logo element


    if (menuToggleIcon && mobileMenuContainer) {
        menuToggleIcon.addEventListener('click', () => {
            mobileMenuContainer.classList.toggle('active');
            if (mobileMenuContainer.classList.contains('active')) {
                menuToggleIcon.querySelector('i').classList.replace('fa-bars', 'fa-times'); // Change to X icon
                // When menu is active, hide desktop search and mobile search icon (as search is now inside menu)
                if (desktopSearchBar) desktopSearchBar.style.display = 'none';
                if (mobileSearchIcon) mobileSearchIcon.style.display = 'none'; 
                // Ensure mobileOnlySearchBar is visible when menu is active
                if (mobileOnlySearchBar) mobileOnlySearchBar.style.display = 'flex';
            } else {
                menuToggleIcon.querySelector('i').classList.replace('fa-times', 'fa-bars'); // Change back to bars
                // When menu is inactive, mobile-only search bar should be hidden
                if (mobileOnlySearchBar) mobileOnlySearchBar.style.display = 'none'; 

                // Revert display for mobileSearchIcon based on screen size
                if (window.innerWidth <= 600) { 
                    if (mobileSearchIcon) mobileSearchIcon.style.display = 'block'; // Show mobile search icon
                }
                // desktopSearchBar should remain hidden on mobile view
                if (desktopSearchBar) desktopSearchBar.style.display = 'none';
            }
        });
    }

    // --- Mobile Search Icon Click Logic (for the standalone search icon on mobile header) ---
    // Note: The desktop search bar is now the one shown inside the mobile menu.
    if (mobileSearchIcon && desktopSearchBar && mobileOnlySearchBar) { 
        mobileSearchIcon.addEventListener('click', () => {
            // Toggle visibility of the mobile-only search bar (inside the menu)
            if (window.innerWidth <= 600) { // Only if on mobile view
                if (mobileOnlySearchBar.style.display === 'flex') { // If the mobileOnlySearchBar is currently visible
                    mobileOnlySearchBar.style.display = 'none';
                    mobileSearchIcon.querySelector('i').classList.replace('fa-times', 'fa-search'); // Change to search icon
                } else {
                    mobileOnlySearchBar.style.display = 'flex'; // Show the search bar
                    mobileSearchIcon.querySelector('i').classList.replace('fa-search', 'fa-times'); // Change to X icon
                }
                // Ensure the mobile menu is closed when search is opened
                if (mobileMenuContainer && mobileMenuContainer.classList.contains('active')) {
                    mobileMenuContainer.classList.remove('active');
                    if (menuToggleIcon) menuToggleIcon.querySelector('i').classList.replace('fa-times', 'fa-bars'); 
                }
                // desktopSearchBar should remain hidden on mobile view
                if (desktopSearchBar) desktopSearchBar.style.display = 'none';
            }
        });
    }

    // --- Prevent logo click from triggering search ---
    if (headerLogoImage) { // Check if logo element exists
        headerLogoImage.addEventListener('click', (event) => {
            // If the mobile-only search bar is visible, and the click is on the logo, prevent default behavior
            // This prevents the logo from inadvertently closing/opening the search bar
            if (window.innerWidth <= 600 && mobileOnlySearchBar && mobileOnlySearchBar.style.display === 'flex') {
                // If it's an actual click to toggle search, the mobileSearchIcon listener will handle it.
                // If it's a logo click that happens to be on top of the search icon, this prevents propagation.
                event.stopPropagation(); // Stop the event from bubbling up to parent elements
            }
        });
    }


    // --- Hide/show mobile menu/search based on window resize (for desktop to mobile transition) ---
    window.addEventListener('resize', () => {
        if (window.innerWidth > 600) {
            // Hide mobile-only elements on desktop
            if (mobileMenuContainer) mobileMenuContainer.classList.remove('active');
            if (menuToggleIcon) menuToggleIcon.querySelector('i').classList.replace('fa-times', 'fa-bars');
            
            // Ensure desktop search is visible and mobile search icon is hidden
            if (desktopSearchBar) desktopSearchBar.style.display = 'flex'; 
            if (mobileSearchIcon) mobileSearchIcon.style.display = 'none'; 
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
            // Show mobile search icon (unless internal search is open)
            // if (mobileSearchIcon && (!mobileOnlySearchBar || mobileOnlySearchBar.style.display !== 'flex')) { // Re-evaluating this based on user's exact need
            //     mobileSearchIcon.style.display = 'block'; 
            // }
            // CHANGED: mobileSearchIcon should only appear when the menu is NOT active and search is NOT open.
            // When menu is open, its search bar is visible. So, mobileSearchIcon should be hidden.
            if (mobileSearchIcon) mobileSearchIcon.style.display = 'none'; // Initially hide, let CSS handle it
            if (menuToggleIcon) menuToggleIcon.style.display = 'block'; // Show burger icon
            // Ensure mobile-only search bar is hidden by default (unless active)
            if (mobileOnlySearchBar && mobileOnlySearchBar.style.display !== 'flex') {
                mobileOnlySearchBar.style.display = 'none';
            }
        }
    });

});
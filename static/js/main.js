document.addEventListener('DOMContentLoaded', () => {
    const themeSwitcher = document.getElementById('theme-switcher');
    const body = document.body;
    const themeLink = document.querySelector('.theme-link'); // Assuming night_mode.css

    // Load saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
    } else {
        // Default to light mode if nothing saved or 'default'
        body.classList.remove('dark-mode');
    }

    themeSwitcher.addEventListener('click', () => {
        if (body.classList.contains('dark-mode')) {
            body.classList.remove('dark-mode');
            localStorage.setItem('theme', 'light');
        } else {
            body.classList.add('dark-mode');
            localStorage.setItem('theme', 'dark');
        }
    });

    // Share button logic (example for quiz_result.html)
    const shareButton = document.getElementById('share-quiz-button');
    if (shareButton) {
        shareButton.addEventListener('click', () => {
            const quizUrl = window.location.href; // Current page URL
            const quizTitle = document.title; // Page title

            if (navigator.share) {
                navigator.share({
                    title: quizTitle,
                    url: quizUrl
                }).then(() => {
                    console.log('Thanks for sharing!');
                })
                .catch(console.error);
            } else {
                // Fallback for browsers that don't support Web Share API
                alert(`এই কুইজটি শেয়ার করতে নিচের লিঙ্কটি কপি করুন:\n${quizUrl}`);
                navigator.clipboard.writeText(quizUrl).then(() => {
                    alert('লিঙ্ক কপি করা হয়েছে!');
                }).catch(err => {
                    console.error('লিঙ্ক কপি করতে ব্যর্থ:', err);
                });
            }
        });
    }
});
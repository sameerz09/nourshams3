// Vanilla JS solution with no dependencies
document.addEventListener('DOMContentLoaded', function() {
    function hideNewButton() {
        // All possible selectors
        var selectors = [
            '.o_calendar_button_new',
            '.o-calendar-button-new',
            'button[title="New Event"]',
            'button[name="action_create"]',
            'button[data-original-title="New Event"]',
            'button i.fa-plus', // Button with plus icon
            'button span:contains("New")' // Button with "New" text
        ];

        selectors.forEach(function(selector) {
            var buttons = document.querySelectorAll(selector);
            buttons.forEach(function(button) {
                // Go up to the button element if we matched child elements
                var btn = button.closest('button') || button;
                btn.style.cssText = 'display: none !important; width: 0 !important; height: 0 !important;';
            });
        });
    }

    // Run immediately and every second as fallback
    hideNewButton();
    setInterval(hideNewButton, 1000);
});
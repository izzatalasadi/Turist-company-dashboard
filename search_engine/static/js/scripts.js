$(document).ready(function () {
    restoreButtonStates()
    fetchAndDisplayStats();
    updateLocalStateAndUI();

    // Setup CSRF token for AJAX requests
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", $('meta[name="csrf-token"]').attr('content'));
            }
        }
    });
    
    // Function to restore the state of buttons from local storage
    function restoreButtonStates() {
        const buttonStates = JSON.parse(localStorage.getItem('buttonStates') || '{}');
        Object.entries(buttonStates).forEach(([bookingNumber, state]) => {
            toggleButtons(bookingNumber, state.status);
            // Consider whether you need to sync the local state with the server here
        });
    }

    // Function to save the state of a button to local storage
    function saveButtonState(bookingNumber, status) {
        const buttonStates = JSON.parse(localStorage.getItem('buttonStates') || '{}');
        buttonStates[bookingNumber] = {status};
        localStorage.setItem('buttonStates', JSON.stringify(buttonStates));
    }

    function updateStatus(bookingNumber, status, callback) {
        $.ajax({
            url: '/update_status', // Make sure this matches your Flask route
            type: 'POST',
            data: {
                booking_number: bookingNumber,
                status: status,
                csrf_token: $('input[name="csrf_token"]').val() // Assuming you have a CSRF token
            },
            success: function(response) {
                if (callback) callback(); // Call callback function if provided
                // Toggle button visibility based on the updated status
                toggleButtons(bookingNumber, status);
                fetchAndDisplayStats();
                if(response.message && response.category) {
                    displayFlashMessages(response.message, response.category);
                }
            },
            error: function(xhr, status, error) {
                console.error("Error updating status: " + error);
                displayFlashMessages("Failed to update status. Please try again.", "danger");
            }
        });
    }

    function toggleButtons(bookingNumber, currentStatus) {
        var addBtn = $(".add-btn[data-booking-number='" + bookingNumber + "']");
        var removeBtn = $(".remove-btn[data-booking-number='" + bookingNumber + "']");
        if (currentStatus === "Checked") {
            addBtn.hide();
            removeBtn.show();
        } else {
            addBtn.show();
            removeBtn.hide();
        }
    }
    // Function to display flash messages
    function displayFlashMessages(message, category) {
        const messageHtml = `<div class="alert alert-${category}" role="alert">${message}</div>`;
        $(".flash-messages").html(messageHtml).fadeIn();
        setTimeout(() => { $(".flash-messages").fadeOut(); }, 2000); // Auto-hide after 5 seconds
    }

    // Function to fetch and display statistics
    function fetchAndDisplayStats() {
        fetch('/dashboard_stats')
            .then(response => response.json())
            .then(data => {
                // these IDs in your HTML
                document.getElementById('total_guests').textContent = `${data.total_guests}`;
                document.getElementById('total_checked').textContent = `${data.total_checked}`;
                document.getElementById('total_unchecked').textContent = `${data.total_unchecked}`;
            })
            .catch(error => console.error('Error fetching stats:', error));
    }
    function updateLocalStateAndUI() {
        $.ajax({
            url: '/api/guests/status',
            type: 'GET',
            success: function(response) {
                // Update local storage and UI for each guest
                Object.entries(response).forEach(([bookingNumber, status]) => {
                    localStorage.setItem(bookingNumber, status); // Update local storage
                    toggleButtons(bookingNumber, status); // Update UI
                });
            },
            error: function(xhr, status, error) {
                console.error("Error fetching guest status: " + error);
            }
        });
    }


    // Handler for both "Mark as Checked" and "Unmark" buttons
    $(".add-btn, .remove-btn").click(function () {
        var bookingNumber = $(this).data("booking-number");
        var status = $(this).hasClass("add-btn") ? "Checked" : "Unchecked";
        //updateStatus(bookingNumber, status, $(this));
        //saveButtonState(bookingNumber, status, $(this));
        //toggleButtons(bookingNumber, status, $(this));

        updateStatus(bookingNumber, status, function() {
            localStorage.setItem(bookingNumber, status); // Update local storage
            updateStatus(bookingNumber, status, $(this));
            saveButtonState(bookingNumber, status, $(this));
            toggleButtons(bookingNumber, status, $(this));
        });
    });

    $('.dropdown-toggle').click(function(e) {
        e.preventDefault(); // Prevent the default anchor behavior
        $(this).next('.dropdown-menu').toggle(); // Manually toggle the dropdown menu
    });

    // Handler for Delete User Modal
    $('#deleteUserModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget); // Button that triggered the modal
        var username = button.data('username'); // Extract info from data-* attributes
        // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
        // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
        var modal = $(this);
        modal.find('.modal-footer #modalUsername').val(username);
    });

    // Make the whole card clickable for marking as checked or unchecked
    document.querySelectorAll('.card-clickable').forEach(card => {
        card.addEventListener('click', (e) => {
            // Prevent interaction with buttons inside the card from triggering this event
            if (!e.target.classList.contains('btn')) {
                var bookingNumber = card.getAttribute('data-booking-number');
                // Simulate click on "Mark as Checked" or "Unmark" button based on visibility
                var addButton = card.querySelector('.add-btn');
                var removeButton = card.querySelector('.remove-btn');
                if (getComputedStyle(addButton).display !== 'none') {
                    addButton.click();
                } else if (getComputedStyle(removeButton).display !== 'none') {
                    removeButton.click();
                }
            }
        });
    });

    
});

$(document).ready(function () {
    // Connect to Socket.IO server
    var socket = io();
    let deferredPrompt; // Step 1: Declare deferredPrompt variable

    window.addEventListener('beforeinstallprompt', (e) => { // Listen for the event
        e.preventDefault(); // Prevent the mini-infobar from appearing on mobile
        deferredPrompt = e; // Save the event so it can be triggered later
        // Update UI notify the user they can add to home screen
        $('#installButton').show(); // Assuming you have an 'installButton' in your HTML
    });

    $('#installButton').click(function() { // Step 3 & 4: Prompt the user to install
        if (deferredPrompt) {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the A2HS prompt');
                } else {
                    console.log('User dismissed the A2HS prompt');
                }
                deferredPrompt = null; // Reset the deferred prompt variable
                $('#installButton').hide(); // Optionally hide the install button
            });
        }
    });
    
    socket.on('status_changed', function(data) {
        console.log('Status change received:', data);
        const bookingNumber = data.booking_number;
        const newStatus = data.new_status;
    
        // Find the buttons for this booking number
        const addBtn = $(`.add-btn[data-booking-number="${bookingNumber}"]`);
        const removeBtn = $(`.remove-btn[data-booking-number="${bookingNumber}"]`);
    
        // Toggle button visibility based on the new status
        if (newStatus === "Checked") {
            addBtn.hide();
            removeBtn.show();
        } else {
            addBtn.show();
            removeBtn.hide();
        }

    });

    // Setup CSRF token for AJAX requests
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", $('meta[name="csrf-token"]').attr('content'));
            }
        }
    });
    $('#fullscreenBtn').click(function() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch((err) => {
                console.error(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
            });
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen().catch((err) => {
                    console.error(`Error attempting to disable full-screen mode: ${err.message} (${err.name})`);
                });
            }
        }
    });
    
    $("#search_form").submit(function(event) {
        event.preventDefault(); // Prevent the form from submitting through the browser
        var searchQuery = $("#search_input").val(); // Get the search input
    
        $.ajax({
            url: '/search-results', // Your search endpoint
            type: 'GET', // or 'POST'
            data: {
                query: searchQuery
            },
            success: function(data) {
                // Update your page with the search results
                // This could involve updating a <div> to display the results
                $("#search_results").html(data);
            },
            error: function(error) {
                // Handle any errors
                console.error("Search failed: ", error);
            }
        });
    });
    // Load users when main_panel.html is loaded
    $.get('/users', function(data) {
        // Populate the userContainer div with the user information
        $('#userContainer').html(data);
        console.log(data);
    });

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
                socket.emit('update_status', { bookingNumber: bookingNumber, status: status });
                toggleButtons(bookingNumber, status);                                                                                               
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




    function openEditModal(guestId) {
        $('#editGuestForm').data('guestId', guestId);
        // Fetch guest details from the server
        $.get(`/get_guest_details/${guestId}`, function(data) {
            const editableFields = ['comments', 'arrival_time', 'arriving_date', 'booking', 'departure_from', 'flight', 'transportation'];
            const form = $('#editGuestForm');
            const modalTitle = $('#editGuestModalLabel');
    
            // Clear existing form fields and set the modal title
            form.empty(); 
            modalTitle.text(`${data.first_name} ${data.last_name}`);
    
            // Today's date in YYYY-MM-DD format
            const today = new Date().toISOString().split('T')[0];
    
            Object.entries(data).forEach(([key, value]) => {
                if (editableFields.includes(key)) {
                    let inputType = 'text';
                    let inputValue = value;
    
                    // Check if the key is 'arriving_date' and set input type to 'date'
                    if (key === 'arriving_date') {
                        inputType = 'date';
                        inputValue = value || today; // Use provided value or today's date if not set
                    } 
                    // Check if the key is 'arrival_time' and set input type to 'time'
                    else if (key === 'arrival_time') {
                        inputType = 'time';
                        // Assume value is in a suitable format ('HH:MM'), adjust if necessary
                        // If value is not provided or invalid, don't set a default
                        inputValue = value || ''; 
                    }
    
                    // Append form group with label and input
                    form.append(`<div class="form-group">
                        <label for="${key}">${key.charAt(0).toUpperCase() + key.slice(1)}</label>
                        <input type="${inputType}" class="form-control" name="${key}" id="${key}" value="${inputValue}">
                    </div>`);
                }
            });
    
            // Append a hidden input to store the guest ID
            form.append(`<input type="hidden" name="guestId" value="${guestId}">`);
            $('#editGuestModal').modal('show');
        });
    }
    
    function submitGuestEdit() {
        // Retrieve the guest ID stored earlier
        var guestId = $('#editGuestForm').data('guestId');
        var formData = $('#editGuestForm').serialize();
        formData += '&id=' + encodeURIComponent(guestId); // Append the guestId to formData
    
        $.post('/update_guest_details', formData)
            .done(function(response) {
                console.log('Response:', response); // Debug line
                $('#editGuestModal').modal('hide');
                console.log('Guest details updated successfully!');
                // refresh the page or update the UI as needed
                location.reload();
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                console.error("Error with request: ", textStatus, errorThrown);
                console.log('Failed to update guest details. Please try again.');
            });
    }
        // Function to delete a message
        function deleteMessage(messageId) {
            $.post(`/delete_message/${messageId}`, function(response) {
                alert(response.message);
                location.reload();
            }).fail(function() {
                alert('Failed to delete message');
            });
        }
    
        // Delegated event handler for delete buttons
        $('.list-group').on('click', '.del-btn', function() {
            var messageId = $(this).attr('data-message-id');
            deleteMessage(messageId);
        });
    
        // Function to send a reply to a message
    function sendReply(messageId) {
        var replyContent = $('#replyContent_' + messageId).val();
        if (replyContent.trim() === '') {
            alert('Please enter a reply message.');
            return;
        }
        $.post(`/reply_message/${messageId}`, { reply_content: replyContent }, function(response) {
            alert(response.message);
            location.reload();
        }).fail(function() {
            alert('Failed to send reply');
        });
    }

    $('.list-group').on('click', '.btn-primary[data-message-id]', function() {
        var messageId = $(this).data('message-id');
        var replyContent = $('#replyContent_' + messageId).val();
        if (replyContent.trim() === '') {
            alert('Please enter a reply message.');
            return;
        }
        $.post(`/reply_message/${messageId}`, { reply_content: replyContent }, function(response) {
            alert(response.message);
            location.reload();
        }).fail(function() {
            alert('Failed to send reply');
        });
    });
    

    

    
    $(document).on('click', '#editButton', function() {
        var guestId = $(this).data('id');
        console.log("Edit button clicked with guestId:", guestId); // Debug line
        openEditModal(guestId);
    });
    
    $(document).ready(function () {
        $('#saveChangesButton').click(function() {
            submitGuestEdit();
        });
    });
   
    // Handler for both "Mark as Checked" and "Unmark" buttons
    $(".add-btn, .remove-btn").click(function () {
        var bookingNumber = $(this).data("booking-number");
        var status = $(this).hasClass("add-btn") ? "Checked" : "Unchecked";
        updateStatus(bookingNumber, status, $(this));
        saveButtonState(bookingNumber, status, $(this));
        toggleButtons(bookingNumber, status, $(this));
        updateLeaveReportChartData();
        location.reload();

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

});

$(document).ready(function () {
    // Make the whole card clickable for marking as checked or unchecked
    document.querySelectorAll('.card-clickable').forEach(card => {
        card.addEventListener('click', function(e) {
            // Prevent interaction with buttons inside the card from triggering this event
            if (!e.target.classList.contains('btn') && !e.target.closest('.btn')) {
                var bookingNumber = this.getAttribute('data-booking-number');
                // Simulate click on "Mark as Checked" or "Unmark" button based on visibility
                var addButton = this.querySelector('.add-btn');
                var removeButton = this.querySelector('.remove-btn');
                if (getComputedStyle(addButton).display !== 'none') {
                    addButton.click();
                } else if (getComputedStyle(removeButton).display !== 'none') {
                    removeButton.click();
                }
            }
        });
    });
});


// Service Worker registration code
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/sw.js').then(registration => {
        console.log('ServiceWorker registration successful with scope: ', registration.scope);
      }, err => {
        console.log('ServiceWorker registration failed: ', err);
      });
    });
  }

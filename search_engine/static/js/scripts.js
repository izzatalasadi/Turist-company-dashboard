// Global variables
let pdfDoc = null, currentPage = 1, totalPages = 0, scale = 1.1;
let isRendering = false, renderTask = null, renderDebounceTimeout;
let lastExecuted = Date.now();
const throttlePeriod = 300; // Time in milliseconds between allowed executions

$(document).ready(function () {
    // Check if the activities list container exists before trying to update it
    if ($('.bullet-line-list').length > 0) {
        updateActivitiesList();
    }

    // Additional setup calls
    var socket = setupSocketIO(); // Setup socket and store reference for further use
    let deferredPrompt; // For install prompt handling

    // Setup AJAX CSRF token for secure requests
    setupCSRFToken();

    // Listeners for install prompt
    setupInstallPrompt(deferredPrompt);

    // Handle form submissions
    setupFormHandlers();

    // Initialize PDF Viewer
    if ($('#pdfModal').length > 0) {
        setupPDFViewer();
        setupZoomSlider();
        updateToolbarResponsive();
        window.addEventListener('resize', updateToolbarResponsive);
    }

    // Register service worker
    setupServiceWorker();

    // Handle interactive UI elements
    setupInteractiveElements();

    // Load user details initially
    loadUserDetails();

    // Event handlers for buttons and other UI interactions
    registerEventHandlers();
});

// Socket.IO setup
function setupSocketIO() {
    const socket = io();
    socket.on('status_changed', function(data) {
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
    return socket;
}

// Prevent default install prompt and show a custom install button
function setupInstallPrompt(deferredPrompt) {
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        $('#installButton').show();
    });

    $('#installButton').click(function() {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                console.log(choiceResult.outcome === 'accepted' ? 'User accepted the A2HS prompt' : 'User dismissed the A2HS prompt');
                deferredPrompt = null;
                $('#installButton').hide();
            });
        }
    });
}

// Setup CSRF token for safe AJAX calls
function setupCSRFToken() {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", $('meta[name="csrf-token"]').attr('content'));
            }
        }
    });
}

// Setup form handlers, primarily for search functionality
function setupFormHandlers() {
    $("#search_form").submit(function(event) {
        event.preventDefault();
        var searchQuery = $("#search_input").val();
        fetchSearchResults(searchQuery);
    });
}

// Function to fetch search results via AJAX
function fetchSearchResults(query) {
    $.ajax({
        url: '/search-results',
        type: 'GET',
        data: { query: query },
        success: function(data) {
            $("#search_results").html(data);
        },
        error: function(error) {
            console.error("Search failed: ", error);
        }
    });
}

// Load user details on startup
function loadUserDetails() {
    $.get('/users', function(data) {
        $('#userContainer').html(data);
    });
}

// Function to save the state of a button to local storage
function saveButtonState(bookingNumber, status) {
    const buttonStates = JSON.parse(localStorage.getItem('buttonStates') || '{}');
    buttonStates[bookingNumber] = {status};
    localStorage.setItem('buttonStates', JSON.stringify(buttonStates));
}

function requestPageRender(pageNum) {
    clearTimeout(renderDebounceTimeout);
    renderDebounceTimeout = setTimeout(() => {
        renderPDFPage(pageNum);
    }, throttlePeriod); 
}

// Enhanced Zoom Features with Throttling
function setupZoomSlider() {
    $('#zoom-slider').on('input', function () {
        const now = Date.now();
        if (now - lastExecuted >= throttlePeriod) {
            scale = parseFloat(this.value);
            renderPDFPage(currentPage);
            lastExecuted = now; // Reset the last executed time
        }
    });
}

// Night Mode Toggle
function toggleNightMode() {
    const pdfViewer = document.getElementById('pdfModal');
    const modalContent = document.querySelector('.modal-content');
    pdfViewer.classList.toggle('night-mode');

    // Toggle the modal background as well
    if (pdfViewer.classList.contains('night-mode')) {
        modalContent.style.backgroundColor = '#333';  // Dark background for night mode
        modalContent.style.color = '#fff';  // Light text for night mode
    } else {
        modalContent.style.backgroundColor = '';  // Reset to default
        modalContent.style.color = '';  // Reset to default
    }
}

// Enhanced PDF Thumbnails
function generateThumbnails(pdfDoc) {
    for (let page = 1; page <= pdfDoc.numPages; page++) {
        pdfDoc.getPage(page).then(function(page) {
            var viewport = page.getViewport({scale: 0.5});
            var canvas = document.createElement('canvas');
            var ctx = canvas.getContext('2d');
            canvas.width = viewport.width;
            canvas.height = viewport.height;

            var renderContext = {
                canvasContext: ctx,
                viewport: viewport
            };
            
            page.render(renderContext).promise.then(function() {
                document.getElementById('thumbnail-container').appendChild(canvas);
            });
        });
    }
}

// Update Toolbar for Responsive Design
function updateToolbarResponsive() {
    const toolbar = document.getElementById('pdf-toolbar');
    if (toolbar) { // Check if the toolbar element exists
        const mq = window.matchMedia('(max-width: 768px)');
        if (mq.matches) {
            toolbar.style.flexDirection = 'column';
        } else {
            toolbar.style.flexDirection = 'row';
        }
    } else {
        console.log('Toolbar element not found');
    }
}

// Initialize PDF Viewer
function setupPDFViewer() {
    document.querySelectorAll('.pdf-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            loadSelectedPDF(this.getAttribute('data-url'));
        });
    });
}

// Load and render PDF documents
function loadSelectedPDF(url) {
    pdfjsLib.getDocument(url).promise.then(function(_pdfDoc) {
        pdfDoc = _pdfDoc;
        totalPages = pdfDoc.numPages;
        renderPDFPage(currentPage); // Render the first page initially
    }).catch(function(error) {
        console.error("Error loading PDF:", error);
    });
}

// Render a specific page of a PDF document
function renderPDFPage(pageNum) {
    if (!pdfDoc) return;

    if (isRendering && renderTask) {
        renderTask.cancel(); // Ensure the current rendering task is cancelled
        console.log(`Rendering for page ${currentPage} cancelled as new request for page ${pageNum} received.`);
    }

    clearCanvas();
    isRendering = true;

    pdfDoc.getPage(pageNum).then(function(page) {
        var canvas = document.getElementById('pdf-render');
        var ctx = canvas.getContext('2d');
        var viewport = page.getViewport({scale: scale});
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        var renderContext = {
            canvasContext: ctx,
            viewport: viewport
        };

        renderTask = page.render(renderContext);
        renderTask.promise.then(function() {
            document.getElementById('page-num').textContent = pageNum;
            document.getElementById('page-count').textContent = totalPages;
            isRendering = false;
            console.log(`Rendered page ${pageNum}.`);
        }).catch(function(renderError) {
            if (renderError.name === 'RenderingCancelledException') {
                console.log(`Rendering for page ${pageNum} was cancelled.`);
            } else {
                console.error("Rendering error:", renderError);
            }
            isRendering = false;
        });
    });
}

function zoomIn() {
    scale *= 1.1;
    renderPDFPage(currentPage);
}

function zoomOut() {
    if (scale > 1) {
        scale /= 1.1;
        renderPDFPage(currentPage);
    }
}

function clearCanvas() {
    var canvas = document.getElementById('pdf-render');
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function toggleFullScreen() {
    var elem = document.getElementById('pdfModal');
    if (!document.fullscreenElement) {
      elem.requestFullscreen().catch(err => {
        displayFlashMessage('Error attempting to enable full-screen mode', 'danger');
      });
    } else {
      document.exitFullscreen();
    }
}

// Setup service worker for offline capabilities
function setupServiceWorker() {
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/static/sw.js').then(registration => {
                console.log('ServiceWorker registration successful with scope: ', registration.scope);
            }, err => {
                console.error('ServiceWorker registration failed: ', err);
            });
        });
    }
}

// Handle dropdowns and other interactive elements
function setupInteractiveElements() {
    $('.dropdown-toggle').click(function(e) {
        e.preventDefault();
        $(this).next('.dropdown-menu').toggle();
    });
}

// Register event handlers for UI elements
function registerEventHandlers() {
    
    $('.flash-messages').empty();
    $('.flash-messages .alert').each(function() {
        const element = $(this);
        element.delay(2000).fadeOut(200, function() {
            element.remove();
        });
    });

    $(".add-btn, .remove-btn").click(function () {
        var bookingNumber = $(this).data("booking-number");
        var status = $(this).hasClass("add-btn") ? "Checked" : "Unchecked";
        updateStatus(bookingNumber, status, function() {
            saveButtonState(bookingNumber, status);
            toggleButtons(bookingNumber, status);
        });
    });

    $('.wrapper').on('submit', 'form', function(event) {
        event.preventDefault();  // Prevent the default form submission behavior
        const form = $(this);
        const url = form.attr('action');  // Assuming the action is correctly set to a URL
        const data = form.serialize();  // Serialize the form data for submission

        $.ajax({
            url: url,
            type: 'POST',
            data: data,
            success: function(response) {
                displayFlashMessage('Message sent successfully!', 'success');  // Or handle more gracefully
                form.find('input[type="text"]').val('');  // Clear the message input field
            },
            error: function(xhr, status, error) {
                displayFlashMessage('Failed to send message', 'danger');
            }
        });
    });

    $('.send-btn').click(function() {
        var messageId = $(this).data('message-id');
        var replyContent = $('#replyContent_' + messageId).val().trim();
        if (!replyContent) {
            displayFlashMessage('Reply content cannot be empty.','warning');
            return;
        }
        $.ajax({
            url: '/reply_message/' + messageId,
            type: 'POST',
            data: { reply_content: replyContent },
            success: function(response) {
                $('#replyModal_' + messageId).modal('hide');
                displayFlashMessage('Message been replied successfully.','success');  // Use the response message for user feedback
            },
            error: function(response) {
                displayFlashMessage('Failed to send reply. ','warning');
            }
        });
    });
    
    $(document).on('click', '#editButton', function() {
        var guestId = $(this).data('id');
        openEditModal(guestId);
    });
    
    $('#saveChangesButton').click(function() {
        submitGuestEdit();
    });
    
    $('.input-group').on('submit', 'form', function(event) {
        event.preventDefault();  // Prevent the default form submission behavior
        const form = $(this);
        const url = form.attr('action');  // Assuming the action is correctly set to a URL
        const data = form.serialize();  // Serialize the form data for submission
    
        $.ajax({
            url: url,
            type: 'POST',
            data: data,
            success: function(response) {
                displayFlashMessage('Message sent successfully!','success');  // Or handle more gracefully
                form.find('input[type="text"]').val('');  // Clear the message input field
            },
            error: function(xhr, status, error) {
                displayFlashMessage('Failed to send message: ', 'warning');
            }
        });
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
    
    $('#replyModal').on('shown.bs.modal', function (event) {
        var modal = $(this);
        var messageId = modal.data('message-id'); // Ensure the data attribute passes the message ID correctly
        modal.find('#replyContent_' + messageId).focus(); // Focuses the textarea when the modal is fully shown
    });
    
    // Event handler for deleting messages
    $('.list-group').on('click', '.delete-btn', function() {
        var messageId = $(this).data('message-id');
        deleteMessage(messageId);
    });

    // Navigation buttons
    $('#prev-page').on('click', function () {
        if (currentPage > 1) {
            requestPageRender(--currentPage);
        }
    });

    $('#next-page').on('click', function () {
        if (currentPage < totalPages) {
            requestPageRender(++currentPage);
        }
    });

    // Example functions for Zoom In and Zoom Out
    $('#zoom-in').on('click', function () {
        zoomIn();
    });

    $('#zoom-out').on('click', function () {
        zoomOut();
    });
     
    // Night Mode Toggle
    $('#night-mode-toggle').on('click', function () {
        toggleNightMode();
    });

    // Zoom Slider
    $('#zoom-slider').on('input', function () {
        scale = parseFloat(this.value);
        renderPDFPage(currentPage);
    });

    // Fullscreen toggle moved into named function for clarity
    $('#fullscreen-toggle').click(toggleFullScreen);

    // Ensure that when the PDF viewer modal is closed, full-screen is exited if active
    $('#pdfModal').on('hidden.bs.modal', function () {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        }
    });
}

// Function to display flash messages dynamically
function displayFlashMessage(message, type) {
    console.log('Displaying flash message:', message, 'with type:', type);

    // Clear existing flash messages
    $('.flash-messages').empty();

    const flashMessageHtml = `
    <div class="alert alert-${type} alert-dismissible fade show flash-message" role="alert">
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>`;
    
    const flashMessageElement = $(flashMessageHtml).hide().fadeIn(200);

    $('.flash-messages').append(flashMessageElement);
    flashMessageElement.delay(2000).fadeOut(200, function() {
        $(this).remove();
    });
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
            $('#editGuestModal').modal('hide');
            // refresh the page or update the UI as needed
            location.reload();
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            console.error("Error with request: ", textStatus, errorThrown);
        });
}

// Update status and handle UI feedback
function updateStatus(bookingNumber, status, callback) {
    console.log(`Updating status. Booking number: ${bookingNumber}, Status: ${status}`);
    
    $.ajax({
        url: '/update_status',
        type: 'POST',
        data: {
            booking_number: bookingNumber,
            status: status,
            csrf_token: $('input[name="csrf_token"]').val(), 
        },
        success: function(response) {
            console.log("Response from server:", response);
            if (response.status === 'success') {
                if (callback) callback();
                displayFlashMessage(response.message, 'success');
            } else {
                displayFlashMessage(response.message, 'warning');
            }
        },
        error: function(xhr, errorStatus, error) {
            console.error("Error updating status: ", error);
            displayFlashMessage("Failed to update status. Please try again.", "danger");
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

// Function to send a reply
function sendReply(messageId, content) {
    $.ajax({
        url: '/reply_message/' + messageId, // Update with your API endpoint
        type: 'POST',
        data: {
            reply_content: content,
            csrf_token: $('meta[name="csrf-token"]').attr('content')
        },
        success: function(response) {
            displayFlashMessage('Reply sent successfully.', 'success');
            $('#replyContent_' + messageId).val(''); // Clear the textarea after sending
        },
        error: function(error) {
            displayFlashMessage('Failed to send reply.', 'warning');
        }
    });
}

// Function to delete a message
function deleteMessage(messageId) {
    $.ajax({
        url: '/delete_message/' + messageId,
        type: 'POST',
        success: function(response) {
            $('article[data-message-id="' + messageId + '"]').remove();
            displayFlashMessage('Message deleted successfully.', 'success');  // User feedback
        },
        error: function(response) {
            displayFlashMessage('Failed to delete message.', 'danger');
        }
    });
}

function updateActivitiesList() {
    $.ajax({
        url: '/api/activities',  // Adjust if the route differs
        type: 'GET',
        success: function(data) {
            if (!Array.isArray(data)) {
                console.error('Expected an array but got:', data);
                return;
            }
            let activitiesHtml = '';
            data.forEach(function(activity) {
                activitiesHtml += `
                    <li>
                        <div class="d-flex justify-content-between">
                            <div>
                                <span class="text-light-green">${activity.username}</span></br>
                                ${activity.event}: ${activity.description}
                            </div>
                            <p>${activity.timestamp}</p>
                        </div>
                    </li>`;
            });
            $('.bullet-line-list').html(activitiesHtml);
        },
        error: function(error) {
            console.log('Error updating activities:', error);
        }
    });
}

setInterval(updateActivitiesList, 30000);

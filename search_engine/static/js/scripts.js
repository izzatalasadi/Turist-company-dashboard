// Global variables
let pdfDoc = null, currentPage = 1, totalPages = 0, scale = 1.1;
let isRendering = false, renderTask = null, renderDebounceTimeout;
let lastExecuted = Date.now();
const throttlePeriod = 300; // Time in milliseconds between allowed executions
// Global variables to store chart instances
let guestsChart; 
let transportChart;
let predictionChartInstance;


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

    // Event handlers for buttons and other UI interactions
    registerEventHandlers();
    
    initializeFloatingChat();

    // Bootstrap Offcanvas and Collapse Initialization
    initializeBootstrapComponents();
    
    navtoggler()
    
});

function navtoggler() {
    document.querySelector('.navbar-toggler-custom').addEventListener('click', function () {
        const navbar = document.querySelector('.navbar-bottom-custom');
        const togglerIcon = this.querySelector('i');
        let isDragging = false;
        let startX, startY, initialX, initialY;

        navbar.classList.toggle('collapsed');
        this.classList.toggle('collapsed');
        if (navbar.classList.contains('collapsed')) {
            this.setAttribute('aria-expanded', 'true');
            togglerIcon.classList.add('mdi-chevron-down');
            togglerIcon.classList.remove('mdi-chevron-up');

        } else {
            this.setAttribute('aria-expanded', 'false');
            togglerIcon.classList.remove('mdi-chevron-up');
            togglerIcon.classList.add('mdi-chevron-down');
        }
      });
  };

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

function initializeFloatingChat() {
    // Load user details on startup
    loadUserDetails();
  
    function loadUserDetails() {
      $.get('/users', function(data) {
        $('#userContainer').html(data);
      });
    }
  
    // Movable Chat Window
    const chatHeader = document.querySelector('.chat-header');
    const chatWindow = document.querySelector('.floating-chat');
    const chatIcon = document.querySelector('.floating-chat-icon');
    const userChatIconsContainer = document.getElementById('userChatIconsContainer');
    let isDragging = false;
    let offsetX, offsetY;
  
    chatHeader.addEventListener('mousedown', (e) => {
      isDragging = true;
      offsetX = e.clientX - chatWindow.getBoundingClientRect().left;
      offsetY = e.clientY - chatWindow.getBoundingClientRect().top;
    });
  
    document.addEventListener('mousemove', (e) => {
      if (isDragging) {
        chatWindow.style.left = `${e.clientX - offsetX}px`;
        chatWindow.style.top = `${e.clientY - offsetY}px`;
      }
    });
  
    document.addEventListener('mouseup', () => {
      isDragging = false;
    });
  
    // Show Chat Window
    chatIcon.addEventListener('click', () => {
      chatWindow.style.display = 'block';
    });
  
    // Close Chat Window
    document.querySelector('.close-chat').addEventListener('click', () => {
      chatWindow.style.display = 'none';
    });
  
    // Open user chat icon
    document.addEventListener('click', function(e) {
      if (e.target.closest('.user-card')) {
        const userCard = e.target.closest('.user-card');
        const username = userCard.getAttribute('data-username');
        const userId = userCard.getAttribute('data-userid');
        const userPic = userCard.getAttribute('data-userpic');
  
        const userChatIcon = document.createElement('div');
        userChatIcon.classList.add('floating-user-chat-icon');
        userChatIcon.innerHTML = `<img class="img-sm rounded-circle" src="${userPic}" alt="${username}'s profile picture">`;
  
        userChatIconsContainer.appendChild(userChatIcon);
  
        // Handle click on user chat icon to open chat
        userChatIcon.addEventListener('click', () => {
          // Open the chat window for the user
          openUserChat(userId, username, userPic);
        });
      }
    });
  
    function openUserChat(userId, username, userPic) {
      // Create a chat window for the user
      const chatWindow = document.createElement('div');
      chatWindow.classList.add('floating-chat');
      chatWindow.innerHTML = `
        <div class="chat-header">
          <span>${username}</span>
          <button class="close-chat">&times;</button>
        </div>
        <div class="chat-body">
          <div id="messages-${userId}" class="messages"></div>
          <form action="/send_message/${userId}" method="POST" class="message-form">
            <input type="hidden" name="csrf_token" value="${document.querySelector('meta[name="csrf-token"]').getAttribute('content')}">
            <input type="text" class="form-control message-input" name="message_content" placeholder="Write your message..." required>
            <button type="submit" class="btn btn-light">
              <i class="mdi mdi-send mdi-24px"></i>
            </button>
          </form>
        </div>
      `;
      document.body.appendChild(chatWindow);
  
      // Handle form submission
      $(chatWindow).find('.message-form').on('submit', function(event) {
        event.preventDefault();
        const form = $(this);
        const url = form.attr('action');
        const data = form.serialize();
  
        $.ajax({
          url: url,
          type: 'POST',
          data: data,
          success: function(response) {
            displayFlashMessage('Message sent successfully!', 'success');
            form.find('input[type="text"]').val('');
          },
          error: function(xhr, status, error) {
            displayFlashMessage('Failed to send message', 'danger');
          }
        });
      });
  
      // Make the chat window movable
      const chatHeader = chatWindow.querySelector('.chat-header');
      chatHeader.addEventListener('mousedown', (e) => {
        isDragging = true;
        offsetX = e.clientX - chatWindow.getBoundingClientRect().left;
        offsetY = e.clientY - chatWindow.getBoundingClientRect().top;
      });
  
      document.addEventListener('mousemove', (e) => {
        if (isDragging) {
          chatWindow.style.left = `${e.clientX - offsetX}px`;
          chatWindow.style.top = `${e.clientY - offsetY}px`;
        }
      });
  
      document.addEventListener('mouseup', () => {
        isDragging = false;
      });
  
      // Close Chat Window
      chatWindow.querySelector('.close-chat').addEventListener('click', () => {
        chatWindow.remove();
      });
  
      // Load previous messages
      loadMessages(userId);
    }
  
    function loadMessages(userId) {
      $.get(`/api/messages?receiver_id=${userId}`, function(messages) {
        const messagesContainer = document.getElementById(`messages-${userId}`);
        if (Array.isArray(messages)) {
          messages.forEach(message => {
            const messageElement = document.createElement('div');
            messageElement.classList.add('message');
            messageElement.innerHTML = `
              <strong>${message.sender}</strong>: ${message.body} <small>${message.timestamp}</small>
            `;
            messagesContainer.appendChild(messageElement);
          });
        } else {
          console.error('Messages data is not an array:', messages);
        }
      });
    }
  
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

// PDF Thumbnails
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
        }).catch(function(renderError) {
            if (renderError.name === 'RenderingCancelledException') {
                console.error(`Rendering for page ${pageNum} was cancelled.`);
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
    let scrollToTopBtn = $('#scrollToTopBtn');

    // When the user scrolls down 20px from the top of the document, show the button
    $(window).scroll(function() {
        if ($(this).scrollTop() > 20) {
            scrollToTopBtn.removeClass('hide').addClass('show');
        } else {
            scrollToTopBtn.removeClass('show').addClass('hide');
        }
    });

    
    $('.flash-messages').empty();
    $('.flash-messages .alert').each(function() {
        const element = $(this);
        element.delay(5000).fadeOut(500, function() {
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
    
    // When the user clicks on the button, scroll to the top of the document
    $(document).on('click', '#scrollToTopBtn', function() {
        $('html, body').animate({ scrollTop: 0 }, 'slow');
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

    
    // Tooltip Initialization
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipList)
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
    
    const flashMessageElement = $(flashMessageHtml).hide().fadeIn(5000);

    $('.flash-messages').append(flashMessageElement);
    flashMessageElement.delay(5000).fadeOut(500, function() {
        $(this).remove();
    });
}

function openEditModal(guestId) {
    $('#editGuestForm').data('guestId', guestId);
    // Fetch guest details from the server
    $.get(`/get_guest_details/${guestId}`, function(data) {
        const editableFields = ['comments', 'arrival_time', 'arriving_date', 'booking', 'departure_from'];
        const form = $('#editGuestForm');
        const modalTitle = $('#editGuestModalLabel');

        // Clear existing form fields and set the modal title
        form.empty(); 
        modalTitle.text(`${data.first_name} ${data.last_name}`);

        // Today's date in YYYY-MM-DD format
        const today = new Date().toISOString().split('T')[0];

        // Flight selection input with datalist
        form.append(`
            <div class="form-group">
                <label for="flight_number">Flight</label>
                <input list="flights" class="form-control" name="flight_number" id="flight_number" value="${data.flight_number}" placeholder="Start typing flight number...">
                <datalist id="flights">
                    <!-- Options will be populated dynamically -->
                </datalist>
            </div>
        `);

        Object.entries(data).forEach(([key, value]) => {
            if (editableFields.includes(key)) {
                let inputType = 'text';
                let inputValue = value;

                // Check if the key is 'arriving_date' and set input type to 'date'
                if (key === 'arriving_date') {
                    inputType = 'date';
                    inputValue = value ? formatDate(value) : today; // Format to YYYY-MM-DD or use today's date
                } 
                // Check if the key is 'arrival_time' and set input type to 'time'
                else if (key === 'arrival_time') {
                    inputType = 'time';
                    inputValue = value ? formatTime(value) : ''; // Format to HH:MM or use an empty string
                }
                

                // Append form group with label and input
                form.append(`<div class="form-group">
                    <label for="${key}">${key.charAt(0).toUpperCase() + key.slice(1)}</label>
                    <input type="${inputType}" class="form-control" name="${key}" id="${key}" value="${inputValue}">
                </div>`);
            }
        });

        // Handle transportation separately if it's an array
        if (Array.isArray(data.transportations)) {
            data.transportations.forEach((transport, index) => {
                form.append(`<div class="form-group">
                    <label for="transportation_${index}_type">Transportation Type</label>
                    <input type="text" class="form-control" name="transportation_${index}_type" id="transportation_${index}_type" value="${transport.transport_type}">
                </div>`);
                form.append(`<div class="form-group">
                    <label for="transportation_${index}_details">Transportation Details</label>
                    <input type="text" class="form-control" name="transportation_${index}_details" id="transportation_${index}_details" value="${transport.transport_details}">
                </div>`);
            });
        }
        

        // Fetch and populate flight options
        $.get(`/get_flights`, function(flights) {
            let flightOptions = '';
            flights.forEach(flight => {
                flightOptions += `<option value="${flight.flight_number}">`;
            });
            $('#flights').html(flightOptions);
        });

        // Append a hidden input to store the guest ID
        form.append(`<input type="hidden" name="guestId" value="${guestId}">`);
        $('#editGuestModal').modal('show');
    });
}

function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        if (!isNaN(date)) {
            return date.toISOString().split('T')[0]; // Format to YYYY-MM-DD
        } else {
            return ''; // Return empty string if date is invalid
        }
    } catch (e) {
        console.error('Invalid date:', dateString);
        return ''; // Return empty string if date is invalid
    }
}

function formatTime(timeString) {
    try {
        // Ensure the time string is in a valid format (HH:MM)
        const timeParts = timeString.split(':');
        if (timeParts.length === 2) {
            const hours = parseInt(timeParts[0], 10);
            const minutes = parseInt(timeParts[1], 10);
            if (!isNaN(hours) && !isNaN(minutes) && hours >= 0 && hours < 24 && minutes >= 0 && minutes < 60) {
                return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
            }
        }
        return ''; // Return empty string if time is invalid
    } catch (e) {
        console.error('Invalid time:', timeString);
        return ''; // Return empty string if time is invalid
    }
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
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

    $.ajax({
        url: '/update_status',
        type: 'POST',
        data: {
            booking_number: bookingNumber,
            status: status,
            csrf_token: csrfToken
        },
        success: function(response) {
            callback(null, response);
        },
        error: function(xhr, status, error) {
            callback(new Error('Failed to update status: ' + xhr.responseText));
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

            // Check if data is an array
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
                                <span class="text-light-green">${activity.username}</span><br>
                                ${activity.event}: ${activity.description}
                            </div>
                            <p>${activity.timestamp}</p>
                        </div>
                    </li>`;
            });
            $('.bullet-line-list').html(activitiesHtml);
        },
        error: function(error) {
            console.error('Error updating activities:', error);
        }
    });
}


// Function to initialize Bootstrap Offcanvas and Collapse components
function initializeBootstrapComponents() {
    // Ensure Offcanvas elements are initialized
    const offcanvasElementList = [].slice.call(document.querySelectorAll('.offcanvas'));
    const offcanvasList = offcanvasElementList.map(function (offcanvasEl) {
        return new bootstrap.Offcanvas(offcanvasEl);
    });

    // Ensure Collapse elements are initialized
    const collapseElementList = [].slice.call(document.querySelectorAll('.collapse'));
    const collapseList = collapseElementList.map(function (collapseEl) {
        return new bootstrap.Collapse(collapseEl, {
            toggle: false
        });
    });

    // Add event listeners to collapse triggers
    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(button => {
        button.addEventListener('click', function () {
            let target = document.querySelector(button.getAttribute('data-bs-target'));
            if (target) {
                let collapseInstance = bootstrap.Collapse.getOrCreateInstance(target);
                collapseInstance.toggle();
            }
        });
    });
}
// Initialize the charts
const guestsChartCtx = document.getElementById('guestsChart').getContext('2d');
const transportChartCtx = document.getElementById('transportChart').getContext('2d');

guestsChart = new Chart(guestsChartCtx, {
  type: 'doughnut',
  data: {
    labels: ['Total Guests', 'Checked In', 'Not Arrived'],
    datasets: [{
        label: 'Guests',
        data: [0, 0, 0],
        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56'],
        hoverBackgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false
  }
});

transportChart = new Chart(transportChartCtx, {
  type: 'doughnut',
  data: {
    labels: ['Buses Needed', '5-Seater Cars Needed', '8-Seater Cars Needed'],
    datasets: [{
      label: 'Transport',
      data: [0, 0, 0],
      backgroundColor: ['#ffc107', '#17a2b8', '#6f42c1'],
      hoverBackgroundColor: ['#ffc107', '#17a2b8', '#6f42c1']
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false
  }
});

// Function to fetch statistics from the server
function fetchStatistics(date = null) {
  let url = '/dashboard_stats';
  if (date) {
    url += `?date=${date}`;
  }
  
  $.ajax({
    url: url,
    method: 'GET',
    success: function(data) {
      const totalGuests = data.total_guests;
      const checkedInGuests = data.total_checked;
      const notArrivedGuests = data.total_unchecked;
      
      const busesNeeded = calculateBusesNeeded(totalGuests);
      const smallCarsNeeded = calculateCarsNeeded(totalGuests, 5);
      const largeCarsNeeded = calculateCarsNeeded(totalGuests, 8);

      const remainingGuests = totalGuests - busesNeeded * 32;
      
      // Update the Guests Chart
      guestsChart.data.datasets[0].data = [totalGuests, checkedInGuests, notArrivedGuests];
      guestsChart.update();

      // Update the Transport Chart
      transportChart.data.datasets[0].data = [busesNeeded, smallCarsNeeded, largeCarsNeeded];
      transportChart.update();

      // Predictions for the next years (dummy example)
      const nextYearsData = predictNextYears(totalGuests);
      updatePredictionChart(nextYearsData);
    }
  });
}

// Function to calculate buses needed
function calculateBusesNeeded(guestCount) {
  const busCapacity = 34; // Assume each bus can hold 32 guests
  return Math.ceil(guestCount / busCapacity);
}

// Function to calculate cars needed
function calculateCarsNeeded(guestCount, carCapacity) {
  return Math.ceil(guestCount / carCapacity);
}

// Function to predict next years' data
function predictNextYears(currentGuestCount) {
  // Dummy prediction logic
  const years = [2024, 2025, 2026, 2027, 2028];
  const growthRate = 0.05; // 5% growth rate
  return years.map((year, index) => ({
    year: year,
    guests: Math.ceil(currentGuestCount * Math.pow(1 + growthRate, index + 1))
  }));
}

function updatePredictionChart(data) {
    const labels = data.map(d => d.year);
    const guestCounts = data.map(d => d.guests);
  
    const ctx = document.getElementById('predictionChart').getContext('2d');
  
    // Destroy the existing chart instance if it exists
    if (predictionChartInstance) {
      predictionChartInstance.destroy();
    }
  
    // Create a new chart instance and store it in the global variable
    predictionChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Predicted Guests',
          data: guestCounts,
          backgroundColor: 'rgba(0, 123, 255, 0.5)',
          borderColor: '#007bff',
          fill: true,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });
  }

// Event listener for date change
document.getElementById('selectDate').addEventListener('change', function() {
  const selectedDate = this.value;
  fetchStatistics(selectedDate);
});


// Initial fetch of statistics

fetchStatistics();
setInterval(updateActivitiesList, 3000);

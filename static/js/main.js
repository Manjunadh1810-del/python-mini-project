document.addEventListener('DOMContentLoaded', function () {

    // ---- Reusable confirmation modal for destructive actions ----
    // Usage: <a href="#" data-confirm
    //           data-confirm-title="Delete Job"
    //           data-confirm-message="This cannot be undone."
    //           data-confirm-href="{% url 'jobs:job_delete' job.pk %}"
    //           data-confirm-label="Delete">Delete</a>
    var confirmModalEl = document.getElementById('confirmActionModal');
    if (confirmModalEl && window.bootstrap) {
        var confirmModal = new bootstrap.Modal(confirmModalEl);
        var titleEl = document.getElementById('confirmActionModalTitle');
        var bodyEl = document.getElementById('confirmActionModalBody');
        var confirmBtn = document.getElementById('confirmActionModalConfirmBtn');

        document.querySelectorAll('[data-confirm]').forEach(function (trigger) {
            trigger.addEventListener('click', function (e) {
                e.preventDefault();
                titleEl.textContent = trigger.getAttribute('data-confirm-title') || 'Confirm';
                bodyEl.textContent = trigger.getAttribute('data-confirm-message') || 'Are you sure?';
                confirmBtn.textContent = trigger.getAttribute('data-confirm-label') || 'Confirm';
                confirmBtn.setAttribute('href', trigger.getAttribute('data-confirm-href') || trigger.getAttribute('href'));
                confirmModal.show();
            });
        });
    }

    // ---- Highlight invalid form fields ----
    // Our forms render field errors as <div class="text-danger small">...</div>
    // immediately after the offending input/select/textarea - add Bootstrap's
    // is-invalid styling to that field so the red border matches the message.
    document.querySelectorAll('.text-danger.small').forEach(function (errorEl) {
        var prev = errorEl.previousElementSibling;
        if (prev && ['INPUT', 'SELECT', 'TEXTAREA'].includes(prev.tagName)) {
            prev.classList.add('is-invalid');
        }
    });

    // ---- Submit button loading state ----
    // Disables the submit button and shows a spinner to prevent double-submits
    // and give feedback on slower operations (e.g. resume upload + analysis).
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function () {
            var submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.dataset.originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Please wait...';
            }
        });
    });
});

document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  let activitiesData = {};
  let recentUpdate = { activity: null, email: null };

  function buildParticipantItems(details, highlightEmail) {
    if (!details.participants.length) {
      return `<li class="participant-empty">No participants yet</li>`;
    }

    return details.participants
      .map((email) => {
        const isNew = email === highlightEmail;
        return `
          <li class="participant-row${isNew ? " participant-updated" : ""}">
            <span class="participant-name${isNew ? " participant-new" : ""}">${email}</span>
            <button type="button" class="participant-remove" data-activity="${details.name}" data-email="${email}" aria-label="Remove ${email}">&times;</button>
          </li>`;
      })
      .join("");
  }

  function createActivityCard(name, details, highlightEmail) {
    const activityCard = document.createElement("div");
    activityCard.className = `activity-card${name === recentUpdate.activity ? " updated-card" : ""}`;
    activityCard.dataset.activityName = name;

    const spotsLeft = details.max_participants - details.participants.length;
    const participantItems = buildParticipantItems(details, highlightEmail);

    activityCard.innerHTML = `
      <h4>${name}</h4>
      <p>${details.description}</p>
      <p><strong>Schedule:</strong> ${details.schedule}</p>
      <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
      <p><strong>Participants (${details.participants.length}):</strong></p>
      <ul class="participant-list">${participantItems}</ul>
    `;

    return activityCard;
  }

  function renderActivities() {
    activitiesList.innerHTML = "";
    activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

    const entries = Object.entries(activitiesData);
    const sortedEntries = [...entries];

    if (recentUpdate.activity) {
      const updatedIndex = sortedEntries.findIndex(([name]) => name === recentUpdate.activity);
      if (updatedIndex !== -1) {
        const [updatedEntry] = sortedEntries.splice(updatedIndex, 1);
        sortedEntries.unshift(updatedEntry);
      }
    }

    sortedEntries.forEach(([name, details]) => {
      details.name = name;
      const highlightEmail = name === recentUpdate.activity ? recentUpdate.email : null;
      const activityCard = createActivityCard(name, details, highlightEmail);
      activitiesList.appendChild(activityCard);

      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      activitySelect.appendChild(option);
    });
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();
      activitiesData = activities;

      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
      renderActivities();
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const emailInput = document.getElementById("email");
    const email = emailInput.value.trim();
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        if (activitiesData[activity]) {
          activitiesData[activity].participants.unshift(email);
          recentUpdate = { activity, email };
          renderActivities();
        } else {
          recentUpdate = { activity: null, email: null };
          fetchActivities();
        }
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Handle participant removal using event delegation
  activitiesList.addEventListener("click", async (event) => {
    const button = event.target.closest(".participant-remove");
    if (!button) return;

    const activity = button.dataset.activity;
    const email = button.dataset.email;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/participants?email=${encodeURIComponent(email)}`,
        { method: "DELETE" }
      );

      const result = await response.json();
      messageDiv.textContent = response.ok ? result.message : result.detail || "Unable to remove participant";
      messageDiv.className = response.ok ? "success" : "error";
      messageDiv.classList.remove("hidden");

      if (response.ok) {
        if (activitiesData[activity]) {
          activitiesData[activity].participants = activitiesData[activity].participants.filter((item) => item !== email);
          recentUpdate = { activity: null, email: null };
          renderActivities();
        } else {
          fetchActivities();
        }
      }
    } catch (error) {
      messageDiv.textContent = "Failed to remove participant. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error removing participant:", error);
    }
  });

  // Initialize app
  fetchActivities();
});

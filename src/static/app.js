document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  let messageTimeout;

  function showMessage(message, type) {
    clearTimeout(messageTimeout);
    messageDiv.textContent = message;
    messageDiv.className = type;
    messageTimeout = setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  async function unregisterParticipant(activity, email, button) {
    button.disabled = true;
    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
        { method: "DELETE" }
      );
      const result = await response.json();

      if (!response.ok) {
        showMessage(result.detail || "Não foi possível cancelar a inscrição.", "error");
        return;
      }

      showMessage(result.message, "success");
      await fetchActivities();
    } catch (error) {
      showMessage("Falha ao cancelar a inscrição. Tente novamente.", "error");
      console.error("Error unregistering participant:", error);
    } finally {
      button.disabled = false;
    }
  }

  // Build participants section with DOM APIs so emails are rendered as text, not HTML
  function buildParticipantsSection(activity, details) {
    const section = document.createElement("div");
    section.className = "participants-section";

    const header = document.createElement("div");
    header.className = "participants-header";

    const title = document.createElement("h5");
    title.textContent = "Participantes";

    const count = document.createElement("span");
    count.className = "participants-count";
    count.textContent = `${details.participants.length}/${details.max_participants}`;

    header.append(title, count);
    section.appendChild(header);

    if (details.participants.length === 0) {
      const empty = document.createElement("p");
      empty.className = "participants-empty";
      empty.textContent = "Nenhum participante ainda — seja o primeiro a se inscrever!";
      section.appendChild(empty);
    } else {
      const list = document.createElement("ul");
      list.className = "participants-list";
      details.participants.forEach((email) => {
        const item = document.createElement("li");

        const avatar = document.createElement("span");
        avatar.className = "participant-avatar";
        avatar.textContent = email.charAt(0).toUpperCase();

        const label = document.createElement("span");
        label.className = "participant-email";
        label.textContent = email;

        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "participant-delete";
        deleteButton.title = `Cancelar inscrição de ${email} em ${activity}`;
        deleteButton.setAttribute("aria-label", deleteButton.title);
        deleteButton.innerHTML = `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round"
               stroke-linejoin="round" aria-hidden="true" focusable="false">
            <path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7" />
          </svg>
        `;
        deleteButton.addEventListener("click", () => {
          unregisterParticipant(activity, email, deleteButton);
        });

        item.append(avatar, label, deleteButton);
        list.appendChild(item);
      });
      section.appendChild(list);
    }

    return section;
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities", { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`Failed to load activities: ${response.status}`);
      }
      const activities = await response.json();
      const selectedActivity = activitySelect.value;

      // Clear loading message and previous dropdown options
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Selecione uma atividade --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
        `;

        activityCard.appendChild(buildParticipantsSection(name, details));
        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
      activitySelect.value = selectedActivity;
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
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
        showMessage(result.message, "success");
        signupForm.reset();
        await fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});

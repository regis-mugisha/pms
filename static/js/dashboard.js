document.addEventListener("DOMContentLoaded", () => {
  const logsTableBody = document.getElementById("logs-table-body");
  const alertsTableBody = document.getElementById("alerts-table-body");
  const navLinks = document.querySelectorAll(".nav-link");
  const sections = document.querySelectorAll(".content-section");

  // Function to handle navigation
  function handleNavigation(e) {
    e.preventDefault();
    const targetSection = e.target.getAttribute("data-section");

    // Update active nav link
    navLinks.forEach((link) => {
      link.classList.remove("active");
      if (link.getAttribute("data-section") === targetSection) {
        link.classList.add("active");
      }
    });

    // Show target section, hide others
    sections.forEach((section) => {
      section.classList.remove("active");
      if (section.id === targetSection) {
        section.classList.add("active");
      }
    });
  }

  // Add click event listeners to nav links
  navLinks.forEach((link) => {
    link.addEventListener("click", handleNavigation);
  });

  // Function to fetch and display vehicle logs
  async function fetchAndDisplayLogs() {
    try {
      const response = await fetch("/api/logs");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const logs = await response.json();

      logsTableBody.innerHTML = ""; // Clear previous logs
      if (logs.length === 0) {
        logsTableBody.innerHTML =
          '<tr><td colspan="5" class="px-6 py-4 text-center text-gray-500">No vehicle activity logs available.</td></tr>';
        return;
      }

      logs.forEach((log) => {
        const row = document.createElement("tr");
        row.className = "table-row"; // Add hover effect

        row.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${
                      log.id
                    }</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${
                      log.plate
                    }</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span class="status-badge ${
                        log.payment_status === "Yes"
                          ? "status-paid"
                          : "status-unpaid"
                      }">${log.payment_status}</span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${
                      log.entry_time || "N/A"
                    }</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${
                      log.exit_time || "N/A"
                    }</td>
                `;
        logsTableBody.appendChild(row);
      });
    } catch (error) {
      console.error("Error fetching logs:", error);
      logsTableBody.innerHTML =
        '<tr><td colspan="5" class="px-6 py-4 text-center text-red-500">Failed to load logs.</td></tr>';
    }
  }

  // Function to fetch and display unauthorized exit alerts
  async function fetchAndDisplayAlerts() {
    try {
      const response = await fetch("/api/alerts");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const alerts = await response.json();

      alertsTableBody.innerHTML = ""; // Clear previous alerts
      if (alerts.length === 0) {
        alertsTableBody.innerHTML =
          '<tr><td colspan="4" class="px-6 py-4 text-center text-gray-500">No incident alerts available.</td></tr>';
        return;
      }

      alerts.forEach((alert) => {
        const row = document.createElement("tr");
        row.className = "alert-row"; // Apply red background for alerts

        row.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">${
                      alert.id
                    }</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">${
                      alert.plate
                    }</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">${
                      alert.timestamp || "N/A"
                    }</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">${
                      alert.incident_type || "N/A"
                    }</td>
                `;
        alertsTableBody.appendChild(row);
      });
    } catch (error) {
      console.error("Error fetching alerts:", error);
      alertsTableBody.innerHTML =
        '<tr><td colspan="4" class="px-6 py-4 text-center text-red-500">Failed to load alerts.</td></tr>';
    }
  }

  // Initial fetch and display
  fetchAndDisplayLogs();
  fetchAndDisplayAlerts();

  // Refresh data every 5 seconds
  setInterval(fetchAndDisplayLogs, 5000);
  setInterval(fetchAndDisplayAlerts, 5000);
});

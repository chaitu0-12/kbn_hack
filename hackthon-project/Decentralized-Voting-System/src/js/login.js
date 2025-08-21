const loginForm = document.getElementById("loginForm");
const errorMessage = document.getElementById("error-message");

function showError(message) {
  if (errorMessage) {
    errorMessage.textContent = message || "Something went wrong";
    errorMessage.style.display = "block";
  } else {
    alert(message || "Something went wrong");
  }
}

if (loginForm) {
  loginForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    if (errorMessage) {
      errorMessage.style.display = "none";
      errorMessage.textContent = "";
    }

    const voter_id = document.getElementById("voter_id").value;
    const password = document.getElementById("password").value;

    try {
      const response = await fetch("http://127.0.0.1:8000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `voter_id=${encodeURIComponent(
          voter_id
        )}&password=${encodeURIComponent(password)}`,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Server error: ${response.status}`);
      }

      if (data.success) {
        // Save JWT locally
        localStorage.setItem("token", data.token);

        // Redirect based on role
        if (data.role === "admin") {
          localStorage.setItem("jwtTokenAdmin", data.token);
          window.location.href = "admin.html";
        } else {
          localStorage.setItem("jwtTokenVoter", data.token);
          window.location.href = "index.html";
        }
      } else {
        showError(data.message || "Login failed");
      }
    } catch (error) {
      console.error("Login error:", error);
      showError(error.message || "Login failed. Please try again.");
    }
  });
}

// Helper function for making authenticated requests
async function authFetch(url, options = {}) {
  const token = localStorage.getItem("token");
  if (!token) throw new Error("No authorization token found");

  options.headers = {
    ...options.headers,
    Authorization: `Bearer ${token}`,
  };

  const res = await fetch(url, options);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(
      errData.detail || `Request failed with status ${res.status}`
    );
  }
  return res.json();
}

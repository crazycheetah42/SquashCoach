// navbar.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.11.0/firebase-app.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/12.11.0/firebase-auth.js";

const firebaseConfig = {
    apiKey: "AIzaSyASWLSUE6DWMaQN7SpWBtCelDdVc30pTNM",
    authDomain: "squashcoach-f1cea.firebaseapp.com",
    projectId: "squashcoach-f1cea"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

const navLinks = document.getElementById("navLinks");

onAuthStateChanged(auth, user => {
    if (user) {
        navLinks.innerHTML = `
            <li class="nav-item">
                <a class="nav-link" href="/">Home</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/matches">Log a Match</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/stats">Stats</a>
            </li>
            <li class="nav-item d-flex align-items-center">
                <span class="nav-link text-primary fw-bold">${user.displayName}</span>
            </li>
            <li class="nav-item d-flex align-items-center">
                <button class="btn btn-outline-danger btn-sm ms-2" id="logoutBtn">Logout</button>
            </li>
        `;

        document.getElementById("logoutBtn").addEventListener("click", async () => {
            await signOut(auth);
            window.location.href = "/login";
        });

    } else {
        navLinks.innerHTML = `
            <li class="nav-item">
                <a class="nav-link" href="/">Home</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/login">Login / Register</a>
            </li>
        `;
    }
});
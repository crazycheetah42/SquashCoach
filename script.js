// script.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.11.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/12.11.0/firebase-auth.js";
import { getFirestore, doc, setDoc, getDoc, updateDoc, arrayUnion } from "https://www.gstatic.com/firebasejs/12.11.0/firebase-firestore.js";

// ------------------- Firebase Setup -------------------
const firebaseConfig = {
  apiKey: "AIzaSyASWLSUE6DWMaQN7SpWBtCelDdVc30pTNM",
  authDomain: "squashcoach-f1cea.firebaseapp.com",
  projectId: "squashcoach-f1cea",
  storageBucket: "squashcoach-f1cea.firebasestorage.app",
  messagingSenderId: "917985213639",
  appId: "1:917985213639:web:574d81e63f35007a3b12e2"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const provider = new GoogleAuthProvider();

// ------------------- DOM Elements -------------------
const signInBtn = document.getElementById('signInBtn');
const userName = document.getElementById('userName');
const profileSection = document.getElementById('profile');
const matchTracker = document.getElementById('matchTracker');
const drillsSection = document.getElementById('drills');
const skillLevelSelect = document.getElementById('skillLevel');
const matchForm = document.getElementById('matchForm');
const matchList = document.getElementById('matchList');
const drillList = document.getElementById('drillList');
const statsDisplay = document.getElementById('stats');

// ------------------- Drills Catalog -------------------
const drillsCatalog = [
  {name: "Straight Drive", level: "beginner", video: "https://youtu.be/example1"},
  {name: "Boast", level: "beginner", video: "https://youtu.be/example2"},
  {name: "Basic Volley", level: "beginner", video: "https://youtu.be/example3"},
  {name: "Cross-Court Accuracy", level: "intermediate", video: "https://youtu.be/example4"},
  {name: "Backhand Strength", level: "intermediate", video: "https://youtu.be/example5"},
  {name: "Power Boast", level: "advanced", video: "https://youtu.be/example6"},
  {name: "Front Court Control", level: "advanced", video: "https://youtu.be/example7"},
  {name: "Conditioning + Tactical", level: "advanced", video: "https://youtu.be/example8"}
];

let currentUserDoc;

// ------------------- Auth -------------------
signInBtn.addEventListener('click', async () => {
  const result = await signInWithPopup(auth, provider);
  const user = result.user;
  await initUser(user);
});

onAuthStateChanged(auth, async (user) => {
  if(user) {
    await initUser(user);
  } else {
    profileSection.classList.add('hidden');
    matchTracker.classList.add('hidden');
    drillsSection.classList.add('hidden');
    signInBtn.classList.remove('hidden');
  }
});

// ------------------- Initialize User -------------------
async function initUser(user) {
  userName.textContent = `Hello, ${user.displayName}`;
  signInBtn.classList.add('hidden');
  profileSection.classList.remove('hidden');
  matchTracker.classList.remove('hidden');
  drillsSection.classList.remove('hidden');

  const docRef = doc(db, 'users', user.uid);
  const docSnap = await getDoc(docRef);
  if(!docSnap.exists()) {
    await setDoc(docRef, {skillLevel: 'beginner', matches: []});
  }
  currentUserDoc = docRef;

  const data = (await getDoc(docRef)).data();
  skillLevelSelect.value = data.skillLevel;
  loadMatches(data.matches || []);
  loadDrills(data.matches || []);
}

// ------------------- Skill Level -------------------
skillLevelSelect.addEventListener('change', async () => {
  const level = skillLevelSelect.value;
  await updateDoc(currentUserDoc, {skillLevel: level});
  const data = (await getDoc(currentUserDoc)).data();
  loadDrills(data.matches || []);
});

// ------------------- Match Submission -------------------
matchForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const opponent = document.getElementById('opponent').value;
  const yourScore = parseInt(document.getElementById('yourScore').value);
  const opponentScore = parseInt(document.getElementById('opponentScore').value);
  const weakAreasInput = document.getElementById('weakAreas').value;
  const weakAreas = weakAreasInput.split(',').map(s => s.trim()).filter(s=>s);

  const match = {opponent, yourScore, opponentScore, weakAreas, date: new Date().toISOString()};
  await updateDoc(currentUserDoc, {matches: arrayUnion(match)});

  addMatchToUI(match);
  loadDrills(await getCurrentMatches());
  matchForm.reset();
});

async function getCurrentMatches() {
  const data = (await getDoc(currentUserDoc)).data();
  return data.matches || [];
}

// ------------------- Drill Logic -------------------
function getTailoredDrills(matches, skillLevel) {
  const weaknesses = {};
  matches.forEach(match => {
    match.weakAreas?.forEach(area => {
      weaknesses[area.toLowerCase()] = (weaknesses[area.toLowerCase()] || 0) + 1;
    });
  });

  const sortedWeaknesses = Object.entries(weaknesses).sort((a,b)=>b[1]-a[1]).map(e=>e[0]);

  const tailoredDrills = [];
  sortedWeaknesses.forEach(area => {
    const drill = drillsCatalog.find(d => d.name.toLowerCase() === area);
    if(drill) tailoredDrills.push(drill);
  });

  drillsCatalog.forEach(drill => {
    if(drill.level === skillLevel && !tailoredDrills.includes(drill)) {
      tailoredDrills.push(drill);
    }
  });

  return tailoredDrills;
}

function loadDrills(matches) {
  const skillLevel = skillLevelSelect.value;
  const drills = getTailoredDrills(matches, skillLevel);

  drillList.innerHTML = '';
  drills.forEach(drill => {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${drill.name}</strong> - <a href="${drill.video}" target="_blank">Watch Tutorial</a>`;
    drillList.appendChild(li);
  });
}

// ------------------- Matches UI -------------------
function loadMatches(matches) {
  matchList.innerHTML = '';
  let wins = 0, losses = 0;
  matches.forEach(match => {
    addMatchToUI(match);
    if(match.yourScore > match.opponentScore) wins++; else losses++;
  });
  statsDisplay.textContent = `Wins: ${wins} | Losses: ${losses}`;
}

function addMatchToUI(match) {
  const li = document.createElement('li');
  li.textContent = `${match.opponent}: ${match.yourScore}-${match.opponentScore} | Weak: ${match.weakAreas.join(', ')}`;
  matchList.appendChild(li);
}
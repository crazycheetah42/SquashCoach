// Sample drills for different skill levels
const drills = {
  beginner: [
    "Straight Drive Drill",
    "Boast and Drive Drill",
    "Basic Volley Practice"
  ],
  intermediate: [
    "Length and Drop Drill",
    "Cross-court Accuracy Drill",
    "Backhand Strength Drill"
  ],
  advanced: [
    "Power Boast Drill",
    "Front Court Control Drill",
    "Conditioning + Tactical Drill"
  ]
};

// DOM elements
const matchForm = document.getElementById("matchForm");
const matchList = document.getElementById("matchList");
const skillLevelSelect = document.getElementById("skillLevel");
const drillList = document.getElementById("drillList");

// Load drills based on selected skill level
function loadDrills() {
  const level = skillLevelSelect.value;
  drillList.innerHTML = "";
  drills[level].forEach(drill => {
    const li = document.createElement("li");
    li.textContent = drill;
    drillList.appendChild(li);
  });
}

// Handle match submission
matchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const opponent = document.getElementById("opponent").value;
  const yourScore = document.getElementById("yourScore").value;
  const opponentScore = document.getElementById("opponentScore").value;

  const li = document.createElement("li");
  li.textContent = `${opponent}: ${yourScore} - ${opponentScore}`;
  matchList.appendChild(li);

  matchForm.reset();
});

// Update drills when skill level changes
skillLevelSelect.addEventListener("change", loadDrills);

// Initial drill load
loadDrills();
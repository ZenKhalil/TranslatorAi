function updateProgressBar(progress) {
  const progressBar = document.getElementById("progress-bar");
  progressBar.style.width = progress + "%";
}

function onSubmit() {
  document.getElementById("feedback").innerText = "Processing... Please wait.";
  updateProgressBar(50); // Example value, update as needed
  return true;
}

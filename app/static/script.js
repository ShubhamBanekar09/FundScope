function selectRisk(btn){
  document.querySelectorAll('.risk').forEach(b=>{
    b.classList.remove('border-primary','bg-primary','text-white','bg-blue-500','text-white');
    b.classList.add('border');
  });
  btn.classList.add('border-primary','bg-primary','text-white');
}

function selectCategory(btn){
  document.querySelectorAll('.category').forEach(b=>{
    b.classList.remove('bg-primary','text-white','bg-blue-500','text-white');
    b.classList.add('bg-surface-container-high');
  });
  btn.classList.remove('bg-surface-container-high');
  btn.classList.add('bg-primary','text-white');
}

async function getRecommendations(){

  const riskEl = document.querySelector('.risk.border-primary');
  const catEl = document.querySelector('.category.bg-primary');

  // 🛑 SAFETY CHECK
  if(!riskEl || !catEl){
    alert("Please select risk and category");
    return;
  }

  // ✅ CLEAN TEXT EXTRACTION using data attribute if present
  const riskText = riskEl.dataset.risk || (riskEl.querySelector('span:last-child') ? riskEl.querySelector('span:last-child').innerText.trim() : riskEl.innerText.trim());
  const catText = catEl.dataset.category || (catEl.querySelector('span:last-child') ? catEl.querySelector('span:last-child').innerText.trim() : catEl.innerText.trim());

// 📦 DATA
const data = {
user_name: document.getElementById("username").value,
age: document.getElementById("age").value,
amount: document.getElementById("amount").value,
time_frame: document.getElementById("timeframe").value,
risk: riskText,
category: catText
};

console.log("Sending:", data);

// ⏳ LOADING STATE
document.getElementById("results").innerHTML = "<p>Loading recommendations...</p>";

try {
const res = await fetch("/recommend", {
method: "POST",
headers: {"Content-Type": "application/json"},
body: JSON.stringify(data)
});

const result = await res.json();
console.log("Received:", result);

displayResults(result);

} catch (error){
console.error("Error:", error);
document.getElementById("results").innerHTML = "<p>Error fetching data</p>";
}
}

function displayResults(data){
const div = document.getElementById("results");
div.innerHTML = "";

// ❌ ERROR CASE
if(!data || data.error){
div.innerHTML = "<p>No funds found</p>";
return;
}

// ✅ SUCCESS
data.recommendations.forEach(f=>{
div.innerHTML += `
<div class="bg-white p-5 rounded-xl shadow hover:shadow-lg transition">
<h3 class="font-bold text-lg">${f.fund_name}</h3>
<p class="text-gray-500">${f.category}</p>
<div class="mt-2 text-sm space-y-1">
<p>📈 Returns: <b>${f.returns_3yr}%</b></p>
<p>⚖️ Sharpe: ${f.sharpe}</p>
<p>⭐ Score: ${f.score}%</p>
</div>
</div>
`;
});
}
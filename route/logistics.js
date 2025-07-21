document.getElementById("routeForm").addEventListener("submit", function (e) {
  e.preventDefault();
  const src = document.getElementById("src").value.trim();
  const dest = document.getElementById("dest").value.trim();
  const payout = parseFloat(document.getElementById("payout").value);

  const output = document.getElementById("output");

  if (!(src in zipCoords && dest in zipCoords)) {
    output.textContent = "❌ ZIP code(s) not found.";
    return;
  }

  const fob = "44107";               // Forward Operating Base
  const mpg = 20;                   // Urban driving
  const fuelRate = 2.79;            // Estimated average gas price
  const avgSpeed = 25;              // Average speed in mph
  const hourlyRate = 7;             // Your target hourly earnings
  const hourlyGallons = 1;          // Estimated burn rate per hour

  function haversine(lat1, lon1, lat2, lon2) {
    const R = 3958.8; // radius of Earth in miles
    const toRad = (x) => (x * Math.PI) / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  function cost(zipA, zipB) {
    const miles = haversine(
      zipCoords[zipA].lat,
      zipCoords[zipA].lon,
      zipCoords[zipB].lat,
      zipCoords[zipB].lon
    );
    const hours = Math.ceil(miles / avgSpeed);
    const fuelCost = hours * fuelRate * hourlyGallons;
    const laborCost = hours * hourlyRate;
    const totalCost = fuelCost + laborCost;
  
    return {
      miles: miles.toFixed(2),
      cost: totalCost.toFixed(2),
      hours: hours,
    };
  }

  const leg1 = cost(fob, src);
  const leg2 = cost(src, dest);
  const leg3 = cost(dest, fob);

  const totalCost = (
    parseFloat(leg1.cost) + parseFloat(leg2.cost) + parseFloat(leg3.cost)
  ).toFixed(2);
  const goHomeCost = (
    parseFloat(leg1.cost) + parseFloat(cost(src, fob).cost)
  ).toFixed(2);
  const netGain = (payout - totalCost).toFixed(2);
  const verdict = parseFloat(netGain) >= 0
    ? "✅ TAKE IT"
    : "❌ SKIP IT";

  output.textContent = `
🧭 Route Evaluation:
  From ${src} to ${dest}, ending at FOB (${fob})
  Payout Offered: $${payout.toFixed(2)}
  Cost to Complete: $${totalCost}
  Cost to Go Home Instead: $${goHomeCost}
  Net Gain if Taken: $${netGain}

${verdict}
  `.trim();
});
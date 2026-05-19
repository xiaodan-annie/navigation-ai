let map;
let routeLayer;
let markerLayer;

// ----------------------------
// INIT MAP
// ----------------------------
function initMap() {
    map = L.map('map').setView([37.5, -122.0], 9);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Layer for markers (prevents stacking)
    markerLayer = L.layerGroup().addTo(map);
}

initMap();


// ----------------------------
// MAIN FUNCTION
// ----------------------------
async function analyze() {

    const origin = document.getElementById("origin").value.trim();
    const destination = document.getElementById("destination").value.trim();

    const errorBox = document.getElementById("error");

    // ----------------------------
    // VALIDATION
    // ----------------------------
    if (!origin || !destination) {
        errorBox.innerText = "Please enter both origin and destination.";
        return;
    }

    if (/^\d+$/.test(origin) || /^\d+$/.test(destination)) {
        errorBox.innerText = "Please enter valid place names, not numbers.";
        return;
    }

    if (origin.length < 2 || destination.length < 2) {
        errorBox.innerText = "Location name is too short.";
        return;
    }

    errorBox.innerText = "";

    // ----------------------------
    // API CALL
    // ----------------------------
    let data;

    try {
        const res = await fetch("https://navigation-ai-bxxs.onrender.com/route", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ origin, destination })
        });

        if (!res.ok) {
            throw new Error("Backend error");
        }

        data = await res.json();

    } catch (err) {
        errorBox.innerText = "Failed to fetch route. Try again.";
        return;
    }


    // ----------------------------
    // TEXT OUTPUT
    // ----------------------------
    document.getElementById("output").innerHTML = `
        <h3>Route Analysis</h3>
        <p><b>Origin:</b> ${data.origin}</p>
        <p><b>Destination:</b> ${data.destination}</p>
        <p><b>Distance:</b> ${data.distance}</p>
        <p><b>ETA:</b> ${data.eta}</p>
        <p><b>Traffic:</b> ${data.traffic}</p>
        <p><b>Recommendation:</b> ${data.recommendation}</p>

        <h3>AI Summary</h3>
        <div>${data.ai_summary}</div>
    `;

    document.getElementById("tripInfo").innerHTML = `
        <p><b>Distance:</b> ${data.distance}</p>
        <p><b>ETA:</b> ${data.eta}</p>
        <p><b>Traffic:</b> ${data.traffic}</p>
    `;

    // ----------------------------
    // DIRECTIONS PANEL
    // ----------------------------
    const panel = document.getElementById("directions");

    panel.innerHTML = (data.directions || []).map((step, i) => `
        <div class="direction-card">
            <div class="direction-step">STEP ${i + 1}</div>
            <div class="direction-text">${step}</div>
        </div>
    `).join("");


    // ----------------------------
    // MAP UPDATE
    // ----------------------------

    const originLatLng = [
        data.origin_coords[1],
        data.origin_coords[0]
    ];

    const destLatLng = [
        data.destination_coords[1],
        data.destination_coords[0]
    ];

    // Clear old markers
    markerLayer.clearLayers();

    // Add markers
    markerLayer.addLayer(
        L.marker(originLatLng).bindPopup("Origin")
    );

    markerLayer.addLayer(
        L.marker(destLatLng).bindPopup("Destination")
    );

    // Remove old route
    if (routeLayer) {
        map.removeLayer(routeLayer);
    }

    // ----------------------------
    // ROUTE DRAWING
    // ----------------------------
    if (data.geometry && typeof polyline !== "undefined") {

        const decodedRoute = polyline.decode(data.geometry);
        const routeLatLngs = decodedRoute.map(p => [p[0], p[1]]);

        let routeColor = "green";

        if (data.traffic === "moderate") routeColor = "orange";
        if (data.traffic === "heavy") routeColor = "red";

        routeLayer = L.polyline(routeLatLngs, {
            color: routeColor,
            weight: 5
        }).addTo(map);

        map.fitBounds(routeLayer.getBounds());
    }
}
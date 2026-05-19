let map;
let routeLayer;

function initMap() {
    map = L.map('map').setView([37.5, -122.0], 9);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
}

initMap();

async function analyze() {

    const origin = document.getElementById("origin").value;
    const destination = document.getElementById("destination").value;

    const res = await fetch("https://navigation-ai-bxxs.onrender.com/route", {
    //const res = await fetch("http://127.0.0.1:8000/route", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ origin, destination })
    });

    const data = await res.json();


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
    const panel = document.getElementById("directions");


    panel.innerHTML = data.directions.map((step, i) => `
        <div class="direction-card">

            <div class="direction-step">
                STEP ${i + 1}
            </div>

            <div class="direction-text">
                ${step}
            </div>

        </div>
    `).join("");

    document.getElementById("tripInfo").innerHTML = `
        <p><b>Distance:</b> ${data.distance}</p>
        <p><b>ETA:</b> ${data.eta}</p>
        <p><b>Traffic:</b> ${data.traffic}</p>
    `;
    

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

    // Remove old route
    if (routeLayer) {
        map.removeLayer(routeLayer);
    }

    // Markers
    L.marker(originLatLng).addTo(map).bindPopup("Origin");
    L.marker(destLatLng).addTo(map).bindPopup("Destination");

    // Safety check
    if (data.geometry) {

        const decodedRoute = polyline.decode(data.geometry);

        const routeLatLngs = decodedRoute.map(p => [p[0], p[1]]);
        
        let routeColor = "green";

        if (data.traffic === "moderate") {
            routeColor = "orange";
        }

        if (data.traffic === "heavy") {
            routeColor = "red";
        }

        routeLayer = L.polyline(routeLatLngs, {
            color: "blue",
            weight: 5
        }).addTo(map);

        map.fitBounds(routeLayer.getBounds());
    }

}
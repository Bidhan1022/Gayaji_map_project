// static/js/map.js

// 1. Gaya ke coordinates par map ko center karein
// (Aap Mahabodhi Mandir ke coordinates bhi daal sakte hain)
const gayaCoords = [24.7954, 85.0039];
const map = L.map('map').setView(gayaCoords, 14); // 14 zoom level hai

// 2. OpenStreetMap ka layer add karein
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// 3. Jaise hi page load ho, purane pins ko fetch karo
async function loadPins() {
    const response = await fetch('/api/get_pins');
    const pins = await response.json();

    pins.forEach(pin => {
        let popupContent = `<b>${pin.name}</b><br>Added by: ${pin.author}`;
        if (pin.image_url) {
            popupContent += `<br><img src="${pin.image_url}" width="100">`;
        }

        L.marker([pin.lat, pin.lng])
         .addTo(map)
         .bindPopup(popupContent);
    });
}
loadPins(); // Function ko call karo

// 4. Jab user map par click kare, tab naya pin add karne ka form dikhao
map.on('click', function(e) {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    // Ek simple form pucho
    const name = prompt("Is jagah ka naam batayein:");
    if (!name) return; // Agar user cancel karde

    // Image ke liye hum ek proper HTML form modal bana sakte hain,
    // Lekin abhi ke liye, hum sirf naam aur co-ordinates bhejte hain.
    // Image upload ke liye HTML form ki zaroorat padegi.

    // Ek behtar tareeka: Ek modal (popup box) banayein 
    // jismein 'Naam' aur 'File Upload' ka option ho.

    // Chaliye, ek simple modal ka example dete hain
    const popupContent = `
        <form id="pinForm" style="width: 200px;">
            <b>Add New Pin</b><br>
            <label>Name:</label>
            <input type="text" id="pinName" value="${name}" required><br>
            <label>Image:</label>
            <input type="file" id="pinImage" accept="image/*"><br>
            <button type="submit">Add Pin</button>
        </form>
    `;

    const popup = L.popup()
        .setLatLng([lat, lng])
        .setContent(popupContent)
        .openOn(map);

    // Form submit ko handle karo
    // Ye thoda advanced JS hai,
    // Hum popup ke andar ke form element ko select kar rahe hain
    // Iske liye `setTimeout` ka istemal karna pad sakta hai taaki form DOM mein aa jaaye

    setTimeout(() => {
        const form = document.getElementById('pinForm');
        if (form) {
            form.addEventListener('submit', async (event) => {
                event.preventDefault(); // Page ko reload hone se roko

                const pinName = document.getElementById('pinName').value;
                const pinImage = document.getElementById('pinImage').files[0];

                // FormData ka istemal karein jab image bhejni ho
                const formData = new FormData();
                formData.append('name', pinName);
                formData.append('lat', lat);
                formData.append('lng', lng);
                if (pinImage) {
                    formData.append('image', pinImage);
                }

                // Backend ko data bhejo
                const response = await fetch('/api/add_pin', {
                    method: 'POST',
                    body: formData // JSON nahi, FormData
                });

                if (response.ok) {
                    map.closePopup(popup); // Popup band karo
                    loadPins(); // Map ko refresh karo
                    alert('Pin added!');
                } else {
                    alert('Error adding pin.');
                }
            });
        }
    }, 100); // 100ms ka chhota sa delay
});
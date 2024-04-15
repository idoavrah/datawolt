console.log('WoltBot is running');
let cookies = document.cookie.split('; ');
let token = '';
let tokenCookie = cookies.find(row => row.startsWith('__wtoken='));
if (tokenCookie) {
    let json_part = tokenCookie.split('=')[1]
    let decodedString = decodeURIComponent(json_part)
    let jsonObject = JSON.parse(decodedString);
    token = jsonObject.accessToken
    console.log('JWT token found: ' + token)
}

fetch('https://datawolt-r3xg75z5ba-uc.a.run.app', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        token: token
    })

}).then(response => {
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    return response.json();

}).then(data => {
    console.log('Success:', data);
    alert('DataWolt extension:\nOrders added to the database.\nPress OK to forward to the dashboard.')
    window.open('https://datawolt.streamlit.app/?userid=' + data.userid);

}).catch(error => {
    // Handle any errors that occurred during the fetch
    console.log('There was a problem with your fetch operation:', error);
    alert('Failed to add orders to the database :/')
});

// -------------------- Load Chat --------------------

window.onload = function () {

    let history = localStorage.getItem("chatHistory");

    if (history) {

        document.getElementById("chat-box").innerHTML = history;

    }

    if (localStorage.getItem("theme") === "dark") {

        document.body.classList.add("dark-mode");

        document.getElementById("themeBtn").innerHTML = "☀ Light Mode";

    }

};

// -------------------- Send Message --------------------

function sendMessage() {

    let input = document.getElementById("message");

    let message = input.value.trim();

    if (message === "") return;

    let chatBox = document.getElementById("chat-box");

    // User Message

    chatBox.innerHTML += `
    <div class="user-message">
        👤 <b>You:</b><br>${message}
    </div>
    `;

    chatBox.scrollTop = chatBox.scrollHeight;

    input.value = "";

    document.getElementById("typing").style.display = "block";

    fetch("/get", {

        method: "POST",

        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },

        body: "msg=" + encodeURIComponent(message)

    })

    .then(response => response.json())

    .then(data => {

        document.getElementById("typing").style.display = "none";

        chatBox.innerHTML += `
        <div class="bot-message">
            🤖 <b>Bot:</b><br>${data.reply}
        </div>
        `;

        chatBox.scrollTop = chatBox.scrollHeight;

        localStorage.setItem("chatHistory", chatBox.innerHTML);

        // Voice Output

        let speech = new SpeechSynthesisUtterance(data.reply);

        speech.lang = "en-IN";

        window.speechSynthesis.speak(speech);

    })

    .catch(error => {

        document.getElementById("typing").style.display = "none";

        chatBox.innerHTML += `
        <div class="bot-message">
            ❌ Error connecting to chatbot.
        </div>
        `;

        console.log(error);

    });

}

// -------------------- Enter Key --------------------

document.getElementById("message").addEventListener("keypress", function(e){

    if(e.key === "Enter"){

        sendMessage();

    }

});

// -------------------- Voice Input --------------------

if ("webkitSpeechRecognition" in window) {

    const recognition = new webkitSpeechRecognition();

    recognition.lang = "en-IN";

    recognition.continuous = false;

    recognition.interimResults = false;

    document.getElementById("micBtn").addEventListener("click", function(){

        recognition.start();

    });

    recognition.onresult = function(event){

        document.getElementById("message").value =
        event.results[0][0].transcript;

    };

}

// -------------------- Clear Chat --------------------

function clearChat(){

    if(confirm("Clear chat window?")){

        document.getElementById("chat-box").innerHTML="";

        localStorage.removeItem("chatHistory");

    }

}

// -------------------- Dark Mode --------------------

function toggleTheme(){

    document.body.classList.toggle("dark-mode");

    if(document.body.classList.contains("dark-mode")){

        localStorage.setItem("theme","dark");

        document.getElementById("themeBtn").innerHTML="☀ Light Mode";

    }else{

        localStorage.setItem("theme","light");

        document.getElementById("themeBtn").innerHTML="🌙 Dark Mode";

    }

}
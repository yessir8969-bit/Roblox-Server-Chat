from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

# Messages storage
messages = []

# Track connected users
connected_users = {}
next_anon_id = 1

# ================= Website HTML =================
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Roblox Chat</title>
</head>
<body>
    <h1>Roblox Chat</h1>
    <div id="chat" style="height:300px; overflow-y:scroll; border:1px solid black;"></div>
    <input type="text" id="msg" placeholder="Type message"/>
    <button onclick="sendMessage()">Send</button>

    <script>
        const chatDiv = document.getElementById("chat")
        const input = document.getElementById("msg")

        async function fetchMessages() {
            const res = await fetch("/get")
            const data = await res.json()
            chatDiv.innerHTML = ""
            data.forEach(msg => {
                const el = document.createElement("p")
                el.textContent = msg.username + ": " + msg.message
                if(msg.system && msg.color === "green") el.style.color = "green"
                else if(msg.system && msg.color === "red") el.style.color = "red"
                chatDiv.appendChild(el)
            })
            chatDiv.scrollTop = chatDiv.scrollHeight
        }

        async function sendMessage() {
            const message = input.value
            if(!message) return
            await fetch("/send", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({username: "Website", message})
            })
            input.value = ""
            fetchMessages()
        }

        setInterval(fetchMessages, 2000)
        fetchMessages()
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

# ================= Send message / connect / disconnect =================
@app.route("/send", methods=["POST"])
def send():
    global next_anon_id
    data = request.get_json()
    username = data.get("username", "Unknown")
    message = data.get("message", "")

    # Handle connect / disconnect messages from Roblox
    if message.startswith("__connect__"):
        anon = data.get("anonymous", False)
        if anon:
            anon_name = f"Anonymous{next_anon_id}"
            next_anon_id += 1
            connected_users[username] = anon_name
            messages.append({
                "username": "System",
                "message": f"{anon_name} has connected to chat!",
                "time": datetime.utcnow().isoformat(),
                "system": True,
                "color": "green"
            })
        else:
            connected_users[username] = username
            messages.append({
                "username": "System",
                "message": f"{username} has connected to chat!",
                "time": datetime.utcnow().isoformat(),
                "system": True,
                "color": "green"
            })
        return jsonify({"success": True})

    elif message.startswith("__disconnect__"):
        if username in connected_users:
            name = connected_users[username]
            messages.append({
                "username": "System",
                "message": f"{name} has disconnected from chat.",
                "time": datetime.utcnow().isoformat(),
                "system": True,
                "color": "red"
            })
            connected_users.pop(username, None)
        return jsonify({"success": True})

    # Regular chat messages
    name_to_send = connected_users.get(username, username)
    messages.append({
        "username": name_to_send,
        "message": message,
        "time": datetime.utcnow().isoformat(),
        "system": False
    })
    return jsonify({"success": True})

@app.route("/get", methods=["GET"])
def get_messages():
    return jsonify(messages), 200

if __name__ == "__main__":
    app.run(debug=True)

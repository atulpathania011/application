from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Hello App</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }
    button {
      padding: 12px 28px;
      font-size: 18px;
      border: none;
      border-radius: 8px;
      background: #4f46e5;
      color: white;
      cursor: pointer;
    }
    button:hover { background: #4338ca; }
    #message { margin-top: 20px; font-size: 24px; }
  </style>
</head>
<body>
  <button onclick="sayHello()">Say Hello</button>
  <p id="message"></p>

  <script>
    async function sayHello() {
      const response = await fetch("/hello");
      const data = await response.json();
      document.getElementById("message").textContent = data.message;
    }
  </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(PAGE)

@app.route("/hello")
def hello():
    return jsonify(message="Hello from Python!")

if __name__ == "__main__":
    app.run(debug=True)
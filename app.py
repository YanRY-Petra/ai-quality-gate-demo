from flask import Flask, jsonify, request

app = Flask(__name__)

# ❌ 硬编码的 API Key
HARDCODED_API_KEY = "SECRET_API_KEY_1234567890"

@app.route("/")
def index():
    return "Hello, DevOps Lab!"
@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200
@app.route("/dangerous-divide")
def dangerous_divide():
    """
    ❌ 明显 Bug：当传入 divisor=0 时会发生除以零异常 ZeroDivisionError
    访问示例：
      /dangerous-divide?dividend=10&divisor=0
    """
    dividend = int(request.args.get("dividend", 10))
    # 默认 divisor=0，更容易触发 Bug
    divisor = int(request.args.get("divisor", 0))
    # 这里会在 divisor 为 0 时抛出 ZeroDivisionError
    result = dividend / divisor
    return jsonify({"result": result})
@app.route("/get-api-key")
def get_api_key():
    """
    ❌ 直接返回硬编码的 API Key
    """
    return jsonify({"api_key": HARDCODED_API_KEY})
if __name__ == "__main__":
    # ❌ debug=True 
    app.run(host="0.0.0.0", port=5000, debug=True)



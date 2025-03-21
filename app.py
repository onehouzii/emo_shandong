from flask import Flask, render_template, jsonify, send_file
import json
import os

app = Flask(__name__, 
            static_folder='static',
            template_folder='.')  # 修改模板目录为当前目录

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

@app.route('/hot')
def hot():
    return send_file('hot.html')  # 直接发送hot.html文件

@app.route('/api/analysis_data')
def get_analysis_data():
    try:
        with open('static/analysis_report.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 
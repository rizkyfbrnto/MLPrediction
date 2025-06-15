from flask import Flask, render_template, request, jsonify
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from module import getHeroData, calculateTeamStrength, calculateWinPercentage, generateMatchData

app = Flask(__name__)

with open('./models/model.pkl', 'rb') as model_file:
    model = pickle.load(model_file)
    
with open('./models/pca.pkl', 'rb') as model_file:
    pca = pickle.load(model_file)
    
hero_data = pd.read_csv('./data/fix.csv')
heroes = hero_data.to_dict(orient='records')

@app.route('/')
def index():
    return render_template('index.html', heroes=heroes)

@app.route('/predict', methods=['POST'])
def predict():
    # Mendapatkan nama-nama hero yang dipilih oleh pengguna untuk tim 1 dan tim 2
    team1 = [
        request.form['team1_hero_1'],
        request.form['team1_hero_2'],
        request.form['team1_hero_3'],
        request.form['team1_hero_4'],
        request.form['team1_hero_5']
    ]
    team2 = [
        request.form['team2_hero_1'],
        request.form['team2_hero_2'],
        request.form['team2_hero_3'],
        request.form['team2_hero_4'],
        request.form['team2_hero_5']
    ]
    
    # Ambil data hero untuk tim 1 dan tim 2
    team1_data = {hero: getHeroData(hero) for hero in team1}
    team2_data = {hero: getHeroData(hero) for hero in team2}
    
    # Jika ada hero yang belum dipilih
    if any(hero == "" for hero in team1) or any(hero == "" for hero in team2):
        return render_template('index.html', heroes=heroes, error="Harap pilih hero untuk semua posisi di kedua tim!")
    
    # Pastikan bahwa semua hero ditemukan, jika tidak, beri pesan kesalahan
    if any(isinstance(value, (pd.Series, pd.DataFrame)) and value.isnull().any() for value in team1_data.values()) or \
       any(isinstance(value, (pd.Series, pd.DataFrame)) and value.isnull().any() for value in team2_data.values()):
        return "Beberapa hero tidak ditemukan, harap pilih hero yang valid!", 400


    # Menghitung total kekuatan tim
    team1Strength, team1_data, unmatchedLane1 = calculateTeamStrength(team1)
    team2Strength, team2_data, unmatchedLane2 = calculateTeamStrength(team2)

    # Menghitung persentase kemenangan berdasarkan kekuatan tim
    team1WinPercentage, team2WinPercentage, team1_data, team2_data = calculateWinPercentage(team1, team2)
    
    # Ambil semua data fitur untuk analisis dan prediksi
    match_data = generateMatchData(team1, team2, team1_data, team2_data)
    
    print(team1)
    print(team2)
    
    numeric_data = {key: value for key, value in match_data.items() if key not in ['Hero Name', 'Role']}
    numeric_values = [list(numeric_data.values())]  # Pastikan menjadi array 2D

    # Melakukan scaling data
    scaler = StandardScaler()
    hero_data_scaled = scaler.fit_transform(numeric_values)  # Menggunakan fit_transform untuk training
    
    # Melakukan PCA untuk mereduksi dimensi
    pca_data = pca.transform(hero_data_scaled)  # Fit and transform pada data
    
    # Melakukan prediksi dengan model
    prediction = model.predict(pca_data)
    
    # Menyusun hasil prediksi
    result = {
        'team1': team1,
        'team2': team2,
        'team1_win_percentage': f"{team1WinPercentage:.2f}%",
        'team2_win_percentage': f"{team2WinPercentage:.2f}%",
        'prediction': prediction.tolist(),
        'team1_data': team1_data,  
        'team2_data': team2_data
    }
    
    print(prediction)

    return render_template('result.html', result=result)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
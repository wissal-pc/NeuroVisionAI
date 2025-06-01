from flask import Flask, render_template, request, redirect, session, jsonify, flash
from tensorflow.keras.models import load_model
from werkzeug.utils import secure_filename
from utils import calculate_volume, get_tumor_coordinates, get_centroid_3d_mm, dice_coefficient, overlay_mask # <-- importer les fonctions
from fpdf import FPDF
from flask import send_file
import os
import numpy as np
import nibabel as nib
import cv2
import sys
import io
import re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from utils import preprocess_slice, calculer_age
from datetime import datetime  
import mysql.connector
from flask_cors import CORS
app = Flask(__name__)
app.secret_key = 'ton_secret_key'
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # True si HTTPS (pas en local)
from datetime import timedelta
app.permanent_session_lifetime = timedelta(minutes=30)
import bcrypt
def check_bcrypt_password(stored_hash, password):
    # stored_hash est bytes, donc si tu l'as en str, encode en bytes
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    # password aussi doit être bytes
    password = password.encode('utf-8')
    return bcrypt.checkpw(password, stored_hash)
def allowed_file(filename):
    return filename.lower().endswith('.nii') or filename.lower().endswith('.nii.gz')
# Connexion à MySQL via WAMP
db = mysql.connector.connect(
    host="localhost",
    user="root",           
    password="",           
    database="flask_app"   
)
cursor = db.cursor(dictionary=True)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # Vérifier le format de l'email
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            flash("Format d'email invalide. Veuillez entrer une adresse email valide.", "danger")
            return render_template('register.html')
        try:
            cursor.execute("INSERT INTO users (username, password_hash, role, nom, prenom, email) VALUES (%s, %s, 'medecin', %s, %s, %s)", 
               (username, password_hash.decode('utf-8'), nom, prenom, email))
            db.commit()
            flash("Inscription réussie ! Vous pouvez maintenant vous connecter.")
            # return redirect(url_for('login'))
            return redirect(url_for('register', registered=1))
        except:
            db.rollback()
            return "Erreur : utilisateur déjà existant."
    return render_template('register.html')
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Aucune donnée reçue'}), 400
    username = data.get('username')
    password = data.get('password')
    nom = data.get('nom')
    prenom = data.get('prenom')
    email = data.get('email')
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, email):
        return jsonify({'message': "Format d'email invalide."}), 400
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, nom, prenom, email)
            VALUES (%s, %s, 'medecin', %s, %s, %s)
        """, (username, password_hash.decode('utf-8'), nom, prenom, email))
        db.commit()
        return jsonify({'message': 'Inscription réussie'}), 200
    except mysql.connector.IntegrityError:
        db.rollback()
        return jsonify({'message': 'Utilisateur déjà existant'}), 409
    except Exception as e:
        db.rollback()
        print("Erreur:", e)
        return jsonify({'message': 'Erreur serveur'}), 500
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        print("user from DB:", user)
        print("form password:", password)
        if user and check_bcrypt_password(user['password_hash'], password):
            session.permanent = True
            session['username'] = username
            session['role'] = user['role']
            session['user_id'] = user['id']
            session['logged_in'] = True
            session['nom'] = user['nom']
            session['prenom'] = user['prenom']
            return jsonify({"success": True, "message": "Connexion réussie"}), 200
        else:
            return jsonify({"success": False, "message": "Nom d'utilisateur ou mot de passe incorrect"}), 401
    # Réponse en cas de requête GET
    return render_template("login.html", error=error)

from functools import wraps
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            if request.path.startswith('/api/'):
                return jsonify({"error": "Non connecté"}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

UPLOAD_FOLDER = 'uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
from flask import Flask, jsonify
@app.route('/api/result')
def get_result():
    data = {
        "name": "Jean Dupont",
        "age": 58,
        "patient_id": "P123456",
        "tumor_volume": 1523.6,
        "tumor_location": [45.3, 60.2, 38.5],  # exemple coordonnées mm
        "dice_score": 0.87
    }
    return jsonify(data)
model = load_model("model.keras")
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'GET':
        return render_template('upload.html')
    if not session.get('logged_in'):
        return redirect('/')

    lastname = request.form['patient_lastname']
    firstname = request.form['patient_firstname']
    pid = request.form['patient_id']
    birthdate = request.form['patient_birthdate'].strip()# Date au format YYYY-MM-DD
    antecedents = request.form.get('antecedents', '')
    traitements = request.form.get('traitements', '')
    irm_date = request.form['irm_date']
    file = request.files['file']
    session['last_patient_id'] = pid
    session.modified = True  # <-- Important pour forcer Flask à sauvegarder la session
    try:
        birthdate_obj = datetime.strptime(birthdate, '%Y-%m-%d')
        age = (datetime.now() - birthdate_obj).days // 365  # Calcul direct plus simple
        if age < 0:
            return "La date de naissance ne peut pas être dans le futur", 400
    except ValueError as e:
        return "Format de date invalide. Utilisez AAAA-MM-JJ", 400
    if not file or not allowed_file(file.filename):
        return "Fichier non valide. Veuillez uploader un fichier .nii", 400

    # Sauvegarde du fichier IRM
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(filepath)
    session['last_uploaded_filename'] = secure_filename(file.filename)
    # Chargement du volume IRM
    img_obj = nib.load(filepath)
    img_3d = img_obj.get_fdata()
    mask_3d = np.zeros(img_3d.shape, dtype=np.uint8)
    # Traitement slice par slice
    for i in range(img_3d.shape[2]):
        slice_2d = np.rot90(img_3d[:, :, i])
        input_img, original_shape = preprocess_slice(slice_2d)
        pred = model.predict(input_img)[0, :, :, 0]
        pred_mask = (pred > 0.5).astype(np.uint8)
        pred_mask_resized = cv2.resize(pred_mask, (original_shape[1], original_shape[0]))
        pred_mask_resized = (pred_mask_resized > 0.5).astype(np.uint8)
        mask_3d[:, :, i] = np.rot90(pred_mask_resized, k=3)

    # Calcul du volume
    voxel_volume = np.prod(img_obj.header.get_zooms())  # mm³
    volume = calculate_volume(mask_3d, voxel_volume)

    # Dice score si masque fourni
    gt_file = request.files.get('ground_truth')
    dice = None
    if gt_file:
        gt_path = os.path.join(UPLOAD_FOLDER, secure_filename(gt_file.filename))
        gt_file.save(gt_path)
        gt_mask = nib.load(gt_path).get_fdata()
        dice = dice_coefficient((mask_3d > 0).astype(np.uint8), (gt_mask > 0).astype(np.uint8))

    # Centroïde
    spacing = img_obj.header.get_zooms()
    centroid_mm = get_centroid_3d_mm(mask_3d, spacing) if get_tumor_coordinates(mask_3d) else (0, 0, 0)

    # Génération image IRM brute centrale
    original_path = os.path.join('static', 'original.png')
    central_raw = img_3d[:, :, img_3d.shape[2] // 2]
    central_raw_norm = cv2.normalize(central_raw, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    cv2.imwrite(original_path, central_raw_norm)

    # Génération image avec superposition
    overlay_path = os.path.join('static', 'result.png')
    central_mask = mask_3d[:, :, img_3d.shape[2] // 2]
    overlay = overlay_mask(central_raw_norm, central_mask)
    cv2.imwrite(overlay_path, overlay)
    #Insérer les données du patient dans la base de données
    try:
        cursor.execute("INSERT INTO patients (id, lastname, firstname, age, antecedents, traitements, birthdate) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (pid, lastname, firstname, age, antecedents, traitements, birthdate)
                )
        db.commit()
    except mysql.connector.Error as err:
        db.rollback()
        return f"Erreur lors de l'enregistrement du patient: {err}", 500
    try:
        cursor.execute("""
            INSERT INTO results (patient_id, volume, centroid, dice, irm_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (pid, volume, str(centroid_mm), dice, irm_date))
        db.commit()
    except mysql.connector.Error as err:
        db.rollback()
        return f"Erreur lors de l'enregistrement des résultats: {err}", 500
    cursor.execute("SELECT nom, prenom FROM users WHERE username = %s", (session['username'],))
    medecin = cursor.fetchone()
    medecin_nom_complet = f"Dr. {session.get('prenom', '')} {session.get('nom', '')}"
    # Convertir le volume en cm³
    volume_cm3 = volume / 1000 
    return render_template('result.html',
        # patient_name=name,
        patient_lastname=lastname,
        patient_firstname=firstname,
        patient_id=pid,
        patient_birthdate=birthdate,
        patient_age=age,
        medecin=medecin_nom_complet,
        antecedents=antecedents,
        traitements=traitements,
        irm_date=irm_date,
        volume=volume_cm3,
        dice=dice,
        centroid=centroid_mm,
        original_image_file='original.png',
        segmented_mask_file='result.png',
        feedback_submitted=session.get('feedback_submitted', False),
        next_exam=request.form.get('next_exam', ''),
        recommendations=request.form.get('recommendations', '')
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/feedback', methods=['POST'])
def feedback():
    patient_id = request.form['patient_id']
    seg_ok = request.form['seg_ok']
    commentaire = request.form['commentaire']
    next_exam = request.form.get('next_exam', '')  # Nouveau champ
    recommendations = request.form.get('recommandations', 'Aucune')
    confiance = request.form.get('confidence', 3)
  # Nouveau champ (1-5)
    try:
        cursor.execute("""
            INSERT INTO feedbacks 
            (patient_id, seg_ok, commentaire, next_exam, confiance, recommendations) 
            VALUES (%s, %s, %s, %s, %s, %s)""",
            (patient_id, seg_ok, commentaire, next_exam, confiance, recommendations))
        db.commit()
        
        # Mettre à jour la session pour indiquer que le feedback a été soumis
        session['feedback_submitted'] = True
        return redirect(url_for('follow_up', patient_id=patient_id))
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({'error': str(err)})

@app.route('/feedbacks/<patient_id>')
def show_feedbacks(patient_id):
    try:
        cursor.execute("""
            SELECT seg_ok, commentaire, next_exam, confiance, recommendations, timestamp
            FROM feedbacks
            WHERE patient_id = %s
            ORDER BY timestamp DESC
        """, (patient_id,))
        feedbacks = cursor.fetchall()
        return render_template('feedbacks.html', feedbacks=feedbacks, patient_id=patient_id)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})
    
@app.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    # Récupération données formulaire
    f = request.files.get('file')
    gt_file = request.files.get('ground_truth')  # masque réel optionnel
    name = request.form.get('patient_name')
    pid = request.form.get('patient_id')
    age = request.form.get('patient_age')
    if not f:
        return jsonify({'error': 'Fichier IRM non fourni'}), 400
    filename = secure_filename(f.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    f.save(filepath)
    # Charger volume 3D IRM
    img_obj = nib.load(filepath)
    img_3d = img_obj.get_fdata()
    # Préparer masque prédiction vide (même shape que img)
    pred_mask_3d = np.zeros(img_3d.shape, dtype=np.uint8)
    for i in range(img_3d.shape[2]):
        slice_2d = np.rot90(img_3d[:, :, i])
        input_img, original_shape = preprocess_slice(slice_2d)  # Récupère la forme originale
        pred = model.predict(input_img)[0, :, :, 0]
        pred_mask = (pred > 0.5).astype(np.uint8)
        # Redimensionner à la taille originale avant rotation
        pred_mask_resized = cv2.resize(pred_mask, (original_shape[1], original_shape[0]))
        pred_mask_3d[:, :, i] = np.rot90(pred_mask_resized, k=3)
    # Calculs
    voxel_volume = np.prod(img_obj.header.get_zooms())  # volume voxel mm³
    volume = calculate_volume(pred_mask_3d, voxel_volume)
    centroid = get_centroid_3d_mm(pred_mask_3d, img_obj.header.get_zooms())
    dice = None
    if gt_file:
        gt_filename = secure_filename(gt_file.filename)
        gt_path = os.path.join(UPLOAD_FOLDER, gt_filename)
        gt_file.save(gt_path)
        gt_img_obj = nib.load(gt_path)
        gt_mask_3d = gt_img_obj.get_fdata().astype(np.uint8)
        dice = dice_coefficient(pred_mask_3d, gt_mask_3d)
    # Sauvegarder overlay de la première slice avec masque pour affichage
    first_slice_img = np.rot90(img_3d[:, :, 0]).astype(np.uint8)
    first_slice_mask = pred_mask_3d[:, :, 0]
    overlay_img = overlay_mask(first_slice_img, first_slice_mask)
    result_img_path = os.path.join('static', f'result_{pid}.png')
    cv2.imwrite(result_img_path, overlay_img)
    # Retour JSON
    return jsonify({
        'volume': round(volume, 2),
        'centroid': centroid,
        'dice': round(dice, 2) if dice is not None else None,
        'image_url': '/' + result_img_path.replace('\\', '/'),
        'patient_name': name,
        'patient_id': pid,
        'patient_age': age
    })

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('upload_file'))
    else:
        return redirect(url_for('login'))

@app.route('/test_bcrypt')
def test_bcrypt():
    stored_hash = "$2b$12$RbTUKxZf1Lq8nhlt7cu5RO1Ec/NrKhe4m1D3LEkPx0KlfQ1FhlNUq"
    password_attempt = "wiss123"
    is_valid = bcrypt.checkpw(password_attempt.encode('utf-8'), stored_hash.encode('utf-8'))
    return f"Le mot de passe 'wiss123' est valide pour le hash stocké ? {is_valid}"
@app.route('/generate_hashes')
def generate_hashes():
    """Route temporaire pour générer les hashs BCrypt des mots de passe"""
    users = {
        "medecin1": "medecin123",
        "medecin2": "medecin456",
        "medecin3": "pass123",
        "admin1": "admin123",
        "admin2": "root123",
        "wissal": "wiss123",
        "kawtar": "kawtar123"
    }

    output = "<h1>Requêtes SQL de mise à jour</h1><pre>"
    
    for username, pwd in users.items():
        hash = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        output += f"UPDATE users SET password_hash = '{hash}' WHERE username = '{username}';\n"
    
    output += "</pre>"
    return output
@app.route('/api/patients')
@login_required
def get_patients():
    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()
    return jsonify(patients)

@app.route('/api/results/<patient_id>')
@login_required
def get_patient_results(patient_id):
    cursor.execute("SELECT * FROM results WHERE patient_id = %s ORDER BY timestamp DESC", (patient_id,))
    results = cursor.fetchall()
    return jsonify(results)
@app.route('/check_data/<patient_id>')
@login_required
def check_data(patient_id):
    try:
        # Vérifier le patient
        cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        patient = cursor.fetchone()
        # Vérifier les résultats
        cursor.execute("SELECT * FROM results WHERE patient_id = %s ORDER BY timestamp DESC", (patient_id,))
        results = cursor.fetchall()
        # Vérifier les feedbacks
        cursor.execute("SELECT * FROM feedbacks WHERE patient_id = %s ORDER BY timestamp DESC", (patient_id,))
        feedbacks = cursor.fetchall()
        return jsonify({
            'patient': patient,
            'results': results,
            'feedbacks': feedbacks
        })
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    # Récupérer les données du formulaire
    data = request.form
    # Enregistrer en base
    cursor.execute("""INSERT INTO feedbacks (...) VALUES (...)""", (...))
    db.commit()
    # Rediriger vers la page de suivi
    return redirect(url_for('follow_up', patient_id=data['patient_id']))

@app.route('/follow_up/<patient_id>')
@login_required
def follow_up(patient_id):
    # 1. Récupérer les dernières infos du patient
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    # 2. Récupérer le dernier feedback
    cursor.execute("""
        SELECT next_exam, recommendations 
        FROM feedbacks 
        WHERE patient_id = %s 
        ORDER BY timestamp DESC 
        LIMIT 1
    """, (patient_id,))
    feedback = cursor.fetchone()
    cursor.execute("""
    SELECT volume, centroid, dice, irm_date
    FROM results 
    WHERE patient_id = %s 
    ORDER BY timestamp DESC 
    LIMIT 1
    """, (patient_id,))
    result = cursor.fetchone()
    
    # 3. Rendre le template avec les données
    return render_template('follow_up.html',
        patient_lastname=patient['lastname'],
        patient_firstname=patient['firstname'],
        patient_id=patient_id,
        patient_age=patient['age'],
        volume=result['volume'] / 1000 if result else 0,
        centroid=result['centroid'] if result else "Non disponible",
        dice=result['dice'] if result else None,
        next_exam=feedback['next_exam'] if feedback else "Non spécifié",
        recommendations=feedback['recommendations'] if feedback else "Aucune",
        irm_date=result['irm_date'] if result and result['irm_date'] else 'Non spécifiée',
        antecedents=patient.get('antecedents', 'Aucun'),
        traitements=patient.get('traitements', 'Aucun'),
        medecin=session['username']  # Nom du médecin connecté
    )  
@app.route('/api/analyze', methods=['POST'])
@login_required
def api_analyze():
    try:
        # 1. Récupération des données
        patient_data = {
            'name': request.form['patient_name'],
            'id': request.form['patient_id'],
            'birthdate': request.form['patient_birthdate']
        }
        # 2. Traitement du fichier (simplifié)
        file = request.files['file']
        filepath = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(filepath)
        
        # 3. Analyse médicale (exemple simplifié)
        img_obj = nib.load(filepath)
        img_3d = img_obj.get_fdata()
        volume = np.sum(img_3d > 0.5) * np.prod(img_obj.header.get_zooms())
        
        # 4. Préparation réponse JSON
        return jsonify({
            'status': 'success',
            'patient': patient_data,
            'results': {
                'volume': round(volume, 2),
                'centroid': [120, 130, 80],  # Exemple
                'dice_score': None  # Si pas de ground truth
            },
            'images': {
                'original': url_for('static', filename='original.png'),
                'mask': url_for('static', filename='result.png')
            },
            'medecin': session['username']
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
@app.route('/api/feedback', methods=['POST'])
@login_required
def api_feedback():
    try:
        data = request.json  # Pour React on utilisera du JSON
        # Validation minimale
        if not all(k in data for k in ['patient_id', 'seg_ok', 'commentaire']):
            raise ValueError("Données manquantes")
        # Insertion en base
        cursor.execute("""
            INSERT INTO feedbacks 
            (patient_id, seg_ok, commentaire, next_exam, recommendations)
            VALUES (%s, %s, %s, %s, %s)
            """, (
                data['patient_id'],
                data['seg_ok'],
                data['commentaire'],
                data.get('next_exam', ''),
                data.get('recommendations', '')
            ))
        db.commit()
        
        return jsonify({
            'status': 'success',
            'patient_id': data['patient_id'],
            'next_exam': data.get('next_exam', '')
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/generate_report', methods=['POST'])
@login_required
def generate_report():
    try:
        # Récupération des données du formulaire
        data = {
            'patient_id': request.form.get('patient_id', 'Non spécifié'),
            'patient_lastname': request.form.get('patient_lastname', 'Non spécifié'),
            'patient_firstname': request.form.get('patient_firstname', 'Non spécifié'),
            'patient_age': request.form.get('patient_age', 'Non spécifié'),
            'volume': request.form.get('volume', '0'),
            'centroid': request.form.get('centroid', 'Non disponible'),
            'dice': request.form.get('dice', 'Non calculé'),
            'next_exam': request.form.get('next_exam', 'Non spécifié'),
            'recommendations': request.form.get('recommendations', 'Aucune'),
            'antecedents': request.form.get('antecedents', 'Aucun'),
            'traitements': request.form.get('traitements', 'Aucun'),
            'irm_date': request.form.get('irm_date', 'Non spécifiée')
        }

        # Nom complet du médecin
        medecin_nom = f"Dr. {session.get('prenom', '')} {session.get('nom', '')}"

        # Création du PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # ===== Page 1 =====
        # Titre
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Rapport Médical de Segmentation Tumorale', 0, 1, 'C')
        pdf.ln(10)

        # Section Patient
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Informations Patient', 0, 1)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"Nom: {data['patient_lastname']} {data['patient_firstname']}", 0, 1)
        pdf.cell(0, 10, f"ID: {data['patient_id']}", 0, 1)
        pdf.cell(0, 10, f"Âge: {data['patient_age']} ans", 0, 1)
        pdf.cell(0, 10, f"Antécédents: {data['antecedents']}", 0, 1)
        pdf.cell(0, 10, f"Traitements: {data['traitements']}", 0, 1)
        pdf.cell(0, 10, f"Date de l'IRM: {data['irm_date']}", 0, 1)
        pdf.cell(0, 10, f"Médecin responsable: {medecin_nom}", 0, 1)
        pdf.ln(10)

        # Section Résultats
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "Résultats de l'analyse", 0, 1)
        pdf.set_font('Arial', '', 12)
        try:
            volume_cm3 = float(data['volume']) 
            if volume_cm3 > 0:
                pdf.cell(0, 10, f"Volume tumoral: {volume_cm3:.2f} cm³", 0, 1)
                pdf.cell(0, 10, f"Localisation tumorale: {data['centroid']}", 0, 1)
            else:
                pdf.cell(0, 10, "Tumeur non détectée", 0, 1)
        except ValueError:
            pdf.cell(0, 10, "Volume tumoral: Données non valides", 0, 1)

        if data['dice'] != 'Non calculé':
            pdf.cell(0, 10, f"Score Dice: {data['dice']}", 0, 1)
        pdf.ln(10)

        # Section Recommandations
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "Recommandations médicales", 0, 1)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"Prochain examen: {data['next_exam']}", 0, 1)
        pdf.multi_cell(0, 10, f"Recommandations: {data['recommendations']}")

        # ===== Page 2 =====
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Visualisation des résultats', 0, 1, 'C')
        pdf.ln(10)

        # Images
        image_paths = [
            ('static/original.png', '_Image IRM originale_'),
            ('static/result.png', '_Masque de segmentation_')
        ]
        
        if os.path.exists('static/original.png') and os.path.exists('static/result.png'):
            pdf.set_font('Arial', 'I', 12)
            pdf.cell(95, 10, "Image IRM originale", 0, 0, 'C')
            pdf.cell(0, 10, "Masque de segmentation", 0, 1, 'C')
            pdf.image('static/original.png', x=25, y=pdf.get_y(), w=70)
            pdf.image('static/result.png', x=110, y=pdf.get_y(), w=70)
            pdf.ln(45)  # Adapter si nécessaire
        else:
            pdf.cell(0, 10, "Images non disponibles", 0, 1, 'C')
        pdf.set_y(255)  # légèrement plus haut que 250 pour éviter le dépassement

        pdf.set_font('Arial', 'I', 9)
        pdf.cell(0, 6, f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", 0, 1, 'C')
        pdf.cell(0, 6, f"Médecin responsable : {medecin_nom}", 0, 1, 'C')
        pdf.cell(0, 6, "Signature :", 0, 1, 'C')
        # pdf.cell(0, 6, "_" * 40, 0, 1, 'C')
        pdf.cell(0, 6, "______________________________", 0, 1, 'C')

        # Mention légale plus compacte
        pdf.ln(2)
        pdf.set_font('Arial', 'I', 7)
        pdf.multi_cell(0, 4, "Ce rapport est généré automatiquement à partir d'une analyse IA. Il ne remplace pas un diagnostic médical officiel.", 0, 'C')
        # Sauvegarde
        report_path = os.path.join("static", f"report_{data['patient_id']}.pdf")
        pdf.output(report_path)
        return send_file(report_path, as_attachment=True)

    except Exception as e:
        return f"Erreur lors de la génération du rapport : {e}", 500
@app.route('/api/latest_result')
@login_required
def latest_result():
    # récupère le dernier patient ou ID courant
    patient_id = session.get('last_patient_id')
    if not session.get('logged_in'):
        return jsonify({'error': 'Non autorisé'}), 401
    if not patient_id:
        return jsonify({'error': 'Aucun patient trouvé'}), 400
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    cursor.execute("SELECT * FROM results WHERE patient_id = %s ORDER BY timestamp DESC LIMIT 1", (patient_id,))
    result = cursor.fetchone()

    return jsonify({
        "patient_lastname": patient["lastname"],
        "patient_firstname": patient["firstname"],
        "patient_id": patient_id,
        "patient_birthdate": patient["birthdate"],
        "patient_age": patient["age"],
        "antecedents": patient.get("antecedents", ""),
        "traitements": patient.get("traitements", ""),
        "irm_date": result.get("irm_date", ""),
        "volume": round(result["volume"] / 1000, 2),
        "dice": result["dice"],
        "centroid": result["centroid"],
        "medecin": f"Dr. {session.get('prenom', '')} {session.get('nom', '')}"
    })
@app.route('/api/follow_up/<id>')
@login_required
def api_follow_up(id):
    cursor.execute("SELECT firstname, lastname FROM patients WHERE id = %s", (id,))
    patient = cursor.fetchone()
    cursor.execute("SELECT next_exam, recommendations FROM feedbacks WHERE patient_id = %s ORDER BY timestamp DESC LIMIT 1", (id,))
    feedback = cursor.fetchone()
    if not patient or not feedback:
        return jsonify({'error': 'Informations de suivi introuvables'}), 404

    return jsonify({
        "prenom": patient["firstname"],
        "nom": patient["lastname"],
        "patient_id": id,
        "next_exam": feedback["next_exam"],
        "recommendations": feedback["recommendations"]
    })
@app.route('/download_report/<patient_id>')
@login_required
def download_report(patient_id):
    pdf_path = os.path.join('static', f'report_{patient_id}.pdf')
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return "Rapport non trouvé", 404
@app.route('/api/latest_result')
@login_required
def api_latest_result():
    pid = session.get('last_patient_id')
    if not pid:
        return jsonify({'error': 'Aucun patient récent'}), 400

    cursor.execute("SELECT * FROM patients WHERE id = %s", (pid,))
    patient = cursor.fetchone()
    
    cursor.execute("""
        SELECT volume, centroid, dice, irm_date 
        FROM results WHERE patient_id = %s ORDER BY timestamp DESC LIMIT 1
    """, (pid,))
    result = cursor.fetchone()

    if not patient or not result:
        return jsonify({'error': 'Données manquantes'}), 404

    return jsonify({
        "patient_lastname": patient["lastname"],
        "patient_firstname": patient["firstname"],
        "patient_id": patient["id"],
        "patient_birthdate": patient["birthdate"],
        "patient_age": patient["age"],
        "antecedents": patient["antecedents"],
        "traitements": patient["traitements"],
        "irm_date": result["irm_date"],
        "volume": result["volume"] / 1000,
        "centroid": result["centroid"],
        "dice": result["dice"],
        "medecin": f"Dr. {session.get('prenom')} {session.get('nom')}"
    })
@app.route('/generate_and_download/<patient_id>')
@login_required
def generate_and_download(patient_id):
    # Appelle la fonction qui génère le rapport PDF
    generate_pdf_report(patient_id)  # tu dois avoir cette fonction quelque part
    pdf_path = os.path.join('static', f'rapport_{patient_id}.pdf')
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return "Erreur lors de la génération du rapport", 500

def generate_pdf_report(patient_id):
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()

    cursor.execute("SELECT * FROM results WHERE patient_id = %s ORDER BY timestamp DESC LIMIT 1", (patient_id,))
    result = cursor.fetchone()

    cursor.execute("SELECT * FROM feedbacks WHERE patient_id = %s ORDER BY timestamp DESC LIMIT 1", (patient_id,))
    feedback = cursor.fetchone()

    if not patient or not result:
        print(" Données manquantes")
        return

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Logo à droite + titre bleu à gauche
    if os.path.exists("static/logo.png"):
        pdf.image("static/logo.png", x=170, y=8, w=25)  # logo à droite

    pdf.set_xy(10, 10)
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 51, 102)  # bleu foncé
    pdf.cell(0, 10, "Rapport Médical de Segmentation Tumorale", ln=1, align='C')

    # ligne de séparation
    pdf.set_draw_color(0, 51, 102)
    pdf.set_line_width(0.8)
    pdf.line(10, 25, 200, 25)
    pdf.ln(15)

    # 🧍 Informations Patient
    pdf.set_text_color(0, 51, 102)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Informations Patient", ln=1)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Nom : {patient['lastname']} {patient['firstname']}", ln=1)
    pdf.cell(0, 10, f"ID : {patient['id']}", ln=1)
    pdf.cell(0, 10, f"Âge : {patient['age']} ans", ln=1)
    pdf.cell(0, 10, f"Antécédents : {patient['antecedents']}", ln=1)
    pdf.cell(0, 10, f"Traitements : {patient['traitements']}", ln=1)
    pdf.cell(0, 10, f"Date IRM : {result['irm_date']}", ln=1)
    pdf.cell(0, 10, f"Médecin : Dr. {session.get('prenom')} {session.get('nom')}", ln=1)
    pdf.ln(5)

    # Résultats
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "Résultats de l'analyse", ln=1)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 12)
    try:
        volume = float(result['volume']) / 1000
        pdf.cell(0, 10, f"Volume tumoral : {volume:.2f} cm³", ln=1)
    except:
        pdf.cell(0, 10, "Volume tumoral : non disponible", ln=1)

    pdf.cell(0, 10, f"Centroïde : {result.get('centroid', 'Non disponible')}", ln=1)
    pdf.cell(0, 10, f"Score Dice : {result.get('dice', 'Non calculé')}", ln=1)
    pdf.ln(5)

    # Feedback
    if feedback:
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, "Recommandations médicales", ln=1)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Prochain examen : {feedback.get('next_exam', 'Non défini')}", ln=1)
        pdf.multi_cell(0, 10, f"Recommandations : {feedback.get('recommendations', 'Aucune')}")
        pdf.ln(3)

    # Images
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "Visualisation des Résultats", ln=1, align='C')
    pdf.ln(5)

    if os.path.exists('static/original.png') and os.path.exists('static/result.png'):
        pdf.set_font("Arial", 'I', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(95, 10, "IRM originale", 0, 0, 'C')
        pdf.cell(0, 10, "Masque de segmentation", 0, 1, 'C')
        pdf.image("static/original.png", x=25, y=pdf.get_y(), w=70)
        pdf.image("static/result.png", x=110, y=pdf.get_y(), w=70)
    else:
        pdf.set_text_color(100, 0, 0)
        pdf.cell(0, 10, " Images non disponibles", ln=1, align='C')

    #  Pied de page
    pdf.set_y(255)
    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", ln=1, align='C')
    pdf.cell(0, 6, f"Médecin : Dr. {session.get('prenom')} {session.get('nom')}", ln=1, align='C')
    pdf.cell(0, 6, "Signature :", ln=1, align='C')

    # Sauvegarde
    report_path = os.path.join("static", f"rapport_{patient_id}.pdf")
    pdf.output(report_path)
    print(f" Rapport sauvegardé : {report_path}")
if __name__ == '__main__':
    app.run(debug=True)
    

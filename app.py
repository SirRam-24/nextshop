import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from bson.objectid import ObjectId

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret')

# Configure MongoDB
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/nextshop')
client = MongoClient(mongo_uri)
db = client.get_database()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

@app.route('/')
def index():
    team = list(db.team.find())
    projects = list(db.projects.find())
    faqs = list(db.faqs.find())
    return render_template('index.html', team=team, projects=projects, faqs=faqs)

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    email = request.form.get('email')
    service = request.form.get('service')
    message = request.form.get('message')
    db.contacts.insert_one({
        'name': name,
        'email': email,
        'service': service,
        'message': message
    })
    flash('Thank you! Your message has been sent.', 'success')
    return redirect(url_for('index'))

# Admin Auth Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'nextshop@' and password == '12345':
            session['logged_in'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    contacts = list(db.contacts.find().sort('_id', -1))
    return render_template('admin/dashboard.html', contacts=contacts)

# Team Admin
@app.route('/admin/team', methods=['GET', 'POST'])
@login_required
def admin_team():
    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role')
        image = request.files.get('image')
        image_url = ''
        if image and image.filename != '':
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result.get('secure_url')
        
        db.team.insert_one({'name': name, 'role': role, 'image_url': image_url})
        flash('Team member added successfully!', 'success')
        return redirect(url_for('admin_team'))
        
    team_members = list(db.team.find())
    return render_template('admin/team.html', team=team_members)

@app.route('/admin/team/delete/<member_id>')
@login_required
def delete_team(member_id):
    db.team.delete_one({'_id': ObjectId(member_id)})
    flash('Team member deleted.', 'success')
    return redirect(url_for('admin_team'))

# Projects Admin
@app.route('/admin/projects', methods=['GET', 'POST'])
@login_required
def admin_projects():
    if request.method == 'POST':
        name = request.form.get('name')
        tech = request.form.get('tech')
        description = request.form.get('description')
        demo_url = request.form.get('demo_url')
        image = request.files.get('image')
        image_url = ''
        if image and image.filename != '':
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result.get('secure_url')
            
        db.projects.insert_one({
            'name': name,
            'tech': tech,
            'description': description,
            'demo_url': demo_url,
            'image_url': image_url
        })
        flash('Project added successfully!', 'success')
        return redirect(url_for('admin_projects'))
        
    projects = list(db.projects.find())
    return render_template('admin/projects.html', projects=projects)

@app.route('/admin/projects/delete/<project_id>')
@login_required
def delete_project(project_id):
    db.projects.delete_one({'_id': ObjectId(project_id)})
    flash('Project deleted.', 'success')
    return redirect(url_for('admin_projects'))

# FAQ Admin
@app.route('/admin/faqs', methods=['GET', 'POST'])
@login_required
def admin_faqs():
    if request.method == 'POST':
        question = request.form.get('question')
        answer = request.form.get('answer')
        db.faqs.insert_one({'question': question, 'answer': answer})
        flash('FAQ added successfully!', 'success')
        return redirect(url_for('admin_faqs'))
        
    faqs = list(db.faqs.find())
    return render_template('admin/faq.html', faqs=faqs)

@app.route('/admin/faqs/delete/<faq_id>')
@login_required
def delete_faq(faq_id):
    db.faqs.delete_one({'_id': ObjectId(faq_id)})
    flash('FAQ deleted.', 'success')
    return redirect(url_for('admin_faqs'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

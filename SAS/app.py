import os
from datetime import datetime, timedelta
from flask import (Flask, render_template, request, redirect, url_for, flash,
                   Response, session, abort, make_response)
from flask_login import (LoginManager, UserMixin, login_user, login_required,
                         logout_user, current_user)
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

import os
from datetime import datetime, timedelta
from flask import (Flask, render_template, request, redirect, url_for, flash,
                   Response, session, abort, make_response)
from flask_login import (LoginManager, UserMixin, login_user, login_required,
                         logout_user, current_user)
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from weasyprint import HTML
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"

app.secret_key = os.environ.get('SECRET_KEY', 'a_secure_random_secret_key_for_development')

# --- DATABASE CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql+psycopg2://tsb_jilz_user:WQuuirqxSdknwZjsvldYzD0DbhcOBzQ7@dpg-d0jjegmmcj7s73836lp0-a.frankfurt-postgres.render.com:5432/tsb_jilz'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
# --- DATABASE MODELS ---


# --- DECORATEUR DE ROLE ---
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403) # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator

hebergement_employee_association = db.Table('hebergement_employee_association',
    db.Column('hebergement_id', db.Integer, db.ForeignKey('hebergement.id'), primary_key=True),
    db.Column('employee_id', db.Integer, db.ForeignKey('employee.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")
    
    # --- C'est la relation cruciale qui manque ---
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    employee = db.relationship('Employee', backref='user', uselist=False, lazy='joined')
    
    # Relation vers les documents (déjà présente dans votre code)
    documents = db.relationship('Document', backref='owner', lazy=True)
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(50), default='Prospect')
    last_contact_date = db.Column(db.DateTime, default=datetime.utcnow)
    quotes = db.relationship('Quote', backref='client', lazy=True, cascade="all, delete-orphan")
    chantiers = db.relationship('Chantier', backref='client', lazy=True)
    factures = db.relationship('Facture', backref='client', lazy=True)
    sav_tickets = db.relationship('SavTicket', backref='client', lazy=True)
class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(50), default='In Service')
    notes = db.Column(db.Text, nullable=True)
    brand = db.Column(db.String(80), nullable=True)
    model = db.Column(db.String(80), nullable=True)
    last_maintenance_date = db.Column(db.Date, nullable=True)
    next_maintenance_date = db.Column(db.Date, nullable=True)
    immatriculation = db.Column(db.String(50), nullable=True)
    responsable_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    responsable = db.relationship('Employee')
    date_debut_responsabilite = db.Column(db.Date, nullable=True)
    date_fin_responsabilite = db.Column(db.Date, nullable=True)
    type_engin = db.Column(db.String(100), nullable=True)
    hauteur = db.Column(db.Float, nullable=True)
    date_vgp = db.Column(db.Date, nullable=True)
    nombre_cles = db.Column(db.Integer, nullable=True)
    photo_fuel_url = db.Column(db.String(500), nullable=True)
    serial_number = db.Column(db.String(120), unique=True, nullable=True)
    type_materiel = db.Column(db.String(100), nullable=True)
    etat = db.Column(db.String(50), nullable=True)


class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    
    # AJOUTEZ CETTE LIGNE 👇
    service_type = db.Column(db.String(200), nullable=True)
    
    details = db.Column(db.Text)
    price = db.Column(db.Float)
    vat_rate = db.Column(db.Float, default=0.20)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def total_price(self):
        return self.price * (1 + self.vat_rate) if self.price and self.vat_rate is not None else 0
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    hire_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    salary = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    _requests = db.relationship('Request', backref='employee', lazy='dynamic')
    hebergements = db.relationship('Hebergement', secondary=hebergement_employee_association, back_populates='employees')
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    _type = db.Column(db.String(50), nullable=False, default='Annual ')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')
    proposed_start_date = db.Column(db.Date, nullable=True)
    proposend_date = db.Column(db.Date, nullable=True)
class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    position_applied_for = db.Column(db.String(100), nullable=False)
    application_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Applied')
class Chantier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    status = db.Column(db.String(50), default='Planifié')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    documents = db.relationship('Document', backref='chantier', lazy=True)
class Facture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Brouillon')
    due_date = db.Column(db.Date)
    pdf_filename = db.Column(db.String(300), nullable=True) 

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  # Renommé de 'filename' à 'name'
    url = db.Column(db.String(500), nullable=False)   # Nouveau champ pour le lien
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    chantier_id = db.Column(db.Integer, db.ForeignKey('chantier.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
class SavTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Ouvert')
class PlanningEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
class Hebergement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(300), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    employees = db.relationship('Employee', secondary=hebergement_employee_association, back_populates='hebergements')

# --- AUTHENTICATION & CORE ROUTES ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and bcrypt.check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            # On vérifie le rôle pour la redirection
            if current_user.role == 'CEO':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('bienvenue'))
    return render_template('main_template.html', view='login')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
@role_required(['CEO'])
def dashboard():
    clients = Client.query.order_by(Client.last_contact_date.desc()).limit(5).all()
    quotes = Quote.query.filter_by(status='Pending').order_by(Quote.created_at.desc()).limit(5).all()
    return render_template('main_template.html', view='dashboard', clients=clients, quotes=quotes)

# --- ROUTES "AUTRES" (Accès: Tous les utilisateurs connectés) ---
@app.route('/clients')
@login_required
@role_required(['CEO', 'RH']) # <-- AJOUTÉ
def list_clients():
    clients = Client.query.order_by(Client.name).all()
    return render_template('main_template.html', view='clients_list', clients=clients)

# ADD THIS NEW ROUTE
@app.route('/quote/pdf/<int:quote_id>')
@login_required
@role_required(['CEO', 'Finance']) # Protect the route
def generate_quote_pdf(quote_id):
    """Generates a PDF for a specific quote."""
    # 1. Fetch the quote from the database
    quote = Quote.query.get_or_404(quote_id)
    
    # 2. Render an HTML template with the quote's data
    #    (You'll need to create this template, see step 2 below)
    rendered_html = render_template('quote_pdf_template.html', quote=quote)
    
    # 3. Use WeasyPrint to convert the HTML to a PDF
    pdf = HTML(string=rendered_html).write_pdf()
    
    # 4. Return the PDF as a response to the browser
    return Response(pdf,
                    mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment;filename=devis_{quote.quote_number}.pdf'})

@app.route('/planning')
@login_required
def list_planning():
    events = PlanningEvent.query.all()
    return render_template('main_template.html', view='planning_list', events=events)

@app.route('/documents')
@login_required
def list_documents():
     # Le CEO voit tous les documents
    if current_user.role == 'CEO':
        documents = Document.query.order_by(Document.upload_date.desc()).all()
    # Les autres utilisateurs ne voient que les leurs
    else:
        documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.upload_date.desc()).all()
        
    return render_template('main_template.html', view='documents_list', documents=documents)

@app.route('/documents/add', methods=['GET', 'POST'])
@login_required
def add_document():
    if request.method == 'POST':
        filename = request.form.get('filename')
        if not filename:
            flash("Le nom du fichier est requis.", "danger")
        else:
            # On associe le document à l'utilisateur actuellement connecté
            new_doc = Document(filename=filename, owner=current_user)
            db.session.add(new_doc)
            db.session.commit()
            flash("Document ajouté avec succès.", "success")
            return redirect(url_for('list_documents'))

    # Affiche un simple formulaire (pour l'exemple)
    return render_template('main_template.html', view='document_form')

@app.route('/client/add', methods=['GET', 'POST'])
@login_required
@role_required(['CEO', 'RH'])
def add_client():

    if request.method == 'POST':
        new_client = Client(
            name=request.form['name'], 
            email=request.form['email'], 
            phone=request.form['phone'], 
            address=request.form['address'], 
            status=request.form['status']
        )
        db.session.add(new_client)
        db.session.commit()
        flash('Client ajouté avec succès !', 'success')
        return redirect(url_for('list_clients'))
    return render_template('main_template.html', view='client_form', form_title="Ajouter un Client", client=None)

@app.route('/client/edit/<int:client_id>', methods=['GET', 'POST'])
@login_required
@role_required(['CEO', 'RH'])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        client.name = request.form['name']
        client.email = request.form['email']
        client.phone = request.form['phone']
        client.address = request.form['address']
        client.status = request.form['status']
        client.last_contact_date = datetime.utcnow()
        db.session.commit()
        flash('Client mis à jour avec succès !', 'success')
        return redirect(url_for('client_profile', client_id=client.id))
    return render_template('main_template.html', view='client_form', form_title="Modifier le Client", client=client)
@app.route('/candidate/add', methods=['GET', 'POST'])
@login_required
@role_required(['CEO', 'RH'])
def add_candidate():
    if request.method == 'POST':
        new_candidate = Candidate(
            full_name=request.form['full_name'],
            email=request.form['email'],
            phone=request.form.get('phone'),
            position_applied_for=request.form['position_applied_for'],
            notes=request.form.get('notes')
        )
        db.session.add(new_candidate)
        db.session.commit()
        flash('Nouveau candidat ajouté avec succès.', 'success')
        return redirect(url_for('list_candidates'))

    return render_template('main_template.html', view='candidate_form', form_title="Ajouter un Candidat")

@app.route('/candidate/view/<int:candidate_id>', methods=['GET', 'POST'])
@login_required
@role_required(['CEO', 'RH'])
def view_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    if request.method == 'POST':
        candidate.status = request.form.get('status', candidate.status)
        candidate.notes = request.form.get('notes', candidate.notes)
        db.session.commit()
        flash('Profil du candidat mis à jour.', 'success')
        return redirect(url_for('view_candidate', candidate_id=candidate.id))
        
    return render_template('main_template.html', view='candidate_profile', candidate=candidate)

@app.route('/Bienvenue')
@login_required
def bienvenue():
    # Cette page sert de portail pour les utilisateurs non-CEO
    return render_template('main_template.html', view='bienvenue_page')

@app.route('/client/<int:client_id>')
@login_required
@role_required(['CEO', 'RH'])
def client_profile(client_id):
    client = Client.query.get_or_404(client_id)
    return render_template('main_template.html', view='client_profile', client=client)

# --- ROUTES "OPÉRATIONS" (Accès: CEO, Chef de projet) ---
@app.route('/equipment')
@login_required
@role_required(['CEO', 'Chef de projet', 'Employé'])
def list_equipment():
    equipment_list = Equipment.query.all()
    return render_template('main_template.html', view='equipment_list', equipment=equipment_list)

@app.route('/chantiers')
@login_required
@role_required(['CEO', 'Chef de projet', 'Employé'])
def list_chantiers():
    chantiers = Chantier.query.all()
    return render_template('main_template.html', view='chantiers_list', chantiers=chantiers)

@app.route('/sav')
@login_required
@role_required(['CEO', 'Chef de projet', 'Employé'])
def list_sav():
    tickets = SavTicket.query.all()
    return render_template('main_template.html', view='sav_list', tickets=tickets)


# --- ROUTES "FINANCES" (Accès: CEO, Finance) ---
@app.route('/quotes')
@login_required
@role_required(['CEO', 'Finance'])
def list_quotes():
    quotes = Quote.query.order_by(Quote.created_at.desc()).all()
    return render_template('main_template.html', view='quote_list', quotes=quotes)

@app.route('/factures')
@login_required
@role_required(['CEO', 'Finance'])
def list_factures():
    factures = Facture.query.all()
    return render_template('main_template.html', view='factures_list', factures=factures)


# --- ROUTES "RH" (Accès: CEO, RH) ---
@app.route('/employees')
@login_required
@role_required(['CEO', 'RH'])
def list_employees():
    employees = Employee.query.order_by(Employee.full_name).all()
    return render_template('main_template.html', view='employees_list', employees=employees)


@app.route('/candidates')
@login_required
@role_required(['CEO', 'RH'])
def list_candidates():
    candidates = Candidate.query.order_by(Candidate.application_date.desc()).all()
    return render_template('main_template.html', view='candidates_list', candidates=candidates)

@app.route('/planning/add', methods=['GET', 'POST'])
@login_required
def add_planning_event():
    if request.method == 'POST':
        title = request.form.get('title')
        start_str = request.form.get('start_time')
        end_str = request.form.get('end_time')
        description = request.form.get('description')

        if not title or not start_str or not end_str:
            flash("Le titre et les dates de début et de fin sont requis.", "danger")
        else:
            # Conversion des chaînes de caractères en objets datetime
            start_time = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
            end_time = datetime.strptime(end_str, '%Y-%m-%dT%H:%M')

            new_event = PlanningEvent(
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description
            )
            db.session.add(new_event)
            db.session.commit()
            flash("Nouvel événement ajouté au planning.", "success")
            return redirect(url_for('list_planning'))
    
    return render_template('main_template.html', view='planning_form', form_title="Ajouter un Événement")
# --- ROUTES "ADMINISTRATION" (Accès: CEO Seulement) ---

@app.route('/users')
@login_required
@role_required(['CEO'])
def manage_users():
    users = User.query.all()
    
    # 1. On récupère les IDs de tous les employés déjà liés à un compte
    linkemployee_ids = [user.employee_id for user in users if user.employee_id]
    
    # 2. On récupère les employés qui ne sont PAS dans cette liste
    unlinkemployees = Employee.query.filter(Employee.id.notin_(linked_employee_ids)).all()

    return render_template('main_template.html', view='users_list', users=users, unlinked_employees=unlinked_employees)


@app.route('/quote/add', methods=['GET', 'POST'])
@login_required
@role_required(['CEO', 'Finance'])
def add_quote():
    if request.method == 'POST':
        # ... (code for quote_number) ...
        new_quote = Quote(
            quote_number=quote_number,
            client_id=request.form['client_id'],
            
            # AJOUTEZ CETTE LIGNE 👇
            service_type=request.form['service_type'],

            details=request.form['details'],
            price=float(request.form['price']),
            vat_rate=float(request.form['vat_rate'])
        )
        db.session.add(new_quote)
        db.session.commit()
        flash(f'Devis {quote_number} créé.', 'success')
        return redirect(url_for('list_quotes'))
    clients = Client.query.all()
    return render_template('main_template.html', view='quote_form', clients=clients)

@app.route('/sav/add', methods=['GET', 'POST'])
@login_required
@role_required(['CEO', 'Chef de projet'])
def add_sav_ticket():
    if request.method == 'POST':
        last_ticket = SavTicket.query.order_by(SavTicket.id.desc()).first()
        new_id = (last_ticket.id + 1) if last_ticket else 1
        ticket_number = f"TICKET-{datetime.now().year}-{new_id:04d}"
        new_ticket = SavTicket(
            ticket_number=ticket_number,
            client_id=request.form['client_id'],
            description=request.form['description'],
            status='Ouvert'
        )
        db.session.add(new_ticket)
        db.session.commit()
        flash('Ticket SAV créé.', 'success')
        return redirect(url_for('list_sav'))
    clients = Client.query.all()
    return render_template('main_template.html', view='sav_form', clients=clients, form_title="Nouveau Ticket SAV")

@app.route('/facture/add', methods=['GET', 'POST'])
@login_required
@role_required(['CEO', 'Finance'])
def add_facture():
    if request.method == 'POST':
        last_invoice = Facture.query.order_by(Facture.id.desc()).first()
        new_id = (last_invoice.id + 1) if last_invoice else 1
        invoice_number = f"FACT-{datetime.now().year}-{new_id:04d}"
        new_facture = Facture(
            invoice_number=invoice_number,
            client_id=request.form['client_id'],
            amount=float(request.form['amount']),
            due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d').date() if request.form['due_date'] else None,
            status='Brouillon'
        )
        pdf_file = request.files.get('pdf_file')
        if pdf_file and pdf_file.filename != '':
            # Sécuriser le nom du fichier
            filename = secure_filename(pdf_file.filename)
            # Sauvegarder le fichier dans notre dossier UPLOAD_FOLDER
            pdf_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Enregistrer le nom du fichier dans la base de données
            new_facture.pdf_filename = filename

        db.session.add(new_facture)
        db.session.commit()
        flash('Facture créée avec succès.', 'success')
        return redirect(url_for('list_factures'))

    clients = Client.query.all()
    return render_template('main_template.html', view='facture_form', clients=clients, form_title="Nouvelle Facture")

@app.route('/users/add', methods=['POST'])
@login_required
@role_required(['CEO'])
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    employee_id = request.form.get('employee_id') # On récupère l'ID de l'employé

    if User.query.filter_by(username=username).first():
        flash("Ce nom d'utilisateur existe déjà.", "warning")
        return redirect(url_for('manage_users'))
        
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # On convertit l'ID en entier, ou on le met à None s'il est vide
    employee_id_to_set = int(employee_id) if employee_id else None

    new_user = User(username=username, password_hash=hashed_password, role=role, employee_id=employee_id_to_set)
    db.session.add(new_user)
    db.session.commit()
    flash("Nouvel utilisateur ajouté avec succès.", "success")
    return redirect(url_for('manage_users'))


@app.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required(['CEO'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'CEO' and current_user.id != user.id:
        flash("Le compte CEO ne peut pas être modifié par un autre utilisateur.", "warning")
        return redirect(url_for('manage_users'))

    if request.method == 'POST':
        user.role = request.form.get('role')
        employee_id = request.form.get('employee_id')
        user.employee_id = int(employee_id) if employee_id else None
        db.session.commit()
        flash("Utilisateur mis à jour avec succès.", "success")
        return redirect(url_for('manage_users'))

    # Pour le formulaire de modification, on doit lister tous les employés non liés,
    # PLUS l'employé actuellement lié à cet utilisateur (s'il y en a un).
    linked_employee_ids = [u.employee_id for u in User.query.filter(User.id != user.id, User.employee_id.isnot(None)).all()]
    available_employees = Employee.query.filter(Employee.id.notin_(linked_employee_ids)).all()
    
    return render_template('main_template.html', view='user_edit_form', user=user, available_employees=available_employees)

@app.route('/user/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required(['CEO'])
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.role == 'CEO':
        flash("Vous ne pouvez pas supprimer le compte CEO.", "danger")
        return redirect(url_for('manage_users'))
    db.session.delete(user_to_delete)
    db.session.commit()
    flash("Utilisateur supprimé.", "success")
    return redirect(url_for('manage_users'))



@app.route('/hebergements')
@login_required
@role_required(['CEO', 'RH'])
def list_hebergements():
    hebergements = Hebergement.query.order_by(Hebergement.start_date.desc()).all()
    return render_template('main_template.html', view='hebergements_list', hebergements=hebergements)

@app.route('/hebergement/add', methods=['GET', 'POST'])
@login_required
@role_required(['CEO', 'RH'])
def add_hebergement():
    if request.method == 'POST':
        # On crée d'abord l'objet hébergement
        new_hebergement = Hebergement(
            address=request.form.get('address'),
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form['end_date'] else None,
            cost=float(request.form.get('cost')) if request.form.get('cost') else None,
            notes=request.form.get('notes')
        )

        # On récupère la liste des IDs d'employés sélectionnés
        employee_ids = request.form.getlist('employee_ids')
        if employee_ids:
            # On trouve les objets Employé correspondants
            selected_employees = Employee.query.filter(Employee.id.in_(employee_ids)).all()
            # On les assigne à l'hébergement
            new_hebergement.employees = selected_employees
        
        db.session.add(new_hebergement)
        db.session.commit()
        flash("Hébergement ajouté avec succès.", "success")
        return redirect(url_for('list_hebergements'))

    employees = Employee.query.all()
    return render_template('main_template.html', view='hebergement_form', form_title="Ajouter un Hébergement", employees=employees)
@app.route('/chantier/add', methods=['GET', 'POST'])
@login_required
@role_required(['CEO', 'Chef de projet'])
def add_chantier():
    if request.method == 'POST':
        new_chantier = Chantier(
            name=request.form.get('name'),
            client_id=request.form.get('client_id'),
            status=request.form.get('status'),
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form['start_date'] else None,
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form['end_date'] else None
        )
        db.session.add(new_chantier)
        db.session.commit()
        flash('Nouveau chantier créé avec succès.', 'success')
        return redirect(url_for('list_chantiers'))

    clients = Client.query.all()
    return render_template('main_template.html', view='chantier_form', form_title="Créer un Chantier", clients=clients)
@app.route('/employee/add', methods=['GET', 'POST'])
@login_required
@role_required(['CEO', 'RH'])
def add_employee():
    if request.method == 'POST':
        hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date() if request.form['hire_date'] else datetime.utcnow().date()
        salary = float(request.form['salary']) if request.form['salary'] else None
        
        new_employee = Employee(
            full_name=request.form['full_name'],
            position=request.form['position'],
            email=request.form['email'],
            phone=request.form['phone'],
            hire_date=hire_date,
            salary=salary
        )
        db.session.add(new_employee)
        db.session.commit()
        flash('Employé ajouté avec succès !', 'success')
        return redirect(url_for('list_employees'))
        
    return render_template('main_template.html', view='employee_form', form_title="Ajouter un Employé", employee=None)
@app.route('/equipment/category/<category_name>')
@login_required
def list_equipment_by_category(category_name):
    if current_user.role == 'Finance':
        abort(403)
    if category_name not in ['Vehicules', 'Engins', 'Materiels']:
        abort(404)
    equipment_list = Equipment.query.filter_by(category=category_name).order_by(Equipment.name).all()
    return render_template('main_template.html', 
                           view='equipment_list', 
                           equipment=equipment_list, 
                           category_title=category_name)
  
@app.route('/employee/edit/<int:employee_id>', methods=['GET', 'POST'])
@login_required
@role_required(['CEO', 'RH'])
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    if request.method == 'POST':
        employee.full_name = request.form['full_name']
        employee.position = request.form['position']
        employee.email = request.form['email']
        employee.phone = request.form['phone']
        employee.hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date() if request.form['hire_date'] else employee.hire_date
        employee.salary = float(request.form['salary']) if request.form['salary'] else employee.salary
        
        db.session.commit()
        flash('Les informations de l\'employé ont été mises à jour !', 'success')
        return redirect(url_for('list_employees'))
        
    return render_template('main_template.html', view='employee_form', form_title="Modifier l'Employé", employee=employee)

@app.route('/chantier/<int:chantier_id>')
@login_required
@role_required(['CEO', 'Chef de projet'])
def chantier_profile(chantier_id):
    chantier = Chantier.query.get_or_404(chantier_id)
    return render_template('main_template.html', view='chantier_profile', chantier=chantier)

@app.route('/chantier/<int:chantier_id>/add_document', methods=['POST'])
@login_required
@role_required(['CEO', 'Chef de projet'])
def add_document_to_chantier(chantier_id):
    chantier = Chantier.query.get_or_404(chantier_id)
    doc_name = request.form.get('doc_name')
    doc_url = request.form.get('doc_url')

    if not doc_name or not doc_url:
        flash("Le nom et le lien du document sont requis.", 'danger')
    else:
        new_document = Document(
            name=doc_name,
            url=doc_url,
            chantier_id=chantier.id,
            owner=current_user 
        )
        db.session.add(new_document)
        db.session.commit()
        flash('Document lié au chantier avec succès.', 'success')

    return redirect(url_for('chantier_profile', chantier_id=chantier_id))

# --- VOS ROUTES DE GESTION DES CONGÉS CORRIGÉES ---

@app.route('/link-user-employee')
@login_required
@role_required(['CEO']) # Sécurité : Seul le CEO peut visiter cette page
def link_user_employee():
    """
    Route temporaire pour lier un utilisateur à un employé.
    À supprimer après utilisation.
    """
    # --- MODIFIEZ CES VALEURS ---
    username_to_link = 'employe'
    employee_full_name = 'Nom Complet de l\'Employé' # <-- Mettez le nom exact de l'employé ici
    # ---------------------------

    user = User.query.filter_by(username=username_to_link).first()
    employee = Employee.query.filter_by(full_name=employee_full_name).first()

    if not user:
        flash(f"Utilisateur '{username_to_link}' non trouvé.", 'danger')
        return redirect(url_for('dashboard'))
    
    if not employee:
        flash(f"Employé '{employee_full_name}' non trouvé.", 'danger')
        return redirect(url_for('dashboard'))

    # On fait la liaison
    user.employee_id = employee.id
    db.session.commit()

    flash(f"L'utilisateur '{user.username}' a été lié avec succès à l'employé '{employee.full_name}'.", 'success')
    return redirect(url_for('dashboard'))

@app.route('/leaves')
@login_required
@role_required(['CEO', 'RH'])
def list_leaves():
    """Affiche toutes les demandes de congé (pour les admins/CEO)."""
    # CHANGÉ: LeaveRequest -> Request
    leaves = Request.query.order_by(Request.start_date.desc()).all()
    return render_template('main_template.html', view='leaves_list', leaves=leaves)

@app.route('/my_leaves')
@login_required
def my_leaves():
    """Affiche les congés de l'employé actuellement connecté."""
    
    # Vérifie que le compte utilisateur est bien lié à un profil employé
    if not current_user.employee:
        flash("Votre compte utilisateur n'est pas lié à un profil employé.", "danger")
        return redirect(url_for('dashboard'))
    
    # Récupère les congés UNIQUEMENT pour cet employé
    leaves = Request.query.filter_by(employee_id=current_user.employee.id).order_by(Request.start_date.desc()).all()
    
    # Affiche la page avec la liste de ses congés
    return render_template('main_template.html', view='employee_leaves', leaves=leaves)
@app.route('/leaves/request', methods=['GET', 'POST'])
@login_required
def request_leave():
    """Gère la création d'une demande de congé."""
    if request.method == 'POST':
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()

        if start_date > end_date:
            flash('❌ La date de début ne peut pas être après la date de fin.', 'danger')
            return redirect(url_for('request_leave'))

        employee_id_to_request = request.form.get('employee_id')
        if not employee_id_to_request and current_user.employee:
            employee_id_to_request = current_user.employee.id
        
        if not employee_id_to_request:
            flash("❌ Impossible d'identifier l'employé pour cette demande.", "danger")
            return redirect(url_for('dashboard'))

        # DEBUG
        print("Employee ID:", employee_id_to_request)

        # Création de la demande
        new_request = Request(
            employee_id=employee_id_to_request,
            _type=request.form['leave_type'],
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(new_request)
        db.session.commit()

        # ✅ Message confirmation
        flash('✅ Votre demande de congé a été envoyée et est en attente de validation par le service RH.', 'success')

        # ✅ Rester sur la page formulaire au lieu d’une redirection vers une page interdite
        employees = Employee.query.filter_by(is_active=True).all()
        return render_template(
            'main_template.html',
            view='leave_request_form',
            employees=employees,
            form_title="Demander un Congé"
        )

    # GET → Afficher formulaire
    employees = Employee.query.filter_by(is_active=True).all()
    return render_template('main_template.html', view='leave_request_form', employees=employees, form_title="Demander un Congé")


@app.route('/leaves/<int:leave_id>/update_status', methods=['POST'])
@login_required
@role_required(['CEO', 'RH'])
def update_leave_status(leave_id):
    """Met à jour le statut d'une demande (Approuvé/Rejeté)."""
    # CHANGÉ: LeaveRequest -> Request
    leave = Request.query.get_or_404(leave_id)
    new_status = request.form.get('status')

    if new_status not in ['Approved', 'Rejected']:
        flash('Statut invalide.', 'danger')
        return redirect(url_for('list_leaves'))

    leave.status = new_status
    db.session.commit()
    flash(f'La demande de congé a été {new_status.lower()}.', 'success')
    return redirect(url_for('list_leaves'))

@app.route('/leaves/propose/<int:leave_id>', methods=['GET', 'POST'])
@login_required
@role_required(['CEO', 'RH'])
def propose_new_dates(leave_id):
    leave = Request.query.get_or_404(leave_id)

    if request.method == 'POST':
        new_start = datetime.strptime(request.form['new_start_date'], '%Y-%m-%d').date()
        new_end = datetime.strptime(request.form['new_end_date'], '%Y-%m-%d').date()

        if new_start > new_end:
            flash('La date de début ne peut pas être après la date de fin.', 'danger')
            return redirect(url_for('propose_new_dates', leave_id=leave_id))

        # Met à jour les champs de proposition
        leave.proposed_start_date = new_start
        leave.proposed_end_date = new_end
        # Le statut reste 'Pending' pour que l'employé puisse répondre
        db.session.commit()

        flash("Nouvelles dates proposées. En attente de la réponse de l'employé.", 'success')
        return redirect(url_for('list_leaves'))

    return render_template('main_template.html', view='propose_new_dates', leave=leave, form_title="Proposer de nouvelles dates")

# Assurez-vous que cette fonction est bien dans votre app.py
@app.route('/equipment/add/<category_name>', methods=['GET', 'POST'])
@login_required
def add_equipment(category_name):
    if current_user.role == 'Finance':
        abort(403)
    if category_name not in ['Vehicules', 'Engins', 'Materiels']:
        abort(404)

    if request.method == 'POST':
        # ... (toute votre logique de sauvegarde reste la même) ...
        category = request.form.get('category')
        name = request.form.get('name')
        status = request.form.get('status')
        notes = request.form.get('notes')
        new_equip = Equipment(category=category, name=name, status=status, notes=notes)
        if category == 'Vehicules':
            new_equip.immatriculation = request.form.get('immatriculation')
            responsable_id = request.form.get('responsable_id')
            if responsable_id: new_equip.responsable_id = int(responsable_id)
            if request.form.get('date_debut_responsabilite'): new_equip.date_debut_responsabilite = datetime.strptime(request.form['date_debut_responsabilite'], '%Y-%m-%d').date()
            if request.form.get('date_fin_responsabilite'): new_equip.date_fin_responsabilite = datetime.strptime(request.form['date_fin_responsabilite'], '%Y-%m-%d').date()
        elif category == 'Engins':
            new_equip.type_engin = request.form.get('type_engin')
            if request.form.get('hauteur'): new_equip.hauteur = float(request.form.get('hauteur'))
            if request.form.get('date_vgp'): new_equip.date_vgp = datetime.strptime(request.form['date_vgp'], '%Y-%m-%d').date()
            if request.form.get('nombre_cles'): new_equip.nombre_cles = int(request.form.get('nombre_cles'))
            new_equip.photo_fuel_url = request.form.get('photo_fuel_url')
        elif category == 'Materiels':
            new_equip.serial_number = request.form.get('serial_number')
            new_equip.type_materiel = request.form.get('type_materiel')
            new_equip.etat = request.form.get('etat')
        
        db.session.add(new_equip)
        db.session.commit()
        flash(f'{category.rstrip("s")} ajouté avec succès.', 'success')
        return redirect(url_for('list_equipment_by_category', category_name=new_equip.category))
    
    employees = Employee.query.order_by(Employee.full_name).all()
    # Cette ligne est la clé : on envoie la catégorie au template
    return render_template('main_template.html', 
                           view='equipment_form', 
                           form_title=f"Ajouter : {category_name.rstrip('s')}", 
                           employees=employees,
                           preselected_category=category_name)

@app.route('/equipment/edit/<int:equipment_id>', methods=['GET', 'POST'])
@login_required
def edit_equipment(equipment_id):
    # ... (la logique de modification reste la même)
    if current_user.role == 'Finance':
        abort(403)
    equip = Equipment.query.get_or_404(equipment_id)
    if request.method == 'POST':
        equip.category = request.form.get('category')
        equip.name = request.form.get('name')
        equip.status = request.form.get('status')
        equip.notes = request.form.get('notes')
        if equip.category == 'Vehicules':
            equip.immatriculation = request.form.get('immatriculation')
            responsable_id = request.form.get('responsable_id')
            equip.responsable_id = int(responsable_id) if responsable_id else None
            equip.date_debut_responsabilite = datetime.strptime(request.form['date_debut_responsabilite'], '%Y-%m-%d').date() if request.form.get('date_debut_responsabilite') else None
            equip.date_fin_responsabilite = datetime.strptime(request.form['date_fin_responsabilite'], '%Y-%m-%d').date() if request.form.get('date_fin_responsabilite') else None
        elif equip.category == 'Engins':
            equip.type_engin = request.form.get('type_engin')
            hauteur = request.form.get('hauteur')
            equip.hauteur = float(hauteur) if hauteur else None
            equip.date_vgp = datetime.strptime(request.form['date_vgp'], '%Y-%m-%d').date() if request.form.get('date_vgp') else None
            nombre_cles = request.form.get('nombre_cles')
            equip.nombre_cles = int(nombre_cles) if nombre_cles else None
            equip.photo_fuel_url = request.form.get('photo_fuel_url')
        elif equip.category == 'Materiels':
            equip.serial_number = request.form.get('serial_number')
            equip.type_materiel = request.form.get('type_materiel')
            equip.etat = request.form.get('etat')
        db.session.commit()
        flash('Équipement mis à jour.', 'success')
        return redirect(url_for('list_equipment_by_category', category_name=equip.category))
    employees = Employee.query.order_by(Employee.full_name).all()
    return render_template('main_template.html', view='equipment_form', form_title="Modifier l'Équipement", equipment=equip, employees=employees)


@app.route('/leaves/respond/<int:leave_id>', methods=['POST'])
@login_required
def respond_proposal(leave_id):
    """Permet à un employé de répondre à une contre-proposition de dates."""
    leave = Request.query.get_or_404(leave_id)
    if not current_user.employee or leave.employee_id != current_user.employee.id:
        flash("Action non autorisée.", "danger")
        return redirect(url_for('dashboard'))

    response = request.form['response']
    if response == 'accept' and leave.proposed_start_date:
        # On met à jour les dates avec celles de la proposition
        leave.start_date = leave.proposed_start_date
        leave.end_date = leave.proposed_end_date
        
        # ✅ CHANGEMENT PRINCIPAL : Le statut passe directement à "Approuvé"
        leave.status = 'Approved'
        
        # On nettoie les champs de proposition car elle est maintenant acceptée
        leave.proposed_start_date = None
        leave.proposed_end_date = None
        
        # ✅ On met à jour le message de confirmation
        flash("Vous avez accepté la proposition. Votre congé est maintenant approuvé.", "success")
    
    elif response == 'decline':
        # Si l'employé refuse, on efface juste la proposition
        leave.proposed_start_date = None
        leave.proposed_end_date = None
        flash("Vous avez refusé la contre-proposition.", "info")
    
    db.session.commit()
    return redirect(url_for('my_leaves'))

"""
# --- DATABASE AND APP INITIALIZATION ---
# This code now runs automatically when the app starts
with app.app_context():
    print("--- Initialisation de la base de données... ---")
    db.create_all()
    default_users = {
        'ceo': {'password': 'password', 'role': 'CEO'},
        'rh': {'password': 'password', 'role': 'RH'},
        'finance': {'password': 'password', 'role': 'Finance'},
        'chef': {'password': 'password', 'role': 'Chef de projet'},
        'employe': {'password': 'password', 'role': 'Employé'}
    }
    for username, details in default_users.items():
        if not User.query.filter_by(username=username).first():
            hashed_password = bcrypt.generate_password_hash(details['password']).decode('utf-8')
            db.session.add(User(username=username, password_hash=hashed_password, role=details['role']))
    db.session.commit()
    print("--- Base de données prête. ---")
"""
# This block only runs for local development
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)

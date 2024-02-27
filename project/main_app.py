import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, UserMixin, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from sqlalchemy import desc
from werkzeug.datastructures import CombinedMultiDict, MultiDict, ImmutableMultiDict
import json
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import plot as pt

app = Flask(__name__)
app.secret_key = 'I think this key needs to be rather long for it to be secure (from java security reading)'
#app.config["SECRET_KEY"] = "a secret key you won't forget"
#app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)
ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
# --- DATABASE ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.app_context().push()
login_manager = LoginManager()
login_manager.init_app(app)

# email sending setting
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = '1823075630@qq.com'
app.config['MAIL_PASSWORD'] = 'qiqfnymarjtsebfd'
app.config['MAIL_USE_TLS'] = True
mail = Mail(app)

class UserAccount(UserMixin, db.Model):
    __tablename__ = "user_account"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True,  nullable=False)
    # Adjust the length if needed
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(70), unique=True, nullable=False)
    email_active = db.Column(db.Boolean, default=False, nullable=False)
    is_reset_password = db.Column(db.Boolean, default=False, nullable=False)

    api_keys = db.relationship(
        "UserAPIKey", back_populates="user", lazy='dynamic')

    def __repr__(self):
        return f'UserAccount(id={self.id}, username="{self.username}")'


class UserAPIKey(db.Model):
    __tablename__ = "api_keys"
    id = db.Column(db.Integer, primary_key=True)
    API_KEY_COMPANY = db.Column(db.String(30), nullable=False, default="other")
    API_KEY_VALUE = db.Column(db.String(150), nullable=False)
    API_KEY_PASSWORD = db.Column(
        db.String(40), nullable=False, default="other")

    user_id = db.Column(db.Integer, db.ForeignKey("user_account.id"))
    user = db.relationship("UserAccount", back_populates="api_keys")

    def __repr__(self):
        return f'UserAPIKey(id={self.id}, user_id="{self.user_id}")'


# After the model definitions, you can create tables and add a test user like this:
# db.drop_all()
# db.create_all()

import logging

def add_test_user():
    try:
        # Check if the user already exists
        test_user = UserAccount.query.filter_by(username='testuser3333').first()
        if not test_user:
            # User doesn't exist, so create one
            hashed_password = generate_password_hash('testpassword3333', method='pbkdf2:sha256')
            new_user = UserAccount(
                username='testuser3333',  # Make sure this matches the username checked above
                password=hashed_password,
                email='test@example.com',
                email_active=True
            )
            db.session.add(new_user)
            db.session.commit()

            # After committing, check if the user has an id
            if new_user.id:
                logging.info(f'User {new_user.username} was added successfully with ID {new_user.id}.')
                return True
            else:
                logging.error('Failed to add user, no ID has been set after commit.')
                return False
        else:
            logging.info('User testuser3333 already exists.')
            return False
    except SQLAlchemyError as e:
        logging.error(f'An error occurred while adding the user: {e}')
        db.session.rollback()
        return False

# load user
@login_manager.user_loader
def load_user(user_id):
    return UserAccount.query.get(user_id)

# Main page
@app.route('/')
def index():
    return render_template('index.html')

# Account setup page
@app.route('/setup/<username>', methods=['GET', 'POST'])
def Setup(username):
    if request.method == 'POST':

        # figure out maintanance loan and accomodation cost
        maintanance_loan = request.form.get('loan')
        if maintanance_loan == '':
            loanlevel = request.form['rad']
            homestatus = request.form['rad2']

            # if rad & rad2 not set as well:
            if loanlevel == '' and homestatus == '':
                flash(
                    'Your are not enter your maintanance loan or choose your loan level!')
                return redirect(url_for('Setup', username=username))

            if loanlevel == "min":
                if homestatus == "home":
                    maintanance_loan = 3410
                elif homestatus == "nolnd":
                    maintanance_loan = 4289
                else:
                    maintanance_loan = 5981
            elif loanlevel == "mid":
                if homestatus == "home":
                    maintanance_loan = (3410+7747)/2
                elif homestatus == "nolnd":
                    maintanance_loan = (4289+9203)/2
                else:
                    maintanance_loan = (5981+12010)/2
            elif loanlevel == "max":
                if homestatus == "home":
                    maintanance_loan = 7747
                elif homestatus == "nolnd":
                    maintanance_loan = 9203
                else:
                    maintanance_loan = 12010
            else:
                maintanance_loan = 0
        else:
            maintanance_loan = float(maintanance_loan)

        accomodation_cost = request.form.get('acost')
        if accomodation_cost == '':
            fallowfield_accomodation = [
                5975, 4394, 6328, 6174, 6185, 6693, 6338]
            optionaccom = request.form.get('optionaccom')
            accomodation_cost = fallowfield_accomodation[int(optionaccom)-1]
        else:
            accomodation_cost = float(accomodation_cost)

        # calculate budget based off of loan and cost
        year_budget = maintanance_loan - accomodation_cost
        one_month = year_budget/9
        # september and june are half months
        month_budget_list = str(one_month/2)+" " + \
            ((str(one_month)+" ")*8)+str(one_month/2)
        week_budget_list = (str(year_budget/40) + " ")*40

        date_maint1 = datetime.strptime(
            request.form.get('mtdate1'), '%d/%m/%Y')
        date_maint2 = datetime.strptime(
            request.form.get('mtdate2'), '%d/%m/%Y')
        date_maint3 = datetime.strptime(
            request.form.get('mtdate3'), '%d/%m/%Y')
        date_accom1 = datetime.strptime(
            request.form.get('acdate1'), '%d/%m/%Y')
        date_accom2 = datetime.strptime(
            request.form.get('acdate2'), '%d/%m/%Y')
        date_accom3 = datetime.strptime(
            request.form.get('acdate3'), '%d/%m/%Y')

        # get the user record via the passed username
        user = UserAccount.query.filter_by(username=username).first()
        user.setup_budget = True
        user_id = user.id

        new_budget = UserBudget(maintanance_loan=maintanance_loan, accomodation_cost=accomodation_cost,
                                year_budget=year_budget, month_budget_list=month_budget_list,
                                month_remaining_list=month_budget_list, week_budget_list=week_budget_list,
                                week_remaining_list=week_budget_list,
                                date_maint1=date_maint1, date_maint2=date_maint2, date_maint3=date_maint3,
                                date_accom1=date_accom1, date_accom2=date_accom2, date_accom3=date_accom3,
                                account_id=user_id)

        db.session.add(new_budget)
        db.session.commit()

        return redirect(url_for('Daily', username=username))

    return render_template('setup.html', username=username)


@app.route('/setup/<username>/edit', methods=['GET', 'POST'])
def Setup_edit(username):
    # get the user record via the passed username
    user = UserAccount.query.filter_by(username=username).first()
    b = user.budget

    if request.method == 'POST':

        # figure out maintanance loan and accomodation cost
        maintanance_loan = request.form.get('loan')
        if maintanance_loan == '':
            loanlevel = request.form['rad']
            homestatus = request.form['rad2']

            if loanlevel == "min":
                if homestatus == "home":
                    maintanance_loan = 3410
                elif homestatus == "nolnd":
                    maintanance_loan = 4289
                else:
                    maintanance_loan = 5981
            elif loanlevel == "mid":
                if homestatus == "home":
                    maintanance_loan = (3410+7747)/2
                elif homestatus == "nolnd":
                    maintanance_loan = (4289+9203)/2
                else:
                    maintanance_loan = (5981+12010)/2
            elif loanlevel == "max":
                if homestatus == "home":
                    maintanance_loan = 7747
                elif homestatus == "nolnd":
                    maintanance_loan = 9203
                else:
                    maintanance_loan = 12010
            else:
                maintanance_loan = 0
        else:
            maintanance_loan = float(maintanance_loan)

        accomodation_cost = request.form.get('acost')
        if accomodation_cost == '':
            fallowfield_accomodation = [
                5975, 4394, 6328, 6174, 6185, 6693, 6338]
            optionaccom = request.form.get('optionaccom')
            accomodation_cost = fallowfield_accomodation[int(optionaccom)-1]
        else:
            accomodation_cost = float(accomodation_cost)

        # calculate budget based off of loan and cost
        year_budget = maintanance_loan - accomodation_cost
        one_month = year_budget/9
        # september and june are half months
        month_budget_list = str(one_month/2)+" " + \
            ((str(one_month)+" ")*8)+str(one_month/2)
        week_budget_list = (str(year_budget/40) + " ")*40

        date_maint1 = datetime.strptime(
            request.form.get('mtdate1'), '%d/%m/%Y')
        date_maint2 = datetime.strptime(
            request.form.get('mtdate2'), '%d/%m/%Y')
        date_maint3 = datetime.strptime(
            request.form.get('mtdate3'), '%d/%m/%Y')
        date_accom1 = datetime.strptime(
            request.form.get('acdate1'), '%d/%m/%Y')
        date_accom2 = datetime.strptime(
            request.form.get('acdate2'), '%d/%m/%Y')
        date_accom3 = datetime.strptime(
            request.form.get('acdate3'), '%d/%m/%Y')

        b.maintanance_loan = maintanance_loan
        b.accomodation_cost = accomodation_cost
        b.year_budget = year_budget
        b.month_budget_list = month_budget_list
        b.month_remaining_list = month_budget_list
        b.week_budget_list = week_budget_list
        b.week_remaining_list = week_budget_list
        b.date_maint1 = date_maint1
        b.date_maint2 = date_maint2
        b.date_maint3 = date_maint3
        b.date_accom1 = date_accom1
        b.date_accom2 = date_accom2
        b.date_accom3 = date_accom3

        db.session.commit()

        return redirect(url_for('Daily', username=username))

    return render_template('setup_edit.html', budget=b, username=username)

########################################################################################


# - Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('uname')
        password = request.form.get('password')
        password = generate_password_hash(password)  # hashing password

        '''# if no such user, create a new useraccount:'''
        checkU = UserAccount.query.filter_by(username=username).first()
        checkE = UserAccount.query.filter_by(email=email).first()
        if checkU is None and checkE is None:
            user = UserAccount(username=username, email=email,
                               password=password)

            db.session.add(user)
            db.session.commit()

            emptyUser = UserAccount.query.filter_by(username='').first()
            if emptyUser is None:

                user = UserAccount(username=username, email=email,
                                   password=password)

                # validate email -- generate email token
                token = ts.dumps(user.email, salt='email-confirm-key')
                print(token)
                #send_email(user.email,'Please confirm your account','auth/email/confirm',user,token)
                send_email(user.email, 'Please confirm your account',
                           '/confirm/', user, token)
                flash('Validation email has been sent!')
                return redirect(url_for('login'))

                # return render_template('login.html')
            else:
                '''empty exist --- need to change'''
                #msg = "existing empty"
                # print(msg)
                db.session.delete(emptyUser)
                db.session.commit()
                #isUser = False
                flash("Input username is empty")
                return render_template('register.html')
        else:
            '''# already exist  --- wrong  *need to modify'''
            #isUser = False
            flash("User already exists, Please change to another username", 'warning')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/confirm/<token>')
# @login_required
def confirm(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
        print('email_token', email)
        user = UserAccount.query.filter_by(email=email).first_or_404()
        print('email-- user', user)
        user.email_confirmed = True
        user.email_active = True
        # db.session.add(user)
        db.session.commit()
        flash("email activated")
        return redirect(url_for('login'))
    except:
        print("error", token)

    return redirect(url_for('login'))


# submit reset form
@app.route('/password_reset_success/', methods=['GET', 'POST'])
def password_reset_success():
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('password')
        password = generate_password_hash(password)  # hashing password

        checkU = UserAccount.query.filter_by(username=username).first()
        if checkU is not None and checkU.is_reset_password == 1:
            checkU.password = password
            checkU.is_reset_password = 0
            db.session.commit()
            flash("Reset was successful")
            return render_template('reset_pwd2.html')
        else:
            flash("Username is incorrect or has already been reset")
            return render_template('reset_pwd2.html')
    return render_template('reset_pwd2.html')


# @app.before_app_request
# def before_request():
#    if current_user.is_authenticated \
#            and not current_user.confirmed \
#            and request.endpoint[:5] != 'auth.'\
#            and request.endpoint != 'static':
#        return redirect(url_for('index'))


# @app.route("/mail_send_test")
# definition to send email(register confirm && password reset)
def send_email(to, subject, template, user, token):
    #msg = Message(subject='Hello', sender='1659335946@qq.com', recipients=['xuyingyu1108@yeah.net'])
    confirm_url = url_for(
        'confirm',
        token=token,
        _external=True)
    msg = Message(subject=subject, sender='1823075630@qq.com',
                  recipients=[to], body="link here",
                  html=render_template(
                      'activate.html',
                      confirm_url=confirm_url))

    mail.send(msg)


def send_email_reset(to, subject, template, user, token):
    #msg = Message(subject='Hello', sender='1659335946@qq.com', recipients=['xuyingyu1108@yeah.net'])
    confirm_url = url_for(
        'password_reset',
        token=token,
        _external=True)
    msg = Message(subject=subject, sender='1823075630@qq.com',
                  recipients=[to], body="link here",
                  html=render_template(
                      'activate.html',
                      confirm_url=confirm_url))

    mail.send(msg)

@ app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
        return render_template("dashboard.html")


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = UserAccount.query.filter_by(username=username).first()
        if user:
            # Debug: Print out the hashes to ensure they match
            print(f"Stored hash: {user.password}")
            print(f"Provided hash: {generate_password_hash(password, method='pbkdf2:sha256')}")
            
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'warning')
        else:
            flash('No account found with that username', 'warning')
        
        return redirect(url_for('login'))
    
    return render_template("login.html")


@app.route('/list_users')
def list_users():
    users = UserAccount.query.all()
    for user in users:
        print(user.username)  # Print to the server console
    return "Check the console for a list of users."

@app.route('/account/<id>/<username>', methods=['POST', 'GET'])
def account(id, username):
    # print(username)
    user = UserAccount.query.filter_by(username=username).first_or_404()

    #app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)

    user_ca = json.loads(user.user_categories.replace('\'', '"'))
    user_cu = json.loads(user.user_currency.replace('\'', '"'))

    if request.method == 'POST':

        result = request.form
        # print(result)
        result = ImmutableMultiDict(result)
        user_currency = result.getlist("user_currency")
        user_categories = result.getlist("user_categories")

        mcost = result.getlist("mcost")
        mcost = " ".join(mcost)
        wcost = result.getlist("wcost")
        wcost = " ".join(wcost)

        mcategory = result.getlist("mcategory")
        mcategory = " ".join(mcategory)
        wcategory = result.getlist("wcategory")
        wcategory = " ".join(wcategory)

        all_budget_detail = UserBudget(
            mcost=mcost, mcategory=mcategory, wcost=wcost, wcategory=wcategory)

        db.session.add(all_budget_detail)
        print("added new budget.")

        db.session.commit()
        return redirect(url_for('account', id=user.id, username=user.username))

    else:
        user_categories = user.user_categories
        user_currency = user.user_currency

        all_mcost = UserBudget.query.all()
        all_wcost = UserBudget.query.all()

        expense_detail = UserExpenditure.query.all()

        list = []
        data = {}
        for x in expense_detail:
            if x.category not in list:
                list.append(x.category)

        for x in list:
            category_expense = UserExpenditure.query.filter_by(
                user_id=user.id).filter_by(category=x)
            sum = 0
            for i in category_expense:
                sum = sum + i.cost
            data[x] = sum

        category_data_weekly = {}
        category_average_4weeks = {}
        avg4weeks = []
        for x in list:
            category_expense = UserExpenditure.query.filter_by(
                user_id=user.id).filter_by(category=x)
            sum = 0
            category_average_4weeks[x] = 0
            for i in category_expense:
                current = datetime.now()
                if ((current - i.date).days <= 7):
                    sum = sum + i.cost
                elif (current - i.date).days <= 36:
                    category_average_4weeks[x] = category_average_4weeks[x] + i.cost
            category_data_weekly[x] = sum

        return render_template("account.html", username=username, user=user, budget=user.budget,
                               user_currency=user.user_currency, user_categories=user.user_categories,
                               user_ca=user_ca, user_cu=user_cu, mcost=all_mcost,
                               wcost=all_wcost, cost=expense_detail, data=data,
                               monthdata=category_average_4weeks, weekdata=category_data_weekly)


# set user preference in account page
@app.route('/account/preference/<id>/<username>', methods=['POST', 'GET'])
def user_prefer(id, username):
    # print(username)
    user = UserAccount.query.filter_by(username=username).first_or_404()

    #app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)

    user_ca = json.loads(user.user_categories.replace('\'', '"'))
    user_cu = json.loads(user.user_currency.replace('\'', '"'))

    full_cu_o = "['pound(￡)', 'dollar($)', 'euro(€)', 'yuan(￥)', 'yen(¥)', 'rupee(Rs)', \
                             'lira(₺)', 'won(₩)', 'rouble(₽)', 'Australia dollar(A$)', 'More']"
    full_cu = json.loads(full_cu_o.replace('\'', '"'))

    full_ca_o = "['food', 'clothes', 'entertainment', 'sports', 'socialnetwork', \
                             'dailyuse', 'communication', 'electronicdevice', 'education', 'healthcare',\
                             'transportation', 'furniture','alcohol',\
                             'shopping', 'snacks', 'travel', 'beauty', 'car', 'other']"
    full_ca = json.loads(full_ca_o.replace('\'', '"'))

    if request.method == 'POST':
        user = UserAccount.query.filter_by(username=username).first_or_404()
        result = request.form
        print(result)
        result = ImmutableMultiDict(result)
        user_currency = result.getlist("user_currency")

        user_categories = result.getlist("user_categories")

        print(result)
        # print(user_currency)
        # print(user_categories)

        user.user_currency = str(user_currency)
        user.user_categories = str(user_categories)
        db.session.commit()

        user_ca = json.loads(user.user_categories.replace('\'', '"'))
        user_cu = json.loads(user.user_currency.replace('\'', '"'))
        # print('user_ca?', user_ca)

        print("added perference.")
        return render_template("user_preference.html", username=username, user=user, budget=user.budget,
                               user_currency=user.user_currency, user_categories=user.user_categories,
                               user_ca=user_ca, user_cu=user_cu,
                               full_cu=full_cu, full_ca=full_ca)

    user_categories = user.user_categories
    user_currency = user.user_currency

    return render_template("user_preference.html", username=username, user=user, budget=user.budget,
                           user_currency=user.user_currency, user_categories=user.user_categories,
                           user_ca=user_ca, user_cu=user_cu,
                           full_cu=full_cu, full_ca=full_ca)



# - Reset password page
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form.get('uname')
        email = request.form.get('email')
        userU = UserAccount.query.filter_by(username=username).first()
        userE = UserAccount.query.filter_by(email=email).first()
        # if UserAccount.query.filter_by(email=email).first() is not None:
        if userU is not None and userE is not None:
            if userU == userE:
                userU.is_reset_password = 1
                db.session.commit()
                # validate email -- generate email token
                token = ts.dumps(email, salt='email-confirm-key')
                # print(token)
                send_email_reset(
                    userU.email, 'You are resetting your account', '/reset/', userU, token)
                flash('Validation email has been sent!')
                # return redirect(url_for('index'))
            else:
                flash('Username and email cannot match')
        else:
            flash('Username or email is not registered')

    return render_template('reset_pwd.html')


@app.route('/change/<username>', methods=['GET', 'POST'])
def changepassword(username):
    if request.method == 'POST':
        current_pass = request.form.get('oldpass')
        pass1 = request.form.get('pass1')
        pass2 = request.form.get('pass2')

        user = UserAccount.query.filter_by(username=username).first()

        if pass1 != pass2:
            flash("Password does not match")
            return render_template('change.html')

        if check_password_hash(user.password, current_pass):
            user.password = generate_password_hash(pass1)
            db.session.commit()
            flash("Password updated successfully")
            return redirect(url_for('Daily', username=user.username))

    return render_template('change.html')


# reset password by accessing link sended to registered email
@app.route('/reset/<token>')
def password_reset(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
        #print('email_token', email)
        user = UserAccount.query.filter_by(email=email).first_or_404()
        if UserAccount.query.filter_by(email=email).first() is not None:
            #print('email-- user -- reset', user)
            flash("Email sent! Enter the new password.")
        # return redirect(url_for('reset_password'))
        return render_template('reset_pwd2.html')

    except:
        print("error", token)
        # abort(404)

    return render_template('reset_pwd2.html')


# - Logout page
@app.route("/logout")
def logout():
    logout_user()
    return redirect('/')


# Graphs and insights page
@ app.route('/insights/<username>', methods=['GET', 'POST'])
def Insights(username):
    user = UserAccount.query.filter_by(username=username).first_or_404()
    user_expenditure = UserExpenditure.query.filter_by(
        user_id=user.id)
    user_expenditure_all = UserExpenditure.query.filter_by(
        user_id=user.id).order_by(UserExpenditure.date.desc()).all()

    list_categories = []
    category_data = {'Category': 'Expenditure'}

    for x in user_expenditure_all:
        if x.category not in list_categories:
            list_categories.append(x.category)

    for x in list_categories:
        category_expense = UserExpenditure.query.filter_by(
            user_id=user.id).filter_by(category=x)
        sum = 0
        for i in category_expense:
            sum = sum + i.cost
        category_data[x] = sum


    return render_template('insights.html', username=username, budget=user.budget, data=category_data, weekly_category=category_data_weekly, avg=category_average_4weeks,
                           empty_week=empty_week)



@ app.route('/qna', methods=['GET', 'POST'])
def QnA():
    whichOption = True
    msg = "This is page where u can ask us."
    return render_template('support.html', msg=msg, whichOption=whichOption)


@ app.route('/privacy', methods=['POST', 'GET'])
def Privacy():
    whichOption = False
    msg = "This is page with privacy policy infomation."
    return render_template('support.html', msg=msg, whichOption=whichOption)

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=8080, debug=True)
    add_test_user()  # This adds the hardcoded user

def print_all_user_accounts():
    try:
        # Retrieve all user accounts
        all_users = UserAccount.query.all()
        for user in all_users:
            print(user)
            print("nothing")  # This will call the __repr__ method of the UserAccount model
    except Exception as e:
        print(f'An error occurred: {e}')

print_all_user_accounts()



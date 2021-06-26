from datetime import datetime
from flask import render_template, flash, redirect, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, EventsForm
from app.models import User, Events
from werkzeug.urls import url_parse

@app.route('/')
@app.route('/general')
def general():
    if current_user.is_authenticated:
        user = User.query.filter_by(username=current_user.username).first_or_404()
        return render_template('general.html', title='Sport web-site', user=user)
    return render_template('general.html', title = 'Sport web-site')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('general'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = 'general'
        return redirect(url_for(next_page))
        #return redirect('/general') #переход в профиль?
    return render_template('login.html', title='Sign In', form=form)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('general'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/logout') #на странице профиля (html добавить)?
def logout():
    logout_user()
    return redirect(url_for('general'))

@app.route('/user/<username>', methods=['GET', 'POST']) #profile есть
@login_required
def profile(username):
    events = [
        {
            'author': {'username': 'John'},
            'body': 'Who`s want to play football today at 17:40?'
        },
        {
            'author': {'username': 'Valera'},
            'body': "Who's going for a run with me at 12:00?"
        }
    ]
    user = User.query.filter_by(username=username).first_or_404()
    form = EventsForm()
    if form.validate_on_submit():
        event = Events(body=form.event.data, user_id = current_user.id)
        events.append({'author' : {'username' : username}, 'body' : form.event.data})
        db.session.add(event)
        db.session.commit()
        flash('You suggested an event!')
        return redirect(url_for('profile', username=username))

    return render_template('profile.html', user = user, events = events, form = form)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/edit_profile', methods = ['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = username).first()
        if user is None:
            flash('User {} not found'.format(username))
            return redirect(url_for('general'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('profile', username = username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('profile', username = username))
    else:
        return redirect(url_for('general'))

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found'.format(username))
            return redirect(url_for('general'))
        if user == current_user:
            flash('You cannot unfollow yourself')
            return redirect(url_for('profile', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}'.format(username))
        return redirect(url_for('profile', username=username))
    else:
        return redirect(url_for('general'))

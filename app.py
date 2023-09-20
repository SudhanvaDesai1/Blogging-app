from flask import Flask, render_template, request, session, redirect, flash, url_for
from flask_login import LoginManager,UserMixin, current_user
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func



with open("config.json", "r") as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = params["secret_key"]
app.config["SQLALCHEMY_DATABASE_URI"] = params["local_uri"]
db = SQLAlchemy(app)

#-------------------- LOGIN MANAGER FROM FLASK LOGIN --------------------------

login_manager = LoginManager()
login_manager.login_view = "userlogin"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return Users.query.get(int(id))



#========================== DATABASE MODELS ==================================

#========================= CONTACT DETAILS OF THE CLIENTS =====================
class Contacts(db.Model):
    sno = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    phone_num = db.Column(db.String(15), nullable=False)
    message = db.Column(db.String(50), nullable=False)

#==================== POSTS OF THE USER OR ADMIN ===========================
class Posts(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    tagline = db.Column(db.String(30), nullable=False)
    slug = db.Column(db.String(30), unique=True, nullable=False)
    content = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(20), nullable=True)
    author = db.Column(db.Integer(),db.ForeignKey('users.id',ondelete='CASCADE'), nullable=False)
    comments = db.relationship('Comments', backref = 'posts', passive_deletes = True)
    likess = db.relationship('Likes', backref = 'users', passive_deletes = True)
# =================== COMMENT SECTION ====================================== 
class Comments(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    author_id = db.Column(db.Integer(),db.ForeignKey('users.id',ondelete='CASCADE'), nullable=False)
    post_id = db.Column(db.Integer(),db.ForeignKey('posts.id',ondelete='CASCADE'), nullable=False)

# ======================USER LIKES MODEL ======================================
class Likes(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    author_id = db.Column(db.Integer(),db.ForeignKey('users.id',ondelete='CASCADE'), nullable=False)
    post_id = db.Column(db.Integer(),db.ForeignKey('posts.id',ondelete='CASCADE'), nullable=False)
    
# ==================== USER DETAILS RELATION IN DATABASE ======================
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(30), unique = True, nullable = False)
    email = db.Column(db.String(30), unique = True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    postss = db.relationship('Posts', backref = 'users', passive_deletes = True)
    comments = db.relationship('Comments', backref = 'users', passive_deletes = True)
    likess = db.relationship('Likes', backref = 'posts', passive_deletes = True)

#-------------------------- DATABASE DESIGN ENDS HERE --------------------------

#========================== URL ROUTES =========================================
#============================= FOR HOME PAGE ===================================
@app.route("/")
@login_required
def home():
    userss = Users.query.filter_by().all()

    # username = Users.query.filter_by(user.username).first
    posts = Posts.query.filter_by().all()
    return render_template("index1.html", posts=posts, params=params, users = userss, user = current_user)

#=========================== FOR SIGNUP PAGE ===================================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email_id = request.form.get("email-id")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        email_exists = Users.query.filter_by(email=email_id).first()
        username_exists = Users.query.filter_by(username = username).first()

        if email_exists:
            flash("Email already in use.", category="error")
        elif username_exists:
            flash("Username already exists.. ", category='error')
        elif password1 != password2:
            flash("Passwords doesn't match. try again",category='error')
        elif len(username) < 4:
            flash("Username length must be of minimum 6 characters..",category='warning')
        elif len(password1) < 8:
            flash("Password length must be of minimum 8 characters..",category='warning')
        else:
            entry = Users(
                username=username,
                email=email_id,
                password=generate_password_hash(password1,method='sha256')
            )
            db.session.add(entry)
            db.session.commit()
            login_user(entry,remember=True)
            flash("SignedUp Successfully! Please Login",category='success')

    return render_template("signup.html", params=params)

# ================== FOR CONTACT PAGE ===================================
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")

        entry = Contacts(name=name, email=email, phone_num=phone, message=message)
        db.session.add(entry)
        db.session.commit()

    return render_template("contact.html", params=params, user=current_user)

# =====================MAIN POSTS PAGE ====================================
@app.route("/post/<string:post_slug>", methods=["GET"])
def posts(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()

    return render_template("post.html", post=post, params=params, user= current_user)
# ========================= COMMENTS =======================================
@app.route("/create-comment/<post_id>",methods=["POST"])
@login_required
def create_comment(post_id):
    text=request.form.get('text')

    if not text:
        flash("Comment can't be empty." , category="error")
    else:
        post = Posts.query.filter_by(id=post_id).first()
        comments = Comments.query.filter_by().all()
        if post:
            comment = Comments(text=text, author_id = current_user.id, post_id = post_id)
            db.session.add(comment)
            db.session.commit()
    return redirect(url_for("home"))
#==============================LIKING THE POST===========================

@app.route("/like-post/<post_id>",methods=['GET'])
@login_required
def like(post_id):
    post = Posts.query.filter_by(id=post_id)
    like = Likes.query.filter_by(author_id=current_user.id, post_id=post_id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Likes(author_id = current_user.id,post_id=post_id)
        db.session.add(like)
        db.session.commit()
    return redirect(url_for('home'))

# ====================== ABOUT PAGE =======================================
@app.route("/about")
def about():
    return render_template("about.html", params=params)

#-------------------------- ADMIN LEVEL IMPLEMENTATION ----------------------------

# ====================== USER LIST FOR ADMIN======================================== 
@app.route("/userlist")
def userlist():
    users = Users.query.all()
    return render_template("userlist.html", users=users, params=params,user = current_user)

# ========================== ADMIN DASHBOARD =================================
@app.route("/dashboard", methods=["GET", "POST"])
def admin():
    posts = Posts.query.all()

    if "user" in session and session["user"] == params["admin_user"]:
        return render_template(
            "dashboard.html", params=params, posts=posts
        )

    if request.method == "POST":
        username = request.form.get("uname")
        userpass = request.form.get("upass")
        if username == params["admin_user"] and userpass == params["admin_password"]:
            session["user"] = username
            return render_template(
                "dashboard.html", params=params, posts=posts, user=current_user
            )

    return render_template("adminlogin.html")

# ======================= ADMIN POST EDIT AND CREATE PANEL ========================
@app.route("/edit/<string:sno>", methods=["GET", "POST"])
def edit(sno):
    if "user" in session and session["user"] == params["admin_user"]:
        if request.method == "POST":
            box_title = request.form.get("title")
            tagline = request.form.get("tagline")
            slug = request.form.get("slug")
            content = request.form.get("content")
            date = datetime.now()
            if sno == "0":
                post = Posts(
                    title=box_title,
                    tagline=tagline,
                    slug=slug,
                    content=content,
                    date=date
                )
                db.session.add(post)
                db.session.commit()
        #     else:
        #         post = Posts.query.filter_by(sno=sno).first()
        #         post.title = box_title
        #         post.tagline = tagline
        #         post.slug = slug
        #         post.content = content
        #         post.date = date
        #         db.session.commit()
        #         return redirect("/edit/" + sno)
        # post = Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html", params=params, post=post, sno=sno, user=current_user)
    
# ========================= LOGS OUT THE ADMIN FROM THE SESSION =======================
@app.route("/logout")
def logout():
    session.pop("user")
    return redirect("/dashboard")

# ======================= DELETE THE USER POST FROM ADMIN PANEL =======================
@app.route("/delete/<string:sno>", methods=["GET", "POST"])
def delete(sno):
    if "user" in session and session["user"] == params["admin_user"]:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect("/dashboard")

#===================== REMOVE THE USER FROM THE ADMIN PANEL ===========================
@app.route("/deleteuser/<string:user_id>", methods=["GET", "POST"])
def deleteuser(user_id):
    if "user" in session and session["user"] == params["admin_user"]:
        user = Users.query.filter_by(id=user_id).first()
        db.session.delete(user)
        db.session.commit()
        return redirect("/userlist")

#------------------------ ADMIN LEVEL ENDS HERE -------------------------------------
#------------------------------------------------------------------------------------
#---------------------- USER LEVEL IMPLEMENTAION STARTS HERE ---------------------------

#================================== USER DASHBOARD =====================================
@app.route("/userdashboard/<string:usr_id>", methods=["GET", "POST"])
@login_required
def userdash(usr_id):

    posts = Posts.query.filter_by(author = usr_id).all()
    fname = Users.query.get(usr_id).username
    # passw = Users.query.get(usr_id).password
    
    return render_template(
            "userdashboard.html", params=params, posts=posts, username = fname, user = current_user
        )

    # if request.method == "POST":
    #     username = request.form.get("uname")
    #     userpass = request.form.get("upass")
    #     if username == fname and userpass == passw:
    #         session["user"] = fname
    #         return render_template(
    #             "userdashboard.html", params=params, posts=posts, username = fname
    #         )

    # return redirect(url_for('userlogin'))
#---------------------------------------------------------------------------------
#===============================User post create=============================
@app.route('/create-post/<string:sno>', methods = ["GET","POST"])
@login_required
def create_post(sno):
    if request.method == "POST":
        box_title = request.form.get("title")
        tagline = request.form.get("tagline")
        slug = request.form.get("slug")
        content = request.form.get("content")
        date = datetime.now()
        if sno == "0":
            post = Posts (
                title=box_title,
                tagline=tagline,
                slug=slug,
                content=content,
                date=date,
                author=current_user.id)
            db.session.add(post)
            db.session.commit()
        else:
            post = Posts.query.filter_by(sno=sno).first()
            post.title = box_title
            post.tagline = tagline
            post.slug = slug
            post.content = content
            post.date = date
            db.session.commit()
            return redirect("/create-post/" + sno)
    post = Posts.query.filter_by(sno=sno).first()
    return render_template("userpostedit.html", params=params, post=post, sno=sno, user = current_user)
#============================================================================
@app.route("/userlogin", methods = ["GET","POST"])
def userlogin():
    if request.method == "POST":
        email = request.form.get("email")
        userpass = request.form.get("password")
        user  = Users.query.filter_by(email = email).first()
        if user:
            if check_password_hash(user.password,userpass):
                flash('User logged in! ')
                login_user(user, remember=True)
                return redirect('/userdashboard/'+ str(current_user.id))
            else:
                flash("wrong Password!..",category='error')
        else:
            flash("User doesnot exist!..",category='error')

    return render_template("userlogin.html")
#--------------------------------------------------------------------------------
#==============================USER LOGOUT ========================================
@app.route("/userlogout")
@login_required
def userlogout():
    logout_user()
    return redirect("/userlogin")

#---------------------- USER LEVEL IMPLEMENTAION ENDS HERE ---------------------------







#------------------------ THE APP RUNNING METHOD --------------------------------------

if __name__ == "__main__":
    app.run(debug=True)

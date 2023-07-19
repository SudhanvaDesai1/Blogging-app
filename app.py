from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime

with open('config.json','r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = params['secret_key']
app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
db = SQLAlchemy(app)

class Contacts(db.Model):

    sno = db.Column(db.Integer(), primary_key = True)
    name = db.Column(db.String(30), nullable = False)
    email = db.Column(db.String(30), unique = True, nullable = False)
    phone_num = db.Column(db.String(15), nullable = False)
    message = db.Column(db.String(50), nullable = False)

class Posts(db.Model):

    sno = db.Column(db.Integer(), primary_key = True)
    title = db.Column(db.String(50), nullable = False)
    tagline = db.Column(db.String(30), nullable = False)
    slug = db.Column(db.String(30), unique = True, nullable = False)
    content = db.Column(db.String(50), nullable = False)
    date = db.Column(db.String(20), nullable = True)
    img_url = db.Column(db.String(20),nullable = True)





@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    return render_template("index.html", posts = posts, params=params)







@app.route("/contact", methods = ['GET','POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contacts(name=name,email=email,phone_num=phone,message=message)
        db.session.add(entry)
        db.session.commit()

    return render_template("contact.html")







@app.route("/post/<string:post_slug>", methods = ['GET'])
def posts(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()


    return render_template("post.html", post = post, params=params)






@app.route("/about")
def about():
    return render_template("about.html",params=params)







@app.route("/dashboard", methods=['GET','POST'])
def admin():
    posts = Posts.query.all()
    if 'user' in session and session['user'] == params['admin_user']:
        return render_template("dashboard.html",params=params, posts = posts)

    if request.method == "POST":
        username = request.form.get('uname')
        userpass = request.form.get('upass')
        if username == params['admin_user'] and userpass == params['admin_password']:
            session['user'] = username
            return render_template("dashboard.html", params=params, posts=posts)
        
    return render_template("login.html")




@app.route("/edit/<string:sno>", methods=["GET","POST"])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == "POST":
            box_title = request.form.get("title")
            tagline = request.form.get("tagline")
            slug = request.form.get("slug")
            content = request.form.get("content")
            img_file = request.form.get("img_file")
            date = datetime.now()
            if sno == '0':
                post = Posts(title = box_title, tagline = tagline, slug = slug, content = content,date = date, img_url = img_file)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.tagline = tagline
                post.slug = slug
                post.content = content
                post.date = date
                post.img_url = img_file
                db.session.commit()
                return redirect("/edit/"+sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html",params=params,post=post,sno=sno)



@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")



@app.route("/delete/<string:sno>", methods = ['GET','POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        return redirect("/dashboard")



if __name__ == "__main__":
    app.run(debug=True)
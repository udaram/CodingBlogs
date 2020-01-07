#allowing less secure app in gmail
#https://myaccount.google.com/lesssecureapps?pli=1

from flask import Flask,render_template,request,session,redirect,flash
import json
import math
from bson import ObjectId
#to upload file
from werkzeug import secure_filename
from datetime import datetime
from flask_mail import Mail
import os
from pymongo import MongoClient

client = MongoClient("mongodb+srv://udaram:Nq70tTcS6yz2U1We@cluster0-dpehf.mongodb.net/test?retryWrites=true&w=majority")
db = client.CodingBlogs #database name

params=db.config.find_one()

# with open('config.json','r') as cc:
#     params = json.load(cc)["params"]

app = Flask(__name__)
app.secret_key = 'my-secret-key'
app.config["UPLOAD_FOLDER"]=params['location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail'],
    MAIL_PASSWORD=params['pass']

)
mail = Mail(app)


@app.route("/")
def home():
    all_post = list(db.posts.find())
    last = math.ceil(len(all_post)/int(params["max_post"]))
    #get argument from query string URI
    page = request.args.get('page')

    if(not str(page).isnumeric()):
        page=1
    page =int(page)
    post=all_post[(page-1)*int(params["max_post"]):(page-1)*int(params["max_post"])+int(params["max_post"])]      

    #pagination logic
    if page==1:
        prev = "#"
        next = "/?page="+str(page+1)
    elif page==last:
        prev = "/?page="+str(page-1)
        next = "#"
    else:
        prev = "/?page="+str(page-1)
        next = "/?page="+str(page+1)

    return render_template('index.html',all_posts=post,next=next,prev=prev)

@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")

@app.route("/uploader",methods = ['GET','POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_username']:
        if request.method=='POST':
            f = request.files['file1']
            #f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            f.save(os.path.abspath("../"+app.config['UPLOAD_FOLDER']+secure_filename(f.filename)))
            return "Uploaded Successfully"

@app.route("/dashboard",methods = ['GET','POST'])
def dashboard():
    if 'user' in session and session['user'] == params['admin_username']:
        all_posts = list(db.posts.find())
        return render_template('dashboard.html',params=params,posts=all_posts)

    if(request.method=='POST'):
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username==params['admin_username'] and userpass==params['admin_password']):
            #set the session variable
            session['user']=username
            all_posts = list(db.posts.find())
            return render_template('dashboard.html',params=params,posts=all_posts)
    
    return render_template('login.html',params=params)


@app.route("/contact",methods=['GET','POST'])
def contact():
    if(request.method=='POST'):
        name=request.form.get('name')
        phone=request.form.get('phone')
        email=request.form.get('email')
        msg=request.form.get('message')
        entry = {"phone_num":phone,"email":email,"name":name,"message":msg,"date":datetime.now()}
        db.contacts.insert_one(entry)
        mail.send_message('Message from'+name,
        sender=email,
        recipients=[params['gmail']],
        body=msg +'\n'+phone
        )
        flash("Thanks for Submitting your details. I'll get back to you soon!!","success")
    return render_template('contact.html')


@app.route("/post/<string:post_slug>",methods=['GET'])
def route_post(post_slug):
    post = db.posts.find_one({'slug':post_slug})
    return render_template('post.html',post=post)

#to edit and upload post
@app.route("/edit/<string:id>",methods=['GET','POST'])
def edit_post(id):
    if 'user' in session and session['user']==params['admin_username']:
        if request.method=='POST':
            title=request.form.get('title')
            tagline=request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            image_file = request.form.get('img')
            #adding new post
            if id =='0' :
                new_post={"title":title,"tagline":tagline,"slug":slug,"content":content,"img_file":image_file ,"date":datetime.now()}
                db.posts.insert_one(new_post)
            else:
                updated_post={"$set":{"title":title,"tagline":tagline,"slug":slug,"content":content,"img_file":image_file }}
                db.posts.update_one({'_id':ObjectId(id)},updated_post)
                return redirect("/edit/"+str(id))
        if id is not '0':
            post = db.posts.find_one({'_id':ObjectId(id)})
        else:
            post={}
        return render_template('edit.html',post=post,id=id)

#to delete the post
@app.route("/delete/<string:id>",methods=['GET','POST'])
def delete_post(id):
    if 'user' in session and session['user']==params['admin_username']:
        post = db.posts.delete_one({'_id':ObjectId(id)})
    return redirect("/dashboard")



#to automatically detecting changes and debugging
app.run(debug=True)
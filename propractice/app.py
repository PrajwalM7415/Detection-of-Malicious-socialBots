from flask import *
import pandas as pd
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import pickle
import numpy as np
import matplotlib.pyplot as plt
import pymsgbox

app = Flask(__name__)

pickle_in = open('model.pkl','rb')
pac = pickle.load(pickle_in)
tfid = open('tfidf_vectorizer.pkl','rb')
tfidf_vectorizer = pickle.load(tfid)

app.secret_key = 'key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Praju123#'
app.config['MYSQL_DB'] = 'malware'
mysql = MySQL(app)




@app.route('/')
def nav():
    return render_template('navbar.html')
    
@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/pred')
def pred():
    return render_template('prediction.html')

@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/user')
def user():
    return render_template('userlogin.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/userloginaction', methods = ['GET',"POST"])
def userloginaction():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        # Create variables for easy access
        email = request.form['email']
        password = request.form['password']

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM employee WHERE email = %s AND password = %s AND status="Approved" ', (email, password))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            global id
            session['id'] = account['id']
              
            id = session['id']
            session['email'] = account['email']
            # Redirect to home page
            return redirect(url_for('pred'))
        else:
            # Account doesnt exist or username/password incorrect
            flash('Incorrect email/password! or Account Blocked')
            return redirect(url_for('userlogin'))
    # Show the login form with message (if any)
    print("The msg is ", msg)
    return render_template('userlogin.html', msg = msg)


@app.route('/userlogin')
def userlogin():
    return render_template('userlogin.html')

@app.route('/register',methods = ['GET',"POST"])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'email' in request.form and 'password' in request.form:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,10}$"
        pattern = re.compile(reg)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor) 
        cursor.execute('SELECT * FROM employee WHERE Username = %s',(username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not re.search(pattern, password):
            msg = 'Password should contain atleast one number, one lower case character, one uppercase character, one special symbol and must be between 6 to 10 characters long'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO employee VALUES (NULL, %s, %s, %s, "Approved")', (username, email, password))
            mysql.connection.commit()
            flash('You have successfully registered! Please proceed for login!')
            return redirect(url_for('user')) 
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
        return msg 
    return render_template('signup.html', msg=msg)



    

@app.route('/loginaction', methods=['POST'])
def loginaction():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'Prajwal' and password == 'prajju':
            return redirect (url_for('userdetail'))
        else:
            return 'INVALID LOGIN'
    else:
        return 'INVALID LOGIN'

@app.route('/userdetail')
def userdetail():  
   cur = mysql.connection.cursor()      
   cur.execute("SELECT * from employee")
   useradmin=cur.fetchall()
   print(useradmin)
       
   return render_template('userDetails.html',useradmin=useradmin)

@app.route('/users2')
def users2():
    return render_template('users.html')

@app.route('/blockUser',methods=['GET','POST'])
def blockUser():
    if request.method == 'POST' and 'fid' in request.form:
        f1 = request.form['fid']
        con=mysql.connection.cursor()
        con.execute("UPDATE employee SET status='Blocked' WHERE id=%s " , (f1,))
        mysql.connection.commit()
        con.close()
        return redirect(url_for('admin'))




@app.route('/preview',methods = ["POST"])
def preview():
    if request.method == "POST":
        dataset = request.files['datasetfile']
        df = pd.read_csv(dataset,encoding = 'unicode_escape')
        return render_template("preview.html",df_view = df)

@app.route('/chart')
def chart():
       abc = request.args.get('news')
       
       #input_data=re.search("(?P<url>https?://[^\s]+)",abc).group("url")
       #string = [input_data.rstrip()]
       pattern =  r'(?:http://)?\w+\.\S*[^.\s]'
       input_data=re.findall(pattern, abc)
	    
       if input_data:
           
 
         tfidf_test = tfidf_vectorizer.transform(input_data)
         y_pred = pac.predict(tfidf_test)
         pred=format(y_pred[0])
         login()
         cur = mysql.connection.cursor()
         cur.execute("INSERT INTO review(news_content,pred,userid,url) VALUES ( %s, %s,%s,%s) ", (input_data,pred,id,abc))
         mysql.connection.commit()
         cur.close()
       else:
         pymsgbox.alert('Enter the url', 'warning')
         return render_template('prediction.html')
       return redirect('/users')

@app.route('/users')
def users():
     
    cur = mysql.connection.cursor()
    resultValue = cur.execute(" SELECT * from employee INNER JOIN review ON employee.id = review.userId WHERE status !='Blocked';")
     
    if resultValue > 0:
        userDetails = cur.fetchall()
         
        return render_template('users.html',userDetails=userDetails)
    
         
@app.route('/admin')
def admin():
    cur = mysql.connection.cursor()
    resultValue = cur.execute(" SELECT * from employee INNER JOIN review ON employee.id = review.userId;")
     
    if resultValue > 0:
        userDetails = cur.fetchall()
    return render_template('admin.html',userDetails=userDetails) 


@app.route('/analysis')
def analysis():
    legend = "review by pred"
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("SELECT pred from review GROUP BY pred")
        # data = cursor.fetchone()
        rows1 = cursor.fetchall()
        labels = list()
        i = 0
        for row1 in rows1:
            labels.append(row1[i])
        cursor.execute("SELECT pred from review GROUP BY pred")
        # data = cursor.fetchone()
        rows2 = cursor.fetchall()
        
        label = list()
        j = 0
        values = list()
        k = 0
        for row2 in rows2:
            label.append(row2[j])
            cursor.execute("SELECT COUNT(id) from review WHERE pred=%s", (row2[j],))
            rows3 = cursor.fetchall()
             
            #j=j+1
        # Convert query to objects of key-value pairs
            
            for row3 in rows3:
	              values.append(row3[k])
            #k=k+1
        mysql.connection.commit()
        cursor.close()
    except:
        print('Error: unable to fetch items')    

    return render_template('analysis.html', values=values, labels = labels, legend=legend)


if __name__ == '__main__':
    app.run(debug=True)
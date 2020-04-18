import logging #package for logging
import logging.handlers #package for logging
from wsgiref.simple_server import make_server #creates server to test
import mysql.connector #sql integration package
import smtplib, ssl
version = '49'
whatsnew = 'Fixed a lot of stuff'

# set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
LOG_FILE = '/opt/python/log/sample-app.log' #where file of logger is
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1048576, backupCount=5)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s') # formats how logger is written
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info("Oliver: logger started") #message to show logger is running

# boilerplate html
header = """
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
  <!--<link rel="icon" type="image/png" href="icons/xml.png">-->
  <title>Oli's quiz</title>
  <style>
  body {
    color: #000000;
    background-color: #000000;
    font-family: Arial, sans-serif;
    font-size:14px;
    -moz-transition-property: text-shadow;
    -moz-transition-duration: 4s;
    -webkit-transition-property: text-shadow;
    -webkit-transition-duration: 4s;
    text-shadow: none;
  }
  body.blurry {
    -moz-transition-property: text-shadow;
    -moz-transition-duration: 4s;
    -webkit-transition-property: text-shadow;
    -webkit-transition-duration: 4s;
    text-shadow: #fff 0px 0px 25px;
  }
  a {
    color: #FFFFFF;
  }
  .textColumn, .linksColumn .quiz {
    padding: 2em;
  }
  .textColumn {
    position: absolute;
    top: 0px;
    right: 0px;
    bottom: 0px;
    left: 0px;

    text-align: right;
    padding-top: 11em;
    background-color: #40E0D0;
    background-image: -moz-radial-gradient(left top, circle, #6AF9BD 0%, #00B386 60%);
    background-image: -webkit-gradient(radial, 0 0, 1, 0 0, 500, from(#008080), to(#40e0d0));
  }
  .quiz {
    padding-bottom: 15em;
    background-color: #009C9E;
    border: 2px #008385;
  }
  .textColumn p {
    width: 75%;
    float:right;
  }
  h1 {
    font-size: 500%;
    font-weight: normal;
    margin-bottom: 0em;
  }
  h2 {
    font-size: 200%;
    font-weight: normal;
    margin-bottom: 0em;
  }
  ul {
    padding-left: 1em;
    margin: 0px;
  }
  li {
    margin: 1em 0em;
  }
  </style>
</head>
"""
# title screen
welcome1 = """
<body id="sample">
  <div class="textColumn">
    <h1><span style="color:#ff0000;">Q</span><span style="color:#ff7f00;">U</span><span style="color:#ffff00;">I</span><span style="color:#00ff00;">Z</span><span style="color:#00ffff;">Z</span></h1>
    <p>Created by Oliver Cieplinski </p>
"""
# title info
welcome1 += '\n   <p>Version ' + version + '<br> Whats new?: ' + whatsnew + ' </p>'
icon = '<h1><font color="#FFE0D0">QUIZZ v' + version + '</font></h1>'
welcome2 = """
  </div>
</body>
"""
footer = """
</html>
"""

# allows forms to be parsed as a dictionary
def parsePostData(body):
    dic = {}
    tokens = body.split('&')
    for t in tokens:
        k,v = t.split('=')
        dic[k] = v
    return dic

# take mysql query and username to get full name of the player
def getFullName(cursor, username):
    query = 'select first_name from users where username = "' + username + '"'
    cursor.execute(query)
    first_name = cursor.fetchone()[0]
    query = 'select last_name from users where username = "' + username + '"'
    cursor.execute(query)
    last_name = cursor.fetchone()[0]
    fullname = first_name + " " + last_name
    return fullname

# The entire process of the quiz being done.
def quizProcess(bodyDict,mysqlcnx,cursor, body, gameover,username):
    qid = bodyDict['qid']
    score = bodyDict['score']
    quizid = bodyDict['quizid']
    qsdone = bodyDict['qsdone']
    userid = bodyDict['userid']
    question = bodyDict['question']
    useranswer = bodyDict['usanswer']
    if 'challengeid' in bodyDict:
        challengeid = bodyDict['challengeid']
        if not challengeid:
            challengeid = '0'
    else:
        challengeid = '0'
    if 'opponentid' in bodyDict:
        opponentid = bodyDict['opponentid']
        if not opponentid:
            opponentid = '0'
    else:
        opponentid = '0'
    qsdone = str(int(qsdone) + 1)
    logger.info("qid: %s, score: %s, qsdone: %s", qid, score, qsdone)
    answer = bodyDict['answer']
    answer = answer.replace("%2B", " ")
    useranswer = useranswer.replace("+", " ")
    uppanswer = useranswer.upper()
    body += '<p>You answered: <br>'
    body += useranswer + '<br>'
    query = 'select count(*) from questions where quizid = ' + quizid
    cursor.execute(query)
    numqs = int(cursor.fetchone()[0])
    logger.info("numqs: %d", numqs)
    if numqs >= int(qsdone) and gameover != True:
        result = answer
        uppresult = result.upper()
        if uppresult == uppanswer:
            body += 'That is correct!</p>'
            score = str(int(score) + 1)                
        else:
            body += 'Unlucky the answer is : ' + result + '</p>'
        qid = str(int(qid) + 1)
        if str(numqs) != qsdone:
            body += 'You are currently on ' + str(score) + '/' + qsdone + '.'   
        if str(numqs) == qsdone:
            body += 'Game over, you achieved ' + score + ' out of ' + qsdone + '!' + '.</p>'
            query = 'insert into scores(userid, quizid, score) values(' + userid + ',' + quizid + ',' + score + ')'
            cursor.execute(query)
            mysqlcnx.commit()
            query = 'update quizzes set plays = plays + 1 where quizid = ' + quizid
            cursor.execute(query)
            mysqlcnx.commit()
            print(opponentid)
            print(challengeid)
            if int(challengeid) != 0 or int(opponentid) != 0 :
                body += 'You have completed the challenge!<br>'
                print(opponentid)
                print(challengeid)
                if int(opponentid) != 0:
                    query = 'insert into challenge(user1,user2,quizid,score1) values("' + userid + '","' + opponentid + '",' + str(quizid) + ',' + str(score) + ')'
                    cursor.execute(query)
                    mysqlcnx.commit()
                    sendRequest(cursor,userid,quizid,username,opponentid)
                else:
                    query = 'select user1 from challenge where id = ' + str(challengeid)
                    cursor.execute(query)
                    challengerid = cursor.fetchone()[0]
                    query = 'select username from users where id = ' + str(challengerid)
                    cursor.execute(query)
                    user1 = cursor.fetchone()[0]
                    score = int(score)
                    query = 'select score1 from challenge where id = ' + str(challengeid)
                    cursor.execute(query)
                    oppscore = cursor.fetchone()[0]
                    if score > int(oppscore):
                        body += '<font color = "green">Congratulations! You defeated ' + str(user1) + ' by ' + str((int(score)-int(oppscore))) + ' points in the challenge!</font>'
                        res = 0
                    elif score == int(oppscore):
                        body += '<font color = "yellow">Wow! You drew with ' + str(user1) + ' in the challenge!</font>'
                        res = 1
                    else:
                        body += '<font color = "red">Oh no! You lost to ' + str(user1) + ' by ' + str((int(oppscore-int(score)))) + ' in the challenge!</font>'
                        res = 2
                    body += '<br>'
                    sendResults(cursor,username,res,challengeid)
                    query = 'delete from challenge where id = ' + challengeid
                    cursor.execute(query)
                    mysqlcnx.commit()
            body += greatestscore(cursor,score,quizid,userid)
            body += 'The 5 highest scores are: '
            body += highscore(cursor,quizid,numqs)
            body += '<br> <br>'
            body += vote(username,userid,quizid)
            gameover = True
    return gameover, score, qid, qsdone, body, quizid

#allows user to upvote or downvote a quiz
def vote(username,userid,quizid):
    formBody = ''
    formBody += initForm(username,formBody,userid,'')
    formBody += 'How would you rate this quiz?'
    formBody += '<button name="vote" type ="submit" value ="like">I like it!</button>  '
    formBody += '<button name="mode" type ="submit" value ="">No opinion.</button>  '
    formBody += '<button name="vote" type ="submit" value ="dislike">I dislike it.</button>  '
    formBody += '<input type="hidden" name="quizid" value="' + quizid + '">'
    return formBody

#preloaded form code and hidden values inside of the form.
def initForm(username,formBody,userid,whichmode):
    formBody += '<p><form action="quiz" method="post">'
    formBody += '<input type="hidden" name="authentication" value="DONE">'
    formBody += '<input type="hidden" name="username" value="' + username + '">'
    formBody += '<input type="hidden" name="userid" value="' + str(userid) + '">'
    formBody += '<input type="hidden" name="mode" value="' + whichmode + '">'
    return formBody

#Creates main menu with selection, create quiz, add questions and challenge
def dashboard(username,userid):
    value = 0
    formBody = '<p><form action="quiz" method="post">'
    formBody += initForm(username,formBody,userid,'')
    formBody += '<h2><b>Dashboard:<b></h2> <br>'
    formBody += '<button name ="mode" type ="submit" value ="select">Select Quiz</button> <br><br>'
    formBody += '<button name ="mode" type ="submit" value ="create">Create Quiz</button> <br><br>'
    formBody += '<button name ="mode" type ="submit" value ="add">Add Questions</button> <br><br>'
    formBody += '<button name ="mode" type ="submit" value ="challenge">Challenges</button>'
    return formBody

#Allows user to select a quiz to play 
def selectQuiz(username,cursor,userid,sort,opponentid): 
    formBody = '<p><form action="quiz" method="post">'
    formBody += initForm(username,formBody,userid,'play')
    formBody += 'Sort by:  '
    formBody += '<button name ="sort" type ="submit" value ="rated">Highest Rated</button>   '
    formBody += '<button name ="sort" type ="submit" value ="popular">Popular</button>    '
    formBody += '<button name ="sort" type ="submit" value ="recent">Recent</button>    '
    formBody += '<button name ="sort" type ="submit" value ="length">Length</button> <br>'
    formBody += 'Select Quiz: <br><br>'
    i = 1
    if sort != '':
        if sort == 'rated':
            query = 'select quizid,title,reputation,plays,topic,creator,length from quizzes order by reputation desc'
            cursor.execute(query)
            quizinfo = cursor.fetchall()
            formBody += '<input type="hidden" name="opponentid" value=' + opponentid + '>'
        if sort == 'popular':
            query = 'select quizid,title,reputation,plays,topic,creator,length from quizzes order by plays desc'
            cursor.execute(query)
            quizinfo = cursor.fetchall()
            formBody += '<input type="hidden" name="opponentid" value=' + opponentid + '>'
        if sort == 'recent':
            query = 'select quizid,title,reputation,plays,topic,creator,length from quizzes order by quizid desc'
            cursor.execute(query)
            quizinfo = cursor.fetchall()
            formBody += '<input type="hidden" name="opponentid" value=' + opponentid + '>'
        if sort == 'length':
            query = 'select quizid,title,reputation,plays,topic,creator,length from quizzes order by length asc'
            cursor.execute(query)
            quizinfo = cursor.fetchall()
            formBody += '<input type="hidden" name="opponentid" value=' + opponentid + '>'
    for q in quizinfo:
        quizid = str(q[0])
        quiname = str(q[1])
        rep = str(q[2])
        plays = str(q[3])
        topic = str(q[4])
        creator = str(q[5])
        length = str(q[6])
        repi = int(rep)
        if repi > 0:
            colour = 'green'
        elif repi == 0:
            colour = 'yellow'
        elif repi < 0:
            colour = 'red'
        formBody += '<button name="quizid" type = "submit" value = "' + quizid + '">' + quiname  + '</button> Created by: ' + creator + ' <br> Topic: <font color = "purple">' + topic + '</font>  Length: <font color = "orange">' + length + '</font> questions<br> <font color = "' + colour + '">Reputation: ' + rep + '</font>   Plays: <font color = "blue">' + plays + '</font>'
        formBody += '<input type="hidden" name="opponentid" value=' + opponentid + '>'
        formBody += '<br><br>'
        i = i + 1
    formBody += goBack()
    return formBody

#creates a return to dashboard function
def goBack():
    formBody = '<p><form action="quiz" method="post"><br><br>'
    formBody += '<button name="goback" type = "submit" value = "goback"><font color="red">Back to Dashboard</font></button>'
    return formBody

#Declares quiz name and topic name for new quiz
def createQuiz(username,cursor,userid,bodyDict):
    formBody = '<p><form action="quiz" method="post">'
    formBody += initForm(username,formBody,userid,'create')
    formBody += '<h2><b>Create Quiz: </b></h2><br>'
    formBody += 'What is the name of your quiz? '
    formBody += '<input type="text" name="quizname" autocomplete="off"> <br>'
    formBody += 'What is the topic of your quiz?'
    formBody += '<input type="text" name="topic"> <br>'
    formBody += '<input type="submit" value="Submit">'
    formBody += goBack()
    return formBody

# Gives user a menu of quizzes to add questions to
def addQuestionsSelect(username,cursor,userid):
    formBody = '<p><form action="quiz" method="post">'
    formBody += initForm(username,formBody,userid,'add')
    formBody += '<h3><b>Select Quiz to add questions to: </b></h3><br>'
    query = 'select count(title) from quizzes'
    cursor.execute(query)
    cap = int(int(cursor.fetchone()[0]) + 1)
    for i in range(1,cap):
        query = 'select title from quizzes where quizzes.quizid = ' + str(i)
        cursor.execute(query)
        quiname = str(cursor.fetchone()[0])
        formBody += '<button name="quizno" type = "submit" value = "' + str(i) + '">' + quiname + '</button>'
        formBody += '<br><br>'
    return formBody

#Allows user to submit questions to a quiz
def addQuestions(username,cursor,userid):
    formBody = '<p><form action="quiz" method="post">'
    formBody += initForm(username,formBody,userid,'add')
    formBody += '<b>Question:</b> '
    formBody += '<input type="text" name="question" autocomplete="off"> <br>'
    formBody += '<b>Answer:</b> '
    formBody += '<input type="text" name="answer" autocomplete="off">'
    formBody += '<input type="submit" value="Submit">'
    formBody += goBack()
    return formBody

#Allows user to challenge users and see pending challenges
def challenge(username,cursor,userid):
    formBody = '<p><form action="quiz" method="post">'
    formBody += initForm(username,formBody,userid,'add')
    formBody += '<h2><b>Welcome to the challenge screen!</b></h2> <br> <h3><font color = "yellow">Pending Challenges:</font></h3> <br>'
    query = 'select id,user1,quizid from challenge where user2 = ' + userid
    cursor.execute(query)
    challenges = cursor.fetchall()
    for c in challenges:
        query = 'select username from users where id = ' + str(c[1])
        cursor.execute(query)
        origname = str(cursor.fetchone()[0])
        query = 'select title from quizzes where quizid = ' + str(c[2])
        cursor.execute(query)
        quiname = str(cursor.fetchone()[0])
        formBody += '<b><font color = "green">' + origname + ' challenged you to a quiz on ' + quiname + '!</font></b>'
        formBody += '<button name ="challengeid" type = "submit" value = ' + str(c[0]) + '>Play!</button>  '
        formBody += '<button name ="decline" type = "submit" value = ' + str(c[0]) + '>Decline</button><br><br>'
    formBody += '<br><h3><i> Or please choose the user you want to challenge.</i></h3> <br>'
    query = 'select count(id) from users'
    cursor.execute(query)
    cap = int(int(cursor.fetchone()[0]) + 1)
    for i in range(1,cap):
        if int(i) == int(userid):
            continue
        query = 'select username from users where users.id = ' + str(i)
        cursor.execute(query)
        user = str(cursor.fetchone()[0])
        formBody += '<button name="userid2" type = "submit" value = "' + str(i) + '">' + user + '</button>'
        formBody += '<br><br>'
    formBody += goBack()
    return formBody

# This function allows to send emails asking people to respond to challenges
def sendRequest(cursor,userid,quizid,username,opponentid):
    port = 587  
    smtp_server = 'smtp.gmail.com'
    sender_email = 'quizzapp2020@gmail.com'
    query = 'select email from users where id = ' + str(opponentid)
    cursor.execute(query)    
    receiver_email = str(cursor.fetchone()[0])
    query = 'select title from quizzes where quizid = ' + quizid
    cursor.execute(query)
    equizname = str(cursor.fetchone()[0])
    password = 'xA3dsaD3a!'
    message = """\
Subject: New Quizz Challenge
    
You have received a new challenge!
""" + username + """ has challenged you to a quiz on """ + equizname + """!
Go to http://ec2-3-9-188-244.eu-west-2.compute.amazonaws.com/quiz to play it!"""
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

# This function allows to send emails giving an update on a challenge
def sendResults(cursor,username,res,challengeid):
    port = 587  
    smtp_server = 'smtp.gmail.com'
    sender_email = 'quizzapp2020@gmail.com'
    query = 'select user1 from challenge where id = ' + challengeid
    cursor.execute(query)
    user1 = cursor.fetchone()[0]
    query = 'select email from users where id = "' + str(user1) + '"'
    cursor.execute(query)    
    receiver_email = str(cursor.fetchone()[0])
    password = 'xA3dsaD3a!'
    if res == 0:
        text = 'Oh no! You lost your challenge!'
    elif res == 1:
        text = 'Wow! You drew your challenge!'
    else:
        text = 'WOO! You won your challenge!'
    message = """\
Subject: New Quizz Challenge Update!
    
Your challenge has concluded!
""" + text + """
Rematch them at http://ec2-3-9-188-244.eu-west-2.compute.amazonaws.com/quiz and keep quizzing!"""
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
        
#Calculates top 5 scores inside of the current quiz and displays them in a table
def highscore(cursor,quizid,numqs):
    query = 'select score,userid,scoreid,tstamp from scores where quizid = ' + str(quizid) + '  order by score desc, tstamp desc limit 5'
    cursor.execute(query)
    scores = cursor.fetchall()
    strscores = ''
    i = 1
    strscores += """
        <head>
        <style>
        table, th, td {
         border: 1px solid black;
        }
        </style>
        </head>
        
        <table>
         <tr>
          <th>Position</th>
          <th>Score</th>
          <th>Timestamp</th>
          <th>User</th>
         </tr>
         """
    for s in scores:
        query = 'select users.username from users inner join scores on users.id = scores.userid and userid = ' + str(s[1]) + ' and scoreid = ' + str(s[2])
        cursor.execute(query)
        name = str(cursor.fetchone()[0])
        strscores += ' <tr>'
        strscores += '  <td>' + str(i) + '</td>'
        strscores += '  <td>' + str(s[0]) + '/' + str(numqs) + '</td>'
        strscores += '  <td>' + str(s[3]) + '</td>'
        strscores += '  <td>' + name + '</td>'
        strscores += ' </tr>'
        i += 1
    strscores += '</table>'
    return strscores

#Notifies user on whether they have beaten previous best on current quiz
def greatestscore(cursor,score,quizid,userid):
    string = ''
    query = 'select score from scores where userid = ' + str(userid) + ' and quizid = ' + str(quizid) + ' order by score desc limit 1'
    cursor.execute(query)
    newscore = str(cursor.fetchone()[0])
    if int(score) >= int(newscore):
        string += 'Congratulations! You have beaten your previous best!'
    string += '<br>'
    return string

#The main system of the application, and how it works.
def application(environ, start_response):
    dbsampleout = ''
    path    = environ['PATH_INFO']
    method  = environ['REQUEST_METHOD']
    body = ''
    if method == 'POST':
        request_body_size = int(environ['CONTENT_LENGTH'])
        request_body = environ['wsgi.input'].read(request_body_size).decode()
        logger.info("request path: %s, method: %s, body: %s", path, method, request_body)
        if path == '/signup':
            body = '<div class="quiz">'
            mysqlcnx = mysql.connector.connect(user='admin', password='bocian12', host='aa1s6781lp2nmte.c3tsfr834w4d.eu-west-2.rds.amazonaws.com', database='quizzes');
            cursor = mysqlcnx.cursor()
            bodyDict = parsePostData(request_body)
            logger.info("signup attempted")
            body += '<p><form action="signup" method="post">'
            body += '<font color="white">Username: </font>'
            body += '<input type="text" name="uname" autocomplete="off"> <br>'
            body += '<font color="white">Password: </font>'
            body += '<input type="text" name="pword" autocomplete="off"> <br>'
            body += '<font color="white">First Name: </font>'
            body += '<input type="text" name="fname" autocomplete="off"> <br>'
            body += '<font color="white">Last Name: </font>'
            body += '<input type="text" name="lname" autocomplete="off"> <br>'
            body += '<font color="white">Email: </font>'
            body += '<input type="text" name="email" autocomplete="off"> <br>'
            body += '<input type="submit" value="Sign Up">'
            body += '</form></p>'
            if 'uname' in bodyDict:
                    uname = bodyDict['uname']
                    pword = bodyDict['pword']
                    fname = bodyDict['fname']
                    lname = bodyDict['lname']
                    email = bodyDict['email']
                    query = 'insert into users(username,password,first_name,last_name,email) values("' + uname + '","' + pword + '","' + fname + '","' + lname + '","' + email + '")'
                    cursor.execute(query)
                    mysqlcnx.commit()
            body += '<a href="/quiz">Go to Log In</a>'
        elif path == '/quiz':
            try:
                authenticated = False
                body = '<div class="quiz">'
                mysqlcnx = mysql.connector.connect(user='admin', password='bocian12', host='aa1s6781lp2nmte.c3tsfr834w4d.eu-west-2.rds.amazonaws.com', database='quizzes');
                cursor = mysqlcnx.cursor()
                bodyDict = parsePostData(request_body)
                username = bodyDict['username']
                userid = ''
                if 'authentication' in bodyDict:
                    authstatus = bodyDict['authentication']
                    if authstatus.startswith('NONE'):
                        username = bodyDict['username']
                        password = bodyDict['password']
                        if username == '' or password == '':
                            body = '<a href="/quiz">not authenticated</a>'
                        else:
                            query = 'select password from users where username = "' + username + '"'
                            cursor.execute(query)
                            result = cursor.fetchone()[0]
                            query = 'select id from users where username = "' + username + '"'
                            cursor.execute(query)
                            userid = cursor.fetchone()[0]
                            logger.info("u: %s, p: %s, r: %s",username,password,result)
                            if result == password:
                                authenticated = True
                            else:
                                logger.info('not authenticated')
                    else:
                        authenticated = True
                        userid = bodyDict['userid']
                if authenticated:
                    logger.info('authenticated as ' + username)
                    fullname = getFullName(cursor, username)
                    body += '<p>Hello ' + fullname + '<br></p>'
                    gameover = False
                    if 'vote' in bodyDict:
                        quizid = bodyDict['quizid']
                        if bodyDict['vote'] == 'like':
                            query = 'update quizzes set reputation = reputation + 1 where quizid = ' + str(quizid)
                            cursor.execute(query)
                            mysqlcnx.commit()
                        if bodyDict['vote'] == 'dislike':
                            query = 'update quizzes set reputation = reputation - 1 where quizid = ' + str(quizid)
                            cursor.execute(query)
                            mysqlcnx.commit()
                    if not 'mode' in bodyDict or bodyDict['mode'] == '' or 'goback' in bodyDict:    
                        body += dashboard(username,userid)
                    elif bodyDict['mode'] == 'select' or 'sort' in bodyDict or 'userid2' in bodyDict:
                        if 'sort' in bodyDict:
                            sort = bodyDict['sort']
                            if 'opponentid' in bodyDict:
                                opponentid = bodyDict['opponentid']
                            else:
                                opponentid = '0'
                        elif 'userid2' in bodyDict:
                            opponentid = str(bodyDict['userid2'])
                            sort = 'popular'
                        else:
                            opponentid = '0'
                            sort = 'popular'
                        body += selectQuiz(username,cursor,userid,sort,opponentid)
                    elif 'decline' in bodyDict:
                        deleteid = bodyDict['decline']
                        query = 'delete from challenge where id = ' + deleteid
                        cursor.execute(query)
                        mysqlcnx.commit()
                        body += challenge(username,cursor,userid)
                    elif bodyDict['mode'] == 'play' or 'challengeid' in bodyDict:
                        if 'challengeid' in bodyDict:
                            challengeid = bodyDict['challengeid']
                            opponentid = 0
                            query = 'select quizid from challenge where id = ' + str(challengeid)
                            cursor.execute(query)
                            quizid = str(cursor.fetchone()[0])
                        else:
                            challengeid = 0
                            if 'opponentid' in bodyDict:
                                opponentid = bodyDict['opponentid']
                            else:
                                opponentid = 0
                            quizid = bodyDict['quizid']
                        if 'answer' in bodyDict:
                            gameover,score,qid,qsdone,body,quizid = quizProcess(bodyDict,mysqlcnx,cursor,body,gameover,username)
                        else:
                            qid = str(0)
                            score = '0'
                            qsdone = '0'
                            query = 'select question,answer from questions where quizid = ' + str(quizid) + ' limit 1 offset ' + str(qid)
                            cursor.execute(query)
                            question,answer = cursor.fetchone()
                        if gameover == False:
                            query = 'select question,answer from questions where quizid = ' + str(quizid) + ' limit 1 offset ' + str(qid)
                            cursor.execute(query)
                            question,answer = cursor.fetchone()
                            answer = answer.replace(" ", "+")
                            formBody = ''
                            body += initForm(username,formBody,userid,'play')
                            body += question + ':<br><input type="text" name="usanswer" autocomplete="off">'
                            body += '<input type="hidden" name="quizid" value=' + quizid + '>'
                            body += '<input type="hidden" name="qid" value=' + qid + '>'
                            body += '<input type="hidden" name="score" value=' + score + '>'
                            body += '<input type="hidden" name="qsdone" value=' + qsdone + '>'
                            body += '<input type="hidden" name="question" value=' + question + '>'
                            body += '<input type="hidden" name="answer" value=' + answer + '>'
                            body += '<input type="submit" value="Submit"></p>'
                            if challengeid != 0:
                                body += '<input type="hidden" name="challengeid" value =' + str(challengeid) + '>'
                            if opponentid != 0:
                                body += '<input type="hidden" name="opponentid" value =' + str(opponentid) + '>'
                    elif bodyDict['mode'] == 'create':
                        if 'quizname' in bodyDict:
                            topic = bodyDict['topic']
                            qname = bodyDict['quizname']
                            qname = qname.replace("+", " ")
                            qname = qname.replace("%3F","?")
                            query = 'insert into quizzes(title,reputation,plays,topic,creator,length) values("' + str(qname) + '",0,0,"' + topic + '", "' + str(username) + '",0)'
                            print(query)
                            cursor.execute(query)
                            mysqlcnx.commit()
                            print(query)
                            body += dashboard(username,userid)
                        else:
                            body += createQuiz(username,cursor,userid,bodyDict)
                    elif bodyDict['mode'] == 'challenge':
                        body += challenge(username,cursor,userid)
                    elif bodyDict['mode'] == 'add':
                        if 'quizno' in bodyDict or 'question' in bodyDict:
                            if 'quizno' in bodyDict:
                                global qno
                                qno = bodyDict['quizno']
                            if 'question' in bodyDict:
                                q = bodyDict['question']
                                q = q.replace("+", " ")
                                q = q.replace("%3F","?")
                                q = q.replace("%27","'")
                                a = bodyDict['answer']
                                a = a.replace("+", " ")
                                a = a.replace("%3F","?")
                                a = a.replace("%27","'")
                                query = 'insert into questions(question,answer,quizid) values("' + str(q) + '","' + str(a) + '",' + str(qno) + ')'
                                cursor.execute(query)
                                mysqlcnx.commit()
                                query = 'update quizzes set length = length + 1 where quizid = ' + str(qno)
                                cursor.execute(query)
                                mysqlcnx.commit()
                                body += dashboard(username,userid)
                            else:
                                body += addQuestions(username,cursor,userid)
                        else:
                            body += addQuestionsSelect(username,cursor,userid)
                else:
                    logger.info('not authenticated')
                    body = '<a href="/quiz">not authenticated</a>'
                cursor.close()
                mysqlcnx.close()
                body += '</div>'
            except mysql.connector.Error as err:
                logger.error("mysql error")
                if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
                    logger.error("Failed: authentication")
                elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                    logger.error("Failed: bad db")
                else:
                    logger.error("Failed: other exception")
                    logger.error(err.msg)
        else:
            body = '<body>what are you trying to do?</body>'
        response =  header + icon + body + footer
        logger.info(response)
    else:
        if path == '/favicon.ico':
            body = ''
        else:
            body = """
                <p><form action="quiz" method="post">
                <input type="hidden" name="authentication" value="NONE">
                <input type="text" name="username" autocomplete="off">
                <input type="text" name="password" autocomplete="off">
                <input type="submit" value="Log in">
                </form></p>
                <p><form action="signup" method="post">
                <input type="submit" name = "sign" value="Signup">
                </form></p>
                """
        response = header + welcome1 + body + welcome2 + footer
    status = '200 OK'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    logger.info(status)
    return [response.encode("utf-8")]
# standalone main
if __name__ == '__main__':
    httpd = make_server('localhost', 8000, application)
    print("Serving on port 8000...")
    httpd.serve_forever()
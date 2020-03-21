import logging #package for logging
import logging.handlers #package for
from wsgiref.simple_server import make_server
import mysql.connector

version = '47'
whatsnew = 'Battle your friends!'

# set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
LOG_FILE = '/opt/python/log/sample-app.log' #where file of logger is
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1048576, backupCount=5)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info("Oliver: logger started")

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

# valid keys: authentication, username, password, answer, qid, score, qsdone
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
# undergoes quiz process
def quizProcess(bodyDict,mysqlcnx,cursor, body, gameover,username):
    chalmode = False
    print(chalid)
    function = ''
    print(bodyDict)
    qid = bodyDict['qid']
    score = bodyDict['score']
    quizid = bodyDict['quizid']
    qsdone = bodyDict['qsdone']
    userid = bodyDict['userid']
    question = bodyDict['question']
    useranswer = bodyDict['usanswer']
    qsdone = str(int(qsdone) + 1)
    logger.info("qid: %s, score: %s, qsdone: %s", qid, score, qsdone)
    answer = bodyDict['answer']
    print(answer)
    answer = answer.replace("%2B", " ")
    useranswer = useranswer.replace("+", " ")
    uppanswer = useranswer.upper()
    body += '<p>You answered: <br>'
    body += useranswer + '<br>'
    query = 'select count(*) from questions where quizid = ' + quizid
    cursor.execute(query)
    numqs = int(cursor.fetchone()[0])
    logger.info("numqs: %d", numqs)
    if chalid is not None:
        chalmode = True
    if numqs >= int(qsdone) and gameover != True:
        result = answer
        print(result)
        uppresult = result.upper()
        print(uppresult)
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
            if chalmode == True:
                body += 'You have completed the challenge!<br>'
                print(chalid)
                if chalid == 1:
                    print('fasdf')
                    query = 'insert into challenge(user1,user2,quizid,score1) values("' + username + '","' + opponentid + '",' + str(quizid) + ',' + str(score) + ')'
                    print('insert into challenge(user1,user2,quizid,score1) values("' + username + '","' + opponentid + '",' + str(quizid) + ',' + str(score) + ')')
                    cursor.execute(query)
                    mysqlcnx.commit()
                else:
                    print('challengeid ' + challengeid)
                    query = 'select user1 from challenge where id = ' + str(challengeid)
                    cursor.execute(query)
                    score = int(score)
                    opp = cursor.fetchone()[0]
                    query = 'select score1 from challenge where id = ' + str(challengeid)
                    cursor.execute(query)
                    oppscore = cursor.fetchone()[0]
                    if score > int(oppscore):
                        body += '<font color = "green">Congratulations! You defeated ' + str(opp) + ' by ' + str((int(score)-int(oppscore))) + ' points in the challenge!</font>'
                    elif score == int(oppscore):
                        body += '<font color = "yellow">Wow! You drew with ' + str(opp) + ' in the challenge!</font>'
                    else:
                        body += '<font color = "red">Oh no! You lost to ' + str(opp) + ' by ' + str((int(oppscore-int(score)))) + ' in the challenge!</font>'
                    body += '<br>'
                    query = 'delete from challenge where id = ' + challengeid
                    cursor.execute(query)
                    mysqlcnx.commit()
           # body += greatestscore(cursor,score,quizid,userid)
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
#creates 
def initForm(username,formBody,userid,whichmode):
    formBody += '<p><form action="quiz" method="post">'
    formBody += '<input type="hidden" name="authentication" value="DONE">'
    formBody += '<input type="hidden" name="username" value="' + username + '">'
    formBody += '<input type="hidden" name="userid" value="' + str(userid) + '">'
    formBody += '<input type="hidden" name="mode" value="' + whichmode + '">'
    return formBody

def dashboard(username,userid):
    value = 0
    formBody = '<p><form action="quiz" method="post">'
    formBody += initForm(username,formBody,userid,'')
    formBody += 'Dashboard: <br><br>'
    formBody += '<button name ="mode" type ="submit" value ="select">Select Quiz</button> <br>'
    formBody += '<button name ="mode" type ="submit" value ="create">Create Quiz</button> <br>'
    formBody += '<button name ="mode" type ="submit" value ="add">Add Questions</button> <br>'
    formBody += '<button name ="mode" type ="submit" value ="challenge">Challenge a Friend</button>'
    return formBody

def selectQuiz(username,cursor,userid,sort): 
    formBody = '<p><form action="quiz" method="post">'
    formBody += initForm(username,formBody,userid,'play')
    formBody += 'Sort by:  '
    formBody += '<button name ="sort" type ="submit" value ="rated">Highest Rated</button>   '
    formBody += '<button name ="sort" type ="submit" value ="popular">Popular</button>    '
    formBody += '<button name ="sort" type ="submit" value ="recent">Recent</button>'
    formBody += '<button name ="sort" type ="submit" value ="length">Length</button> <br>'
    formBody += 'Select Quiz: <br><br>'
    i = 1
    if sort != '':
        if sort == 'rated':
            query = 'select quizid,title,reputation,plays,topic,creator,length from quizzes order by reputation desc'
            cursor.execute(query)
            quizinfo = cursor.fetchall()
        if sort == 'popular':
            query = 'select quizid,title,reputation,plays,topic,creator,length from quizzes order by plays desc'
            cursor.execute(query)
            quizinfo = cursor.fetchall()
        if sort == 'recent':
            query = 'select quizid,title,reputation,plays,topic,creator,length from quizzes order by quizid desc'
            cursor.execute(query)
            quizinfo = cursor.fetchall()
        if sort == 'length':
            query = 'select quizid,title,reputation,plays,topic,creator,length from quizzes order by length asc'
            cursor.execute(query)
            quizinfo = cursor.fetchall()
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
        formBody += '<br><br>'
        i = i + 1
    return formBody
def register():
    formBody = '<p><form action="quiz" method="post">'
    formBody += 'Enter your username: <br>'
    formBody += '<input type="text" name="username" autocomplete="off"> <br>'
    formBody += 'Enter your password: <br>'
    formBody += '<input type="text" name="password" autocomplete="off"> <br>'

def createQuiz(username,cursor,userid,bodyDict):
    formBody = '<p><form action="quiz" method="post">'
    formBody += initForm(username,formBody,userid,'create')
    formBody += 'Create Quiz: <br><br>'
    formBody += 'What is the name of your quiz? '
    formBody += '<input type="text" name="quizname" autocomplete="off"> <br>'
    formBody += 'What is the topic of your quiz?'
    formBody += '<input type="text" name="topic"> <br>'
    formBody += '<input type="submit" value="Submit">'
    return formBody

def addQuestionsSelect(username,cursor,userid):
    formBody = '<p><form action="quiz" method="post">'
    formBody += initForm(username,formBody,userid,'add')
    formBody += 'Select Quiz to add questions to: <br><br>'
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

def addQuestions(username,cursor,userid):
    formBody = '<p><form action="quiz" method="post">'
    formBody += initForm(username,formBody,userid,'add')
    formBody += 'Question: '
    formBody += '<input type="text" name="question" autocomplete="off"> <br>'
    formBody += 'Answer: '
    formBody += '<input type="text" name="answer" autocomplete="off">'
    formBody += '<input type="submit" value="Submit">'
    return formBody

def challenge(username,cursor,userid):
    formBody = '<p><form action="quiz" method="post">'
    formBody += initForm(username,formBody,userid,'add')
    global chalid
    chalid = 0
    formBody += 'Welcome to the challenge screen! <br> <font color = "yellow">Pending Challenges:</font> <br>'
    query = 'select id,user1,quizid from challenge where user2 = ' + userid
    cursor.execute(query)
    challenges = cursor.fetchall()
    for c in challenges:
        query = 'select title from quizzes where quizid = ' + str(c[2])
        cursor.execute(query)
        quiname = str(cursor.fetchone()[0])
        formBody += '<font color = "green">' + str(c[1]) + ' challenged you to a quiz on ' + quiname + '!</font>'
        formBody += '<button name ="chalacc" type = "submit" value = ' + str(c[0]) + '>Play!</button>'
    formBody += '<br> Or please choose the user you want to challenge. <br>'
    query = 'select count(id) from users'
    cursor.execute(query)
    cap = int(int(cursor.fetchone()[0]) + 1)
    for i in range(1,cap):
        query = 'select username from users where users.id = ' + str(i)
        cursor.execute(query)
        user = str(cursor.fetchone()[0])
        formBody += '<button name="userid2" type = "submit" value = "' + str(i) + '">' + user + '</button>'
        formBody += '<br><br>'
    return formBody

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

#def greatestscore(cursor,score,quizid,userid):
    #string = ''
    #query = 'select score from scores where userid = ' + str(userid) + ' and quizid = ' + str(quizid) + ' limit 1'
   # print('query: ' + query)
    #cursor.execute(query)
   # newscore = str(cursor.fetchone()[0])
   # if int(score) > int(newscore):
    #    string += 'Congratulations! You have beaten your previous best!'
   # string += '<br>'
    #return string

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
            print('hi')
            body += '<p><form action="signup" method="post">'
            body += '<font color="white">Username: </font>'
            body += '<input type="text" name="uname" autocomplete="off"> <br>'
            body += '<font color="white">Password: </font>'
            body += '<input type="text" name="pword" autocomplete="off"> <br>'
            body += '<font color="white">First Name: </font>'
            body += '< type="text" name="fname" autocomplete="off"> <br>'
            body += '<font color="white">Last Name: </font>'
            body += '<input type="text" name="lname" autocomplete="off">'
            body += '<input type="submit" value="Sign Up">'
            body += '</form></p>'
            print(bodyDict)
            if 'uname' in bodyDict:
                    uname = bodyDict['uname']
                    pword = bodyDict['pword']
                    fname = bodyDict['fname']
                    lname = bodyDict['lname']
                    query = 'insert into users(username,password,first_name,last_name) values("' + uname + '","' + pword + '","' + fname + '","' + lname + '")'
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
                        print(bodyDict)
                        if username == '' or password == '':
                            body = '<a href="/quiz">not authenticated</a>'
                            print('safda')
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
                    if not 'mode' in bodyDict or bodyDict['mode'] == '':    
                        body += dashboard(username,userid)
                    elif bodyDict['mode'] == 'play' or 'chalacc' in bodyDict:
                        if 'chalacc' in bodyDict:
                            global challengeid
                            challengeid = bodyDict['chalacc']
                            query = 'select quizid from challenge where id = ' + str(challengeid)
                            cursor.execute(query)
                            quizid = str(cursor.fetchone()[0])
                        else:
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
                            print(answer)
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
                    elif bodyDict['mode'] == 'select' or 'sort' in bodyDict or 'userid2' in bodyDict:
                        global opponentid
                        if 'sort' in bodyDict:
                            sort = bodyDict['sort']
                            opponentid = ''
                        elif 'userid2' in bodyDict:
                            opponentid = str(bodyDict['userid2'])
                            global chalid
                            chalid = 1
                            sort = 'popular'
                            print('hey')
                        else:
                            opponentid = ''
                            sort = 'popular'
                        body += selectQuiz(username,cursor,userid,sort)
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
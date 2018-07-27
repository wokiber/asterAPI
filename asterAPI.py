#import logging
import sys
import time
#from logging.handlers import SysLogHandler
from flask import Flask, jsonify, request, json
#from Service import find_syslog, Service
from flask_restful import Resource, Api
from flaskext.mysql import MySQL
from  flask_httpauth import HTTPBasicAuth
import os




app = Flask(__name__)
mysql = MySQL()
api = Api(app)
auth = HTTPBasicAuth()
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'asterisk_adm'
app.config['MYSQL_DATABASE_PASSWORD'] = 'pkuhEQzrf(1UOFBO!0^wGo'
app.config['MYSQL_DATABASE_DB'] = 'asterisk_log'
app.config['MYSQL_DATABASE_HOST'] = '94.130.82.156'
mysql.init_app(app)
conn = mysql.connect()
cursor = conn.cursor()
teamPropStatus = ['on','off']
teamPropMap = {'on':'true','off':'false','null':'null'}
teamPropKeys = ['Global_Routing','Local_Conference','Local_Listening','Local_Routing','Local_Wispering']
wrongSigns = '~!@#$%^&*()–+=,.<>?;:[]{} '
wrongPassSigns = ' '
digits='0123456789'
trunkKeys={'name':[]}
trunkKeys.update({'username':[]})
trunkKeys.update({'fromuser':[]})
trunkKeys.update({'secret':[]})
trunkKeys.update({'host':[]})
trunkKeys.update({'fromdomain':[]})
trunkKeys.update({'callbackextension':[]})
trunkKeys.update({'nat':['no','yes','auto_comedia','auto_force_port','comedia','force_port','auto_comedia,auto_force_port','comedia,force_port','never','route']})
trunkKeys.update({'type':['friend','peer','user']})
trunkKeys.update({'directmedia':['no','yes','nonat','ongoing','update']})
trunkKeys.update({'allow':['alaw','ulaw','gsm','g729','ilbc','speex','g726','adpcm']})
trunkKeys.update({'dtmfmode':['auto','inband','info','rfc2833','shortinfo']})
trunkKeys.update({'canreinvite':['yes','no']})
trunkDefaultKeys={'username':'null'}
trunkDefaultKeys.update()
trunkDefaultKeys={'username':'null'}
trunkDefaultKeys.update({'fromuser':'null'})
trunkDefaultKeys.update({'secret':'null'})
trunkDefaultKeys.update({'host':'dynamic'})
trunkDefaultKeys.update({'fromdomain':'null'})
trunkDefaultKeys.update({'callbackextension':'null'})
trunkDefaultKeys.update({'type':'friend'})
trunkDefaultKeys.update({'nat':'no'})
trunkDefaultKeys.update({'directmedia':'no'})
trunkDefaultKeys.update({'allow':'alaw;ulaw'})
trunkDefaultKeys.update({'dtmfmode':'rfc2833'})
trunkDefaultKeys.update({'canreinvite':'yes'})


def validParam(ID,ID_name,min,max,ws):
    er=dict()
    if (len(ID)>max): er.update({ID_name:'parameter lenght more'+ str(max)+ ' symbols'})
    if (len(ID)<min): er.update({ID_name:'parameter lenght less'+ str(min)+ ' symbols'})
    for s in ID: 
        if (s in ws):  
            er.update({ID_name: 'wrong sighn \''+ s +'\' in parameter'})
    return er
def get_Trunks(TM_ID,Trunk_ID):
    er=[]
    if (Trunk_ID==None) : args = (TM_ID,None)
    else : 
        er = validParam(Trunk_ID,"Trunk_ID",0,65,wrongSigns)
        if(len(er)>0): 
            args = (TM_ID,None)
        args = (TM_ID,Trunk_ID)
    cursor.callproc('get_trunks',args)
    r = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in cursor.fetchall()]
    return {'Trunks' : r,'Warnings' : er}
def exists_trunk(name):
    cursor.callproc('exists_trunk',(name,))
    if (cursor._rows[0][0]==1): return True
    else: return False

@auth.get_password
def get_password(username):
    if username in users:
        return users.get(username)
    return None

@auth.error_handler
def unauthorized():
    return jsonify({'error': 'Unauthorized access'})

@app.route('/asterisk/v_01/Teams/<TM_ID>/phones',methods=['GET', 'POST'])
@app.route('/asterisk/v_01/Teams/<TM_ID>/phones/',methods=['GET', 'POST'])
@app.route('/asterisk/v_01/Teams/<TM_ID>/phones/<PH_ID>',methods=['GET', 'POST'])
@auth.login_required
def phones(TM_ID, PH_ID=None):
    if (PH_ID==None):
        sql = 'call asterisk_log.get_phones(\"'+TM_ID+'\");'
    else:
        sql = 'call asterisk_log.get_phone(\"'+TM_ID+'\",\"'+PH_ID+'\");'
    cur = mysql.connect().cursor()
    cur.execute(sql)
    r = [dict((cur.description[i][0], value)
            for i, value in enumerate(row)) for row in cur.fetchall()]
    return jsonify({'Phones' : r})

@app.route('/asterisk/v_01/Team',methods=['GET', 'POST'])
@app.route('/asterisk/v_01/Team/',methods=['GET', 'POST'])
@app.route('/asterisk/v_01/Team/<TM_ID>',methods=['GET', 'POST'])
@auth.login_required
def Team(TM_ID=None):
#check if TM_ID is present and have right lenght
    if (TM_ID==None):
         return jsonify({'Errors':{'TM_ID': 'parametr is missing'}})
    er = validParam(TM_ID,"TeamID",4,20,wrongSigns)
    if(len(er)>0): return  jsonify({'Error':er})
#GET request
    if request.method == 'GET':
        sql = 'call asterisk_log.get_Team(\"'+TM_ID+'\");'
        cursor.execute(sql)
        r = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in cursor.fetchall()]
        return jsonify({'Teams' : r})
#POSt request 
    if request.method == 'POST':
        if not request.json:
            return jsonify({'error': 'Not JSON Format'})
        wr=[]
        team_result=dict()
        team=request.json
#Validation of Json request
#Check if prefix and if its present
        if ("Prefix" in team):
            er=validParam(team["Prefix"],"Prefix",4,8,wrongSigns)
            if(len(er)>0): return  jsonify({'Error' : er})
            team_result.update({"Prefix":team["Prefix"]})
        else:
            return jsonify({'Errors':{'Prefix':'parameter is missing'}})
#Validation of all parameters, if warning Ignore parameter. This option will not be changed with request. Lowercase parameters
        for key in teamPropKeys:
            if key in team:
                if (team[key].lower() not in teamPropStatus):
                    wr.append({key:'warning: wrong parameter, should be \'On\' or \'Off\''})
                    team_result.update({key:'null'})
                else:
                    team_result.update({key:team[key].lower()})
            else: 
                wr.append({key:'warning: missing parameter'})
                team_result.update({key:'null'})
#Form sql request with converted parameters to true, false or null
        sql = "call `asterisk_log`.`set_Team`(\'"+TM_ID+"\',\'"+team_result["Prefix"]+"\',"+teamPropMap[team_result["Global_Routing"]]+","+teamPropMap[team_result["Local_Routing"]]+","+teamPropMap[team_result["Local_Listening"]]+","+teamPropMap[team_result["Local_Wispering"]]+","+teamPropMap[team_result["Local_Conference"]]+");"
        cursor.execute(sql)
        r = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in cursor.fetchall()]
        conn.commit()
        return jsonify({"Teams":r,'Warnings':wr})



@app.route('/asterisk/v_01/Team/<TM_ID>/Trunk',methods=['GET', 'POST', 'DELETE'])
@app.route('/asterisk/v_01/Team/<TM_ID>/Trunk/',methods=['GET', 'POST', 'DELETE'])
@app.route('/asterisk/v_01/Team/<TM_ID>/Trunk/<Trunk_ID>',methods=['GET', 'POST', 'DELETE'])
@auth.login_required
def Trunk(TM_ID=None,Trunk_ID=None):
#check if TM_ID is present and have right lenght
    wr=[]
    er = validParam(TM_ID,"TeamID",4,20,wrongSigns)
    if(len(er)>0): return  jsonify({'Error' : er})
    if (Trunk_ID != None):
        er=validParam(Trunk_ID,'Trunk_ID',4,20,wrongSigns)
        if(len(er)>0): return  jsonify({'Error' : er})
#GET request
    if request.method == 'GET':
        return jsonify(get_Trunks(TM_ID,Trunk_ID))
#POSt request 
    if request.method == 'POST':
        if not request.json:
            return jsonify({'error': 'Not JSON Format'})
        trunk_result=dict()
        trunk=request.json
#Validation of Json request
#Check if prefix > 4 lenght and its present
        if (Trunk_ID == None):  
            if 'host' not in trunk : return  jsonify({'Error' : {'host':'error:parameter \'host\' not present'}})                             
            if 'username' not in trunk : return  jsonify({'Error' : {'username':'error:parameter \'username\' not present'}})                             
        else:
            if(exists_trunk(Trunk_ID)==0): return  jsonify({'Error' : {Trunk_ID:'Can\'t find trunk  in team \''+ TM_ID+'\' to update it'}})
            trunkDefaultKeys=get_Trunks(TM_ID,Trunk_ID)['Trunks'][0]
#Validation of all parameters
        for key in trunkKeys:
            if key in trunk:
#if not string parametr 
                if (len(trunkKeys[key])>0):
#if allow checking is different
                    if(key is 'allow'):
                        for codec in trunk[key].split(';'):
                            if (codec.lower() not in trunkKeys[key]):
                                wr.append({key:'warning: wrong parameter'})
                        if key in wr: trunk_result.update({key:trunkDefaultKeys[key].lower()})
                        else: trunk_result.update({key:trunk[key].lower()})
#check other params
                    elif (trunk[key].lower() not in trunkKeys[key]):
                        wr.append({key:'warning: wrong parameter'})
                        trunk_result.update({key:trunkDefaultKeys[key].lower()})
                    else: trunk_result.update({key:trunk[key].lower()})
 #check if string parametr
                else:
                    if(key is 'host' or key is 'username' ):
                        if len(trunk[key])==0 : return  jsonify({'Error' : {key:'error:parameter\''+ key + '\' is empty'}})
                        er=validParam(key,trunk[key],2,255,', ~`!@#$%^&*()[]{}\\|=+')
                        if(len(er)>0):wr.extend(er)
                        trunk_result.update({key:trunk[key]})
                    elif(key is 'fromdomain' or key is 'fromuser'):
                        er=validParam(key,trunk[key],2,255,', ~`!@#$%^&*()[]{}\\|=+')
                        if(len(er)>0): wr.extend(er)
                        trunk_result.update({key:trunk[key]})
                    elif(key is 'secret' ):
                        trunk_result.update({key:trunk[key]})
                    elif(key is 'name'):
                        if(exists_trunk(trunk[key]) and Trunk_ID==None): 
                            return  jsonify({'Error' : 'Trunk with name \''+trunk[key]+'\' already exist in system'})
                        trunk_result.update({key:trunk[key]})
                    trunk_result.update({key:trunk[key]})
            else: 
                wr.append({key:'warning: missing parameter'})
                trunk_result.update({key:trunkDefaultKeys[key]})
#Form sql request with converted parameters to true, false or null
        if Trunk_ID == None: 
            args = (TM_ID,trunk_result['name'],trunk_result['username'],trunk_result['fromuser'],trunk_result['secret'],trunk_result['host'],trunk_result['fromdomain'],trunk_result['callbackextension'],trunk_result['nat'],trunk_result['type'],trunk_result['directmedia'],trunk_result['allow'],trunk_result['dtmfmode'],trunk_result['canreinvite'])
            cursor.callproc('add_trunk',args)
        else: 
            args = (TM_ID,Trunk_ID,trunk_result['name'],trunk_result['username'],trunk_result['fromuser'],trunk_result['secret'],trunk_result['host'],trunk_result['fromdomain'],trunk_result['callbackextension'],trunk_result['nat'],trunk_result['type'],trunk_result['directmedia'],trunk_result['allow'],trunk_result['dtmfmode'],trunk_result['canreinvite'])
            cursor.callproc('update_trunk',args) 
        r = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in cursor.fetchall()]
        conn.commit()
        return jsonify({'Trunks' : r,'Warnings' : wr})
    if request.method == 'DELETE':
        if (Trunk_ID == None):  return  jsonify({'Error' : {'Trunk_ID':'error:Nothing to delete'}})        
        if (exists_trunk(Trunk_ID)==0): return  jsonify({'Error' : {'Trunk_ID':'Trunk \''+ TM_ID+'\'  is not exist. Nothing to delete'}})
        cursor.callproc('remove_trunk',(Trunk_ID,))
        conn.commit()
        if (exists_trunk(Trunk_ID)==0): return jsonify({'Warning' : {'Trunk_ID':'Trunk \''+ TM_ID+'\' was deleted'}})
        else: return jsonify({'Error' : {Trunk_ID:'Trunk \''+ TM_ID+'\' was not deleted probably mistake'}})

    
@app.route('/asterisk/v_01/Team/<TM_ID>/Route',methods=['GET', 'POST', 'DELETE'])
@app.route('/asterisk/v_01/Team/<TM_ID>/Route/',methods=['GET', 'POST', 'DELETE'])
@app.route('/asterisk/v_01/Team/<TM_ID>/Route/<Route_ID>',methods=['GET', 'POST', 'DELETE'])
@app.route('/asterisk/v_01/Team/<TM_ID>/Route/<Route_ID>/',methods=['GET', 'POST', 'DELETE'])
@auth.login_required
def Tunk(TM_ID=None,Route_ID=None):
    wr=[]
    er = validParam(TM_ID,"TeamID",4,20,wrongSigns)
    if(len(er)>0): return  jsonify({'Error' : er})
    if Route_ID is not None: 
        if len(Route_ID)==2:
            if(Route_ID[0] not in digits or Route_ID[0] not in digits):
                return jsonify({'Route_ID' : 'error: parameter should be in format \'XX\' where X is digit'}) 
        else: return jsonify({'Route_ID' : 'error: parameter should be in format \'XX\' where X is digit'}) 
    if request.method == 'GET':
        if 'destination' in request.args:  dest=request.args['destination']
        else: dest = None
        cursor.callproc('get_route',(TM_ID,Route_ID,dest))
        r = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in cursor.fetchall()]
        return jsonify({'Routies' : r,'Warnings' : wr})
    if request.method == 'POST':
        if Route_ID is None : return jsonify({'Route_ID': 'error:No Route_ID present to add route'})     
        if not request.json : return jsonify({'error': 'error:Not JSON Format'})
        route_result=dict()
        route=request.json
        if 'name' in route:
            if len(get_Trunks(TM_ID,route['name'])['Trunks'])==0 :
                 return jsonify({'name' : 'error:Cant\'t find trunk\''+route['name']+'\'for Team \''+TM_ID+'\''})
            else: route_result.update({'name':route['name']})
        else : return jsonify({'name' : 'error: No trunk to setup in route'})
        if 'destination' in route:
            for s in route['destination']:
                if s not in digits: return jsonify({'route_dest' : 'Route destination should be in number format'})
            else: route_result.update({'destination':route['destination']})        
        else : route_result.update({'destination':''})
        if 'Caller_ID' in route:
            for s in route['Caller_ID']:
                if s not in digits: return jsonify({'Caller_ID' : 'Caller_ID destination should be in number format'})
            else: route_result.update({'Caller_ID':route['Caller_ID']})        
        else : route_result.update({'Caller_ID':None})
        cursor.callproc('set_route',(TM_ID,Route_ID,route_result['name'],route_result['destination'],route_result['Caller_ID']))
        conn.commit()
        r = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in cursor.fetchall()]
        return jsonify({'Routies' : r,'Warnings' : wr})
    if request.method == 'DELETE':
        if 'destination' in request.args:  
            for s in request.args['destination']:
                if s not in digits: return jsonify({'route_dest' : 'Route destination should be in number format'})
            else: dest=request.args['destination']
        else: dest = None
        cursor.callproc('remove_route',(TM_ID,Route_ID,dest))
        conn.commit()
        r = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in cursor.fetchall()]
        return jsonify({'Routies' : r,'Warnings' : wr})

if __name__ == '__main__':
#    app.run(host='0.0.0.0',port='5002')
    app.run()




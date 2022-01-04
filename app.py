#coding=utf-8
from flask import Flask,render_template,request,url_for,redirect,session,Response,g
from flask.json import jsonify
from flask_wtf import file
from forms import UserForms,StudentsInfoForms,SearchIdForms,RegisterForms,UploadFileForms
from werkzeug.utils import  secure_filename
from config import DataBaseConfig,Config
from models import User,Books
from decorator import login_required,routing_permission_check,get_hash_value
import os
import xlrd
import time
from dbs import db
import random
import zipfile

#初始化
app = Flask(__name__)
app.config.from_object(DataBaseConfig)
app.config.from_object(Config)
db.init_app(app)
#自定义一个全局变量
BOOK_NAME = []
BOOK_TYPE = []

#创建数据表
#db.create_all(app=app)

#跳转到主页或登录页
@app.route('/',methods = ['POST','GET'])
def index():
    if 'user_id' in session:
       return redirect('home') 
    else:
        return redirect('login')

#用户注册
@app.route('/register',methods = ['POST','GET'])
def register():
    form = RegisterForms()
    if request.method == 'GET':
        return render_template('register.html',form = form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            user=request.form['username']
            passw=request.form['password'] 
            user = str(user)
            passw = str(passw)
            if not User.query.filter_by(username = user).first():
                try:
                    username = user
                    salt = str(time.time())
                    hash_pwd = get_hash_value(passw,salt)
                    add_time = time.strftime('%Y-%m-%d %H:%M:%S')
                    group_id = 2
                    data = User(username,hash_pwd,salt,group_id,add_time)
                    db.session.add(data)
                    db.session.commit()
                    message = 'Sign up: '+ user + ' SUCCESS!'
                    dic2 = {'title':'SUCCESS!','message':message,'frame_type':'alert alert-success alert-dismissable'}
                    return render_template('register.html',form = form,dic2 = dic2)
                except:
                    db.session.rollback()
                    message = 'Sign up: '+ user + ' ERROR!'
                    dic2 = {'title':'ERROR!','message':message,'frame_type':'alert alert-dismissable alert-danger'}
                    return render_template('register.html',form = form,dic2 = dic2)
                finally:
                    db.session.close()
                
            else:
                dic1 = {'title':'fail','message':'The user name already exists, please do not re-register!'}
                return render_template('register.html',form = form,dic1 = dic1)
        else:
            
            return render_template('register.html',form = form) 

#用户登录
@app.route('/login',methods = ['POST','GET'])
def login():
    form = UserForms()
    if request.method == 'GET':
        return render_template('login.html',form = form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            user=request.form['username']
            passw=request.form['password'] 
            res = User.query.filter_by(username = user).first()
            #print(res.__dict__)
            if res:
                dict_user = res.__dict__
                #验证密码的哈希值
                new_pwd = get_hash_value(passw,dict_user['salt'])
                if new_pwd == dict_user['hash_pwd']:
                    #验证通过
                    session['user_id'] = user
                    #return 'Login OK!'
                    return redirect(url_for('home'))
                else:
                    dic1 = {'title':'error','message':'Incorrect password or user does not exist!'}
                    return render_template('login.html',form =form,dic1 =dic1)
            else:
                dic1 = {'title':'error','message':'Incorrect password or user does not exist!'}
                return render_template('login.html',form =form,dic1 =dic1)
        else:
            return render_template('login.html',form = form)

#退出登录
@app.route('/logout',methods = ['POST','GET'])
@login_required
def logout():
    if 'user_id' in session:
        session.pop('user_id')
    return redirect('login')

#用户主页
@app.route("/home",methods = ['POST','GET'])
@login_required
@routing_permission_check
def home():
    form = SearchIdForms()
    username = session.get('user_id')
    dic1 = {'username':username,'active1':'active','active2':'','active3':'','active4':'','active5':'','current_page_number':1}
    #查询book表中的所有数据
    book_info = Books.query.limit(5).all()
    if len(book_info) ==0:
        book_info_list=[]
    else:
        #print(book_info)
        book_info_list = []
        for i in book_info:
            book_info_list.append(i.__dict__)
        for j in book_info_list:
            del j['_sa_instance_state']
            del j['add_book_time']
            del j['book_file_name']
        style_list = ['success','info','warning','error','']
        for dict_data in book_info_list:
            style_value = random.choice(style_list)
            dict_data['style'] = style_value
    return render_template('home.html',form = form,dic1 = dic1,list1 = book_info_list)

#主页中的书本表格翻页
@app.route("/home/page/<int:number>",methods = ['POST','GET'])
@login_required
@routing_permission_check
def home_page(number):
    form = SearchIdForms()
    if request.method =='GET':
        if number == 1:
            return redirect('home')
        username = session.get('user_id')
        dic1 = {'username':username,'active1':'','active2':'','active3':'','active4':'','active5':'','active_next':'','active_Prev':'','current_page_number':number}
        if 1<=number<=5:
            dic1['active'+str(number)] = 'active'
        elif number>5:
            dic1['active_next'] = 'active'
        # else:
        #     dic1['active_Prev'] = 'active'
        #根据传入的页码查询第几条到第几条.offset(10).limit(10).all()
        offset_num = (int(number)-1)*5
        limit_num = 5
        book_info = Books.query.offset(offset_num).limit(limit_num).all()
        if len(book_info) ==0:
            book_info_list=[]
        else:
            #print(book_info)
            book_info_list = []
            for i in book_info:
                book_info_list.append(i.__dict__)
            for j in book_info_list:
                del j['_sa_instance_state']
                del j['add_book_time']
                del j['book_file_name']
            style_list = ['success','info','warning','error','']
            for dict_data in book_info_list:
                style_value = random.choice(style_list)
                dict_data['style'] = style_value   
        return render_template('home.html',form = form,dic1 = dic1,list1 = book_info_list)
    
#home页面的查询翻页
@app.route("/home/search/<int:number>",methods = ['POST','GET'])
@login_required
@routing_permission_check
def search_books(number):
    form = SearchIdForms()
    if request.method =='POST':
        if form.validate_on_submit():
            book_name = str(request.form['book_name'])
            BOOK_NAME.append(book_name)
            username = session.get('user_id')
            dic1 = {'username':username,'active1':'','active2':'','active3':'','active4':'','active5':'','active_next':'','active_Prev':'','current_page_number':number,'errors':''}
            if 1<=number<=5:
                dic1['active'+str(number)] = 'active'
            elif number>5:
                dic1['active_next'] = 'active'
            offset_num = (int(number)-1)*5
            limit_num = 5
            book_info = Books.query.filter_by(book_name = book_name).offset(offset_num).limit(limit_num).all() 
            if len(book_info) ==0:
                book_info_list=[]
            else:
                #print(book_info)
                book_info_list = []
                for i in book_info:
                    book_info_list.append(i.__dict__)
                for j in book_info_list:
                    del j['_sa_instance_state']
                    del j['add_book_time']
                    del j['book_file_name']
                style_list = ['success','info','warning','error','']
                for dict_data in book_info_list:
                    style_value = random.choice(style_list)
                    dict_data['style'] = style_value
                # print(BOOK_NAME) 
            return render_template('home_search.html',form = form,dic1 = dic1,list1 = book_info_list)
        else:
            #未通过表单校验
            form = SearchIdForms()
            username = session.get('user_id')
            dic1 = {'username':username,'active1':'active','active2':'','active3':'','active4':'','active5':'','current_page_number':1,'errors':'bookname can not be empty!'}
            #查询book表中的所有数据
            book_info = Books.query.limit(5).all()
            if len(book_info) ==0:
                book_info_list=[]
            else:
                #print(book_info)
                book_info_list = []
                for i in book_info:
                    book_info_list.append(i.__dict__)
                for j in book_info_list:
                    del j['_sa_instance_state']
                    del j['add_book_time']
                    del j['book_file_name']
                style_list = ['success','info','warning','error','']
                for dict_data in book_info_list:
                    style_value = random.choice(style_list)
                    dict_data['style'] = style_value
            return render_template('home.html',form = form,dic1 = dic1,list1 = book_info_list)
    elif request.method == 'GET':
        #查询翻页请求
        username = session.get('user_id')
        dic1 = {'username':username,'active1':'','active2':'','active3':'','active4':'','active5':'','active_next':'','active_Prev':'','current_page_number':number,'errors':''}
        if 1<=number<=5:
            dic1['active'+str(number)] = 'active'
        elif number>5:
            dic1['active_next'] = 'active'
        offset_num = (int(number)-1)*5
        limit_num = 5
        #print(BOOK_NAME)
        name = BOOK_NAME[-1]
        book_info = Books.query.filter_by(book_name = name).offset(offset_num).limit(limit_num).all() 
        if len(book_info) ==0:
            book_info_list=[]
        else:
            book_info_list = []
            for i in book_info:
                book_info_list.append(i.__dict__)
            for j in book_info_list:
                del j['_sa_instance_state']
                del j['add_book_time']
                del j['book_file_name']
            style_list = ['success','info','warning','error','']
            for dict_data in book_info_list:
                style_value = random.choice(style_list)
                dict_data['style'] = style_value   
        return render_template('home_search.html',form = form,dic1 = dic1,list1 = book_info_list)

#按类型查询表格翻页
@app.route("/home/search/type/<type_1>/<int:number>",methods = ['POST','GET'])
@login_required
@routing_permission_check
def search_by_type(type_1,number):  
    form = SearchIdForms()
    type_1 = str(type_1)
    BOOK_TYPE.append(type_1) 
    username = session.get('user_id')
    dic1 = {'username':username,'active1':'','active2':'','active3':'','active4':'','active5':'','active_next':'','active_Prev':'','current_page_number':number,'errors':'','type':BOOK_TYPE[-1]}
    if 1<=number<=5:
        dic1['active'+str(number)] = 'active'
    elif number>5:
        dic1['active_next'] = 'active'
    offset_num = (int(number)-1)*5
    limit_num = 5
    book_info = Books.query.filter_by(book_type = type_1).offset(offset_num).limit(limit_num).all() 
    if len(book_info) ==0:
        book_info_list=[]
    else:
        #print(book_info)
        book_info_list = []
        for i in book_info:
            book_info_list.append(i.__dict__)
        for j in book_info_list:
            del j['_sa_instance_state']
            del j['add_book_time']
            del j['book_file_name']
        style_list = ['success','info','warning','error','']
        for dict_data in book_info_list:
            style_value = random.choice(style_list)
            dict_data['style'] = style_value  
    return render_template('home_search_type.html',form = form,dic1 = dic1,list1 = book_info_list)
          
# #管理
@app.route('/addStudents',methods = ['POST','GET'])
@login_required
@routing_permission_check
def addStudents():
    form = StudentsInfoForms()
    if request.method == 'GET':
        return render_template('addStudents.html',form = form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            #写入数据库
            #id name sex date nation height	idCard PhoneNumber address teacher hobbies
            try:
                id = request.form['id']
                name = request.form['name']
                sex = request.form['sex']
                date = request.form['date']
                nation = request.form['nation']
                height = request.form['height']
                idCard = request.form['idCard']
                PhoneNumber = request.form['PhoneNumber']
                address = request.form['address']
                teacher = request.form['teacher']
                hobbies = request.form['hobbies']
                db.session.add(studentsInfo(id ,name, sex, date, nation, height,idCard, PhoneNumber, address, teacher, hobbies))
                db.session.commit()
                dic1 = {'title':'success','message':'导入成功!'}
                return render_template('info.html',dic1 = dic1)
            except:
                db.session.rollback()
                dic1 = {'title':'error','message':'导入失败!'}
                return render_template('info.html',dic1 = dic1)
            finally:
                db.session.close()
        else:
            return render_template('addStudents.html',form = form)

# #批量导入学生信息
@app.route('/upload',methods = ['POST','GET'])
@login_required
@routing_permission_check
def upload():
    form = UploadFileForms()
    if request.method == 'POST':
        if form.validate_on_submit():
            #通过表单验证
            f = request.files['file']
            file_extension = str(f.filename).split('.')[1]
            file_name = str(time.time()).replace('.','') + '.' + file_extension
            f.save(os.getcwd()+'\\Temp\\'+secure_filename(file_name))
            #打开文件
            if '.xlsx'  in file_name or '.xls' in file_name :
                table_head = ['学号','姓名','性别','出生年月','民族','身高','身份证号码','家长电话','家庭住址','班主任','兴趣爱好']
                work_book = xlrd.open_workbook(os.getcwd()+'\\Temp\\'+file_name)
                work_sheet = work_book.sheet_by_name('Sheet1')
                data_list = []
                if work_sheet.row_values(0) == table_head:
                    try:
                        for i in range(1,work_sheet.nrows):
                            excelData = work_sheet.row_values(i)
                            id,name,sex,date,nation,height,idCard,PhoneNumber,address,teacher,hobbies = excelData
                            data_list.append(studentsInfo(id,name,sex,date,nation,height,idCard,PhoneNumber,address,teacher,hobbies))
                        db.session.add_all( data_list)
                        db.session. commit()
                    except:
                        db.session.rollback()
                        dic1 = {'title':'SQLerror','message':'导入SQL失败!'}
                        return render_template('info.html',dic1 = dic1)
                        
                    else:
                        dic1 = {'title':'success','message':'导入SQL成功!'}
                        return render_template('info.html',dic1 = dic1)
                    finally:
                        db.session.close()
                        #xlrd 1.2 版本的workbook 没有close方法
                        work_book.release_resources()
                        #os.remove(os.getcwd()+'\\Temp\\'+file_name)
                else:
                    dic1 = {'title':'error','message':'excel文件数据错误，请检查excel文件!'}
                    return render_template('info.html',dic1 = dic1)
            else:
                dic1 = {'title':'error','message':'excel文件传输错误!'}
                return render_template('info.html',dic1 = dic1)
                
        else:
            return render_template('upload.html',form = form)
    elif request.method == 'GET':
        return render_template('upload.html',form = form)

# #批量导入用户
@app.route('/uploadUser',methods = ['POST','GET'])
@login_required
@routing_permission_check
def uploadUser():
    form = UploadFileForms()
    if request.method == 'POST':
        if form.validate_on_submit():
            #通过表单验证
            f = request.files['file']
            file_extension = str(f.filename).split('.')[1]
            file_name = str(time.time()).replace('.','') + '.' + file_extension
            f.save(os.getcwd()+'\\Temp\\'+secure_filename(file_name))
            #打开文件
            if '.xlsx'  in file_name or '.xls' in file_name :
                table_head = ['用户名','密码']
                work_book = xlrd.open_workbook(os.getcwd()+'\\Temp\\'+file_name)
                work_sheet = work_book.sheet_by_name('Sheet1')
                data_list = []
                if work_sheet.row_values(0) == table_head:
                    try:
                        for i in range(1,work_sheet.nrows):
                            time.sleep(0.001)
                            excelData = work_sheet.row_values(i)
                            username,password = excelData
                            time_salt = time.time()
                            salt = str(time_salt)
                            hash_pwd = get_hash_value(password,salt + '@@')
                            data_list.append(userInfo(username = str(username),hash_pwd= hash_pwd,salt = salt))
                            #data_list.append((username,hash_pwd,salt))
                        
                        db.session.add_all(data_list)
                        db.session.commit()
                    except:
                        db.session.rollback()
                        dic1 = {'title':'SQLerror','message':'导入SQL失败！'}
                        return render_template('info.html',dic1 = dic1)
                        
                    else:
                        dic1 = {'title':'success','message':'导入SQL成功！'}
                        return render_template('info.html',dic1 = dic1)
                    finally:
                        db.session.close()
                        #xlrd 1.2 版本的workbook 没有close方法
                        work_book.release_resources()
                        #os.remove(os.getcwd()+'\\Temp\\'+file_name)
                else:
                    dic1 = {'title':'error','message':'excel文件数据错误，请检查excel文件！'}
                    return render_template('info.html',dic1 = dic1)
            else:
                dic1 = {'title':'error','message':'excel文件传输错误！'}
                return render_template('info.html',dic1 = dic1)
        else:
            return render_template('uploadUser.html',form = form)
    elif request.method == 'GET':
        return render_template('uploadUser.html',form = form)
       
# # #查询
# @app.route('/home',methods = ['POST','GET'])
# @login_required
# def home2():
#     form2 = SearchIdForms()
#     if request.method == 'GET':
#         return render_template('home.html',form = form2)
#     elif request.method == 'POST':
#         if form2.validate_on_submit():
#             searchId = request.form['searchId']
#             if str.isdigit(searchId):
#                 data = studentsInfo.query.filter_by(id = searchId).all()
#                 #print(type(data))
#                 if len(data) == 1: 
#                     dic2 = data[0].__dict__
#                     return render_template('data.html',dic = dic2)
#                 else:
#                     dic1 = {'title':'fail','message':'查询错误！'}
#                     return render_template('info.html',dic1 = dic1)
#             else:
#                 data = studentsInfo.query.filter_by(name = searchId).first()
                
#                 if data:
#                     dic2 = data.__dict__
#                     return render_template('data.html',dic = dic2)
#                 else:
#                     #未查询到数据，报错
#                     dic1 = {'title':'fail','message':'查询错误！'}
#                     return render_template('info.html',dic1 = dic1)       
#         else:
#             return render_template('home.html',form = form2)

#管理页面
@app.route('/management',methods = ['POST','GET'])
@login_required
@routing_permission_check
def management():
    return render_template('management.html')

#管理界面用户管理
@app.route("/management/user",methods = ['POST','GET'])
@login_required
@routing_permission_check
def user_mgr():
    form = UploadFileForms()
    if request.method == 'GET':
        #查询用户数据
        dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'','active_next':'','active_Prev':'','current_page_number':1}
        #根据参数查询用户数据，一次10条
        user_info = User.query.limit(10).all()
        user_list = []
        if len(user_info) ==0:
            user_list = []
        else:
            for userdata in user_info:
                user_list.append( userdata.__dict__)
            k = 0
            style_list = ['success','info','warning','error','']
            for j in user_list:
                k+=1
                #删除多余的字段
                del j['_sa_instance_state']
                del j['hash_pwd']
                del j['salt']
                #增加一个id字段
                j['id'] = k
                #根据group id 改写数据为不同的角色组
                if j['group_id'] ==1:
                    del j['group_id']
                    j['group'] = 'admin'
                elif j['group_id'] == 2:
                    del j['group_id']
                    j['group'] = 'others'
                #为表格加随机样式
                j['style'] = random.choice(style_list)
        return render_template('user.html',user_list = user_list,dic1 = dic1,form = form)

#管理界面用户管理翻页
@app.route("/management/user/page/<int:number>",methods = ['POST','GET'])
@login_required
#@routing_permission_check
def user_page(number):
    form = UploadFileForms()
    if request.method == 'GET':
        #查询用户数据
        dic1 = {'active1':'','active2':'','active3':'','active4':'','active5':'','active_next':'','active_Prev':'','current_page_number':number}
        if 1<=number<=5:
            dic1['active'+str(number)] = 'active'
        elif number>5:
            dic1['active_next'] = 'active'
        # else:
        #     dic1['active_Prev'] = 'active'
        #根据参数查询用户数据，一次10条
        offset_num = (int(number)-1)*10
        limit_num = 10
        user_info = User.query.offset(offset_num).limit(limit_num).all()
        #user_info = User.query.limit(10).all()
        user_list = []
        if len(user_info) ==0:
            user_list = []
        else:
            for userdata in user_info:
                user_list.append( userdata.__dict__)
            k = 0
            style_list = ['success','info','warning','error','']
            for j in user_list:
                k+=1
                #删除多余的字段
                del j['_sa_instance_state']
                del j['hash_pwd']
                del j['salt']
                #增加一个id字段
                j['id'] = k
                #根据group id 改写数据为不同的角色组
                if j['group_id'] ==1:
                    del j['group_id']
                    j['group'] = 'admin'
                elif j['group_id'] == 2:
                    del j['group_id']
                    j['group'] = 'others'
                #为表格加随机样式
                j['style'] = random.choice(style_list)
        return render_template('user.html',user_list = user_list,dic1 = dic1,form = form)

#管理界面用户管理 ：修改用户组(admin切换成others，others切换成admin)
@app.route("/management/user/changegroup/<username>/<group>/",methods = ['POST','GET'])
@login_required
@routing_permission_check
def change_group(username,group):
    if group == 'admin':
        #修改为others
        user_data = User.query.filter(User.username == username).first()
        if user_data:
            user_data.group_id = 2
            db.session.commit()
            return redirect('/management/user')
        else:
            return 'no data'
    elif group == 'others':
        user_data = User.query.filter(User.username == username).first()
        if user_data:
            user_data.group_id = 1
            db.session.commit()
            return redirect('/management/user')
        else:
            return 'no data'

#管理界面用户管理 ：删除指定用户
@app.route("/management/user/delete/<username>",methods = ['POST','GET'])
@login_required
@routing_permission_check
def delete_user(username):
    user_data = User.query.filter(User.username == username).first()
    if user_data:
        db.session.delete(user_data)
        db.session.commit()
        return redirect('/management/user')
    else:
        return 'no data'

#批量注册用户数据
@app.route("/management/user/addusers",methods = ['POST','GET'])
@login_required
#@routing_permission_check
def add_users():
    form = UploadFileForms()
    if request.method == 'GET':
        dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'','active_next':'','active_Prev':'','current_page_number':1}
            #根据参数查询用户数据，一次10条
        user_info = User.query.limit(10).all()
        user_list = []
        if len(user_info) ==0:
            user_list = []
        else:
            for userdata in user_info:
                user_list.append( userdata.__dict__)
            k = 0
            style_list = ['success','info','warning','error','']
            for j in user_list:
                k+=1
                #删除多余的字段
                del j['_sa_instance_state']
                del j['hash_pwd']
                del j['salt']
                #增加一个id字段
                j['id'] = k
                #根据group id 改写数据为不同的角色组
                if j['group_id'] ==1:
                    del j['group_id']
                    j['group'] = 'admin'
                elif j['group_id'] == 2:
                    del j['group_id']
                    j['group'] = 'others'
                #为表格加随机样式
                j['style'] = random.choice(style_list)
        return render_template('user.html',form = form,user_list = user_list,dic1 = dic1)
    elif request.method =='POST':
        if form.validate_on_submit():
            #通过表单验证
            f = request.files['file']
            file_name = str(time.time())+f.filename
            file_path = os.getcwd() + os.path.join(os.sep,'media',file_name).replace(file_name,'')
            f.save(file_path + secure_filename(file_name))
            #打开文件
            if '.xlsx'  in file_name or '.xls' in file_name :
                table_head = ['用户名','密码','用户组ID']
                work_book = xlrd.open_workbook(file_path + file_name)
                ws = work_book.sheet_by_name('Sheet1')
                msg_list = []
                if ws.row_values(0) == table_head:
                    for row in range(1,ws.nrows):
                        user1 = ws.cell_value(row,0)
                        pass1 = ws.cell_value(row,1)
                        group_id = ws.cell_value(row,2)
                        ctype =ws.cell(row,1).ctype
                        ctype = ws.cell(row,2).ctype
                        if ctype == 2:
                            pass1 = str(pass1).replace('.0','')
                        if ctype == 2:
                            group_id = int(str(group_id).replace('.0',''))
                        #print(user1,pass1,str(group_id))
                        if not User.query.filter(User.username == user1).first():
                            #用户名查重
                            try:
                                salt = str(time.time())
                                username = str(user1)
                                hash_pwd = get_hash_value(str(pass1),salt)
                                group_id = group_id
                                add_time = time.strftime('%Y-%m-%d %H:%M:%S')
                                db.session.add(User(username,hash_pwd,salt,group_id,add_time))
                                db.session.commit()
                                msg = 'user: ' +user1 +' import successful  '
                                msg_list.append(msg)
                            except:
                                db.session.rollback()
                                msg = 'user: ' +user1 +' import error!  '
                                msg_list.append(msg)
                        else:
                            msg = 'user: ' +user1 +' existing, failed to import!  '
                            msg_list.append(msg)
                    msgs = ''
                    for msg_info in msg_list:
                        msgs +=msg_info
                    if msgs == '':
                        message = 'EXCEL no data!'
                        style = 'alert alert-dismissable alert-danger'
                        title = 'Warning!  '
                    else:
                        message = msgs
                        style = 'alert alert-success alert-dismissable'
                        title = 'SUCCESS! '
                else:
                    message = 'File format error!'
                    style = 'alert alert-dismissable alert-danger'
                    title = 'Warning! '
            else:
                message = 'File type error!'
                style = 'alert alert-dismissable alert-danger'
                title = 'Warning! '
            #删除excel文件
            if os.path.isfile(file_path + file_name) ==True:
                os.remove(file_path + file_name)
            #返回对应的错误信息渲染页面
            dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'','active_next':'','active_Prev':'','current_page_number':1}
            dic1['message'] = message
            dic1['style'] = style
            dic1['title'] = title
            #根据参数查询用户数据，一次10条
            user_info = User.query.limit(10).all()
            user_list = []
            if len(user_info) ==0:
                user_list = []
            else:
                for userdata in user_info:
                    user_list.append( userdata.__dict__)
                k = 0
                style_list = ['success','info','warning','error','']
                for j in user_list:
                    k+=1
                    #删除多余的字段
                    del j['_sa_instance_state']
                    del j['hash_pwd']
                    del j['salt']
                    #增加一个id字段
                    j['id'] = k
                    #根据group id 改写数据为不同的角色组
                    if j['group_id'] ==1:
                        del j['group_id']
                        j['group'] = 'admin'
                    elif j['group_id'] == 2:
                        del j['group_id']
                        j['group'] = 'others'
                    #为表格加随机样式
                    j['style'] = random.choice(style_list)
            return render_template('user.html',form = form,user_list = user_list,dic1 = dic1)

        else:
            #未通过表单校验！
            dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'','active_next':'','active_Prev':'','current_page_number':1}
            #未通过表单校验将报错信息传入dic1
            if form.errors:
                message = ''
                for key,value in form.errors.items():
                    message = value
                dic1['message'] = str(message[0])
                dic1['style'] = 'alert alert-dismissable alert-danger'
                dic1['title'] = 'Warning!  '
            #根据参数查询用户数据，一次10条
            user_info = User.query.limit(10).all()
            user_list = []
            if len(user_info) ==0:
                user_list = []
            else:
                for userdata in user_info:
                    user_list.append( userdata.__dict__)
                k = 0
                style_list = ['success','info','warning','error','']
                for j in user_list:
                    k+=1
                    #删除多余的字段
                    del j['_sa_instance_state']
                    del j['hash_pwd']
                    del j['salt']
                    #增加一个id字段
                    j['id'] = k
                    #根据group id 改写数据为不同的角色组
                    if j['group_id'] ==1:
                        del j['group_id']
                        j['group'] = 'admin'
                    elif j['group_id'] == 2:
                        del j['group_id']
                        j['group'] = 'others'
                    #为表格加随机样式
                    j['style'] = random.choice(style_list)
            return render_template('user.html',form = form,user_list = user_list,dic1 = dic1)
                

#批量注册用户数据下载excel模板
@app.route("/management/user/addusers/download",methods = ['POST','GET'])
@login_required
#@routing_permission_check
def download_upload_user_template():
    file_name = 'template.zip'
    file_path = os.getcwd() + os.path.join(os.sep,'media',file_name )
    if os.path.isfile(file_path) == True:
        #打开指定文件准备传输
        #循环读取文件
        def sendfile(file_path):
            with open(file_path, 'rb') as targetfile:
                while True:
                    data = targetfile.read(20*1024*1024)
                    if not data:
                        break
                    yield data
        response = Response(sendfile(file_path), content_type='application/octet-stream')
        response.headers["Content-disposition"] = 'attachment; filename=%s' % file_name 
        return response
    else:  
        return jsonify({'code':404,'message':'Unable to find resources'})

#管理界面书本管理
@app.route("/management/book",methods = ['POST','GET'])
@login_required
@routing_permission_check
def book_page():
    return render_template('book.html')

#管理界面系统权限管理
@app.route("/management/system",methods = ['POST','GET'])
@login_required
@routing_permission_check
def system_page():
    return render_template('system.html')

#书本下载
@app.route("/book/download/<int:id>",methods = ['POST','GET'])
@login_required
@routing_permission_check  
def download_book(id):
    #在window和linux上自动拼接为windows的 '\\' 或者linux的'/' 
    book_info = Books.query.filter(Books.id == int(id)).first()
    if book_info:
        file_name = str(book_info.book_file_name )
        #读取下载次数+1
        number1 = int(book_info.number_of_downloads)+1
        book_dir = os.getcwd() + os.path.join(os.sep,'media',file_name )
        #打开指定文件准备传输
        #循环读取文件
        def sendfile(file_path):
            with open(file_path, 'rb') as targetfile:
                while True:
                    data = targetfile.read(20*1024*1024)
                    if not data:
                        break
                    yield data
        response = Response(sendfile(book_dir), content_type='application/octet-stream')
        response.headers["Content-disposition"] = 'attachment; filename=%s' % file_name 
        #更新下载次数
        book_info.number_of_downloads = number1
        db.session.commit()
        return response
    else:  
        return jsonify({'code':404,'message':'Unable to find resources'})
        
if __name__ == '__main__':
    app.run(host = '0.0.0.0',port=5000,debug = True)

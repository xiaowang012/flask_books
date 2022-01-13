#coding=utf-8
from flask import Flask,render_template,request,url_for,redirect,session,Response,g,jsonify,abort
from forms import UserForms,RegisterForms,UploadFileForms,SearchBookForms,AddBooksForms,AddPermissionForms
from werkzeug.utils import secure_filename
from config import DataBaseConfig,Config
from models import User,Books,Permission,UserGroup
from decorator import login_required, routing_permission_check,get_hash_value,PERMISSION_DICT
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
#自定义一个全局变量,用于解决翻页问题
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
    if 'user_id' in session:
       return redirect('home')
    form = UserForms()
    if request.method == 'GET':
        return render_template('login.html',form = form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            user=request.form['username']
            passw=request.form['password'] 
            res = User.query.filter(User.username == user).first()
            if res:
                #验证登录密码的哈希值是否和数据库中的密码哈希值相等
                new_pwd = get_hash_value(passw,res.salt)
                if new_pwd == res.hash_pwd:
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
    form = SearchBookForms()
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
        style_list = ['success','info','warning','error']
        for dict_data in book_info_list:
            style_value = random.choice(style_list)
            dict_data['style'] = style_value
    return render_template('home.html',form = form,dic1 = dic1,list1 = book_info_list)

#主页中的书本表格翻页
@app.route("/home/page",methods = ['POST','GET'])
@login_required
@routing_permission_check
def home_page():
    number = request.args.get('number')
    try:
        number = int(number)
    except:
        return abort(404)
    else:
        form = SearchBookForms()
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
                style_list = ['success','info','warning','error']
                for dict_data in book_info_list:
                    style_value = random.choice(style_list)
                    dict_data['style'] = style_value   
            return render_template('home.html',form = form,dic1 = dic1,list1 = book_info_list)
    
#home页面的查询翻页
@app.route("/home/search/page",methods = ['POST','GET'])
@login_required
@routing_permission_check
def search_books():
    number = request.args.get('number')
    try:
        number = int(number)
    except:
        return abort(404)
    else:
        form = SearchBookForms()
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
                    style_list = ['success','info','warning','error']
                    for dict_data in book_info_list:
                        style_value = random.choice(style_list)
                        dict_data['style'] = style_value
                    # print(BOOK_NAME) 
                return render_template('home_search.html',form = form,dic1 = dic1,list1 = book_info_list)
            else:
                #未通过表单校验
                form = SearchBookForms()
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
                    style_list = ['success','info','warning','error']
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
                style_list = ['success','info','warning','error']
                for dict_data in book_info_list:
                    style_value = random.choice(style_list)
                    dict_data['style'] = style_value   
            return render_template('home_search.html',form = form,dic1 = dic1,list1 = book_info_list)

#按类型查询表格翻页
@app.route("/home/search/type",methods = ['POST','GET'])
@login_required
@routing_permission_check
def search_by_type():  
    type_1 = request.args.get('type_1')
    number = request.args.get('number')
    if type_1:
        try:
            number = int(number)
        except:
            return abort(404)
        else:
            form = SearchBookForms()
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
                style_list = ['success','info','warning','error']
                for dict_data in book_info_list:
                    style_value = random.choice(style_list)
                    dict_data['style'] = style_value  
            return render_template('home_search_type.html',form = form,dic1 = dic1,list1 = book_info_list)
    else:
        return abort(404) 

# #管理
# @app.route('/addStudents',methods = ['POST','GET'])
# @login_required
# @routing_permission_check
# def addStudents():
#     form = StudentsInfoForms()
#     if request.method == 'GET':
#         return render_template('addStudents.html',form = form)
#     elif request.method == 'POST':
#         if form.validate_on_submit():
#             #写入数据库
#             #id name sex date nation height	idCard PhoneNumber address teacher hobbies
#             try:
#                 id = request.form['id']
#                 name = request.form['name']
#                 sex = request.form['sex']
#                 date = request.form['date']
#                 nation = request.form['nation']
#                 height = request.form['height']
#                 idCard = request.form['idCard']
#                 PhoneNumber = request.form['PhoneNumber']
#                 address = request.form['address']
#                 teacher = request.form['teacher']
#                 hobbies = request.form['hobbies']
#                 db.session.add(studentsInfo(id ,name, sex, date, nation, height,idCard, PhoneNumber, address, teacher, hobbies))
#                 db.session.commit()
#                 dic1 = {'title':'success','message':'导入成功!'}
#                 return render_template('info.html',dic1 = dic1)
#             except:
#                 db.session.rollback()
#                 dic1 = {'title':'error','message':'导入失败!'}
#                 return render_template('info.html',dic1 = dic1)
#             finally:
#                 db.session.close()
#         else:
#             return render_template('addStudents.html',form = form)

# #批量导入学生信息
# @app.route('/upload',methods = ['POST','GET'])
# @login_required
# @routing_permission_check
# def upload():
#     form = UploadFileForms()
#     if request.method == 'POST':
#         if form.validate_on_submit():
#             #通过表单验证
#             f = request.files['file']
#             file_extension = str(f.filename).split('.')[1]
#             file_name = str(time.time()).replace('.','') + '.' + file_extension
#             f.save(os.getcwd()+'\\Temp\\'+secure_filename(file_name))
#             #打开文件
#             if '.xlsx'  in file_name or '.xls' in file_name :
#                 table_head = ['学号','姓名','性别','出生年月','民族','身高','身份证号码','家长电话','家庭住址','班主任','兴趣爱好']
#                 work_book = xlrd.open_workbook(os.getcwd()+'\\Temp\\'+file_name)
#                 work_sheet = work_book.sheet_by_name('Sheet1')
#                 data_list = []
#                 if work_sheet.row_values(0) == table_head:
#                     try:
#                         for i in range(1,work_sheet.nrows):
#                             excelData = work_sheet.row_values(i)
#                             id,name,sex,date,nation,height,idCard,PhoneNumber,address,teacher,hobbies = excelData
#                             data_list.append(studentsInfo(id,name,sex,date,nation,height,idCard,PhoneNumber,address,teacher,hobbies))
#                         db.session.add_all( data_list)
#                         db.session. commit()
#                     except:
#                         db.session.rollback()
#                         dic1 = {'title':'SQLerror','message':'导入SQL失败!'}
#                         return render_template('info.html',dic1 = dic1)
                        
#                     else:
#                         dic1 = {'title':'success','message':'导入SQL成功!'}
#                         return render_template('info.html',dic1 = dic1)
#                     finally:
#                         db.session.close()
#                         #xlrd 1.2 版本的workbook 没有close方法
#                         work_book.release_resources()
#                         #os.remove(os.getcwd()+'\\Temp\\'+file_name)
#                 else:
#                     dic1 = {'title':'error','message':'excel文件数据错误，请检查excel文件!'}
#                     return render_template('info.html',dic1 = dic1)
#             else:
#                 dic1 = {'title':'error','message':'excel文件传输错误!'}
#                 return render_template('info.html',dic1 = dic1)
                
#         else:
#             return render_template('upload.html',form = form)
#     elif request.method == 'GET':
#         return render_template('upload.html',form = form)

# # #批量导入用户
# @app.route('/uploadUser',methods = ['POST','GET'])
# @login_required
# @routing_permission_check
# def uploadUser():
    # form = UploadFileForms()
    # if request.method == 'POST':
    #     if form.validate_on_submit():
    #         #通过表单验证
    #         f = request.files['file']
    #         file_extension = str(f.filename).split('.')[1]
    #         file_name = str(time.time()).replace('.','') + '.' + file_extension
    #         f.save(os.getcwd()+'\\Temp\\'+secure_filename(file_name))
    #         #打开文件
    #         if '.xlsx'  in file_name or '.xls' in file_name :
    #             table_head = ['用户名','密码']
    #             work_book = xlrd.open_workbook(os.getcwd()+'\\Temp\\'+file_name)
    #             work_sheet = work_book.sheet_by_name('Sheet1')
    #             data_list = []
    #             if work_sheet.row_values(0) == table_head:
    #                 try:
    #                     for i in range(1,work_sheet.nrows):
    #                         time.sleep(0.001)
    #                         excelData = work_sheet.row_values(i)
    #                         username,password = excelData
    #                         time_salt = time.time()
    #                         salt = str(time_salt)
    #                         hash_pwd = get_hash_value(password,salt + '@@')
    #                         data_list.append(userInfo(username = str(username),hash_pwd= hash_pwd,salt = salt))
    #                         #data_list.append((username,hash_pwd,salt))
                        
    #                     db.session.add_all(data_list)
    #                     db.session.commit()
    #                 except:
    #                     db.session.rollback()
    #                     dic1 = {'title':'SQLerror','message':'导入SQL失败！'}
    #                     return render_template('info.html',dic1 = dic1)
                        
    #                 else:
    #                     dic1 = {'title':'success','message':'导入SQL成功！'}
    #                     return render_template('info.html',dic1 = dic1)
    #                 finally:
    #                     db.session.close()
    #                     #xlrd 1.2 版本的workbook 没有close方法
    #                     work_book.release_resources()
    #                     #os.remove(os.getcwd()+'\\Temp\\'+file_name)
    #             else:
    #                 dic1 = {'title':'error','message':'excel文件数据错误，请检查excel文件！'}
    #                 return render_template('info.html',dic1 = dic1)
    #         else:
    #             dic1 = {'title':'error','message':'excel文件传输错误！'}
    #             return render_template('info.html',dic1 = dic1)
    #     else:
    #         return render_template('uploadUser.html',form = form)
    # elif request.method == 'GET':
    #     return render_template('uploadUser.html',form = form)
       
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
        dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'',
                'active_next':'','active_Prev':'','current_page_number':1}
        #根据参数查询用户数据，一次10条
        user_info = User.query.limit(10).all()
        user_list = []
        if len(user_info) ==0:
            user_list = []
        else:
            for userdata in user_info:
                user_list.append( userdata.__dict__)
            k = 0
            style_list = ['success','info','warning','error']
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
@app.route("/management/user/page",methods = ['POST','GET'])
@login_required
@routing_permission_check
def user_page():
    number = request.args.get('number')
    try:
        number = int(number)
    except:
        return abort(404)
    else:
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
                style_list = ['success','info','warning','error']
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
@app.route("/management/user/changegroup",methods = ['POST','GET'])
@login_required
@routing_permission_check
def change_group():
    username = request.args.get('username')
    group = request.args.get('group')
    if username and group:
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
    else:
        return abort(404)

#管理界面用户管理 ：删除指定用户
@app.route("/management/user/delete",methods = ['POST','GET'])
@login_required
@routing_permission_check
def delete_user():
    username = request.args.get('username')
    if username:
        user_data = User.query.filter(User.username == username).first()
        if user_data:
            db.session.delete(user_data)
            db.session.commit()
            return redirect('/management/user')
        else:
            return abort(404)
    else:
        return abort(404)

#批量注册用户数据
@app.route("/management/user/addusers",methods = ['POST','GET'])
@login_required
@routing_permission_check
def add_users():
    form = UploadFileForms()
    if request.method =='GET':
        return abort(404)
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
            dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'',
                    'active_next':'','active_Prev':'','current_page_number':1}
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
                style_list = ['success','info','warning','error']
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
            dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'',
                    'active_next':'','active_Prev':'','current_page_number':1}
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
                style_list = ['success','info','warning','error']
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
                
#批量注册用户下载excel模板
@app.route("/management/user/addusers/download",methods = ['POST','GET'])
@login_required
@routing_permission_check
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

#刷新权限PERMISSION_DICT的值
@app.route("/management/refresh")
@login_required
@routing_permission_check
def refresh_permission():
    cur_url = request.args.get('cur_url')
    if cur_url:
        #更新权限表
        print(cur_url)
        user_group_list = []
        user_group_data = UserGroup.query.all()
        if user_group_data:
            for i in user_group_data:
                user_group_list.append( i.name)
            for j in user_group_list:
                result2 = Permission.query.filter(Permission.name == j).all()
                set1 = set()
                if result2:
                    for k in result2:
                        set1.add(k.url)
                    PERMISSION_DICT[j] = set1
                    #print(PERMISSION_DICT)
                    return redirect(cur_url)
                else:
                    return abort(404)
        else:
            return abort(404)
    else:
        return abort(404)

#书本下载
@app.route("/book/download",methods = ['POST','GET'])
@login_required
@routing_permission_check  
def download_book():
    id = request.args.get('code')
    try:
        id = int(id)
    except:
        return abort(404)
    else:
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
    
#管理界面书本管理
@app.route("/management/book",methods = ['POST','GET'])
@login_required
@routing_permission_check
def book_page():
    form = AddBooksForms()
    dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'','current_page_number':1}
    #查询book表中的所有数据
    book_info = Books.query.limit(10).all()
    if len(book_info) ==0:
        book_info_list=[]
    else:
        #print(book_info)
        book_info_list = []
        for i in book_info:
            book_info_list.append(i.__dict__)
        for j in book_info_list:
            del j['_sa_instance_state']
        style_list = ['success','info','warning','error']
        for dict_data in book_info_list:
            style_value = random.choice(style_list)
            dict_data['style'] = style_value
    return render_template('book.html',form = form,dic1 = dic1,list1 = book_info_list)

#管理界面书本管理页面翻页
@app.route('/management/book/page',methods = ['POST','GET'])
@login_required
@routing_permission_check
def book_mgr():
    number = request.args.get('number')
    try:
        number = int(number)
    except:
        return abort(404)
    else:
        form = UploadFileForms()
        #查询用户数据
        dic1 = {'active1':'','active2':'','active3':'','active4':'','active5':'',
                'active_next':'','active_Prev':'','current_page_number':number}
        if 1<=number<=5:
            dic1['active'+str(number)] = 'active'
        elif number>5:
            dic1['active_next'] = 'active'
        #根据参数查询用户数据，一次10条
        offset_num = (number-1)*10
        limit_num = 10
        book_info = Books.query.offset(offset_num).limit(limit_num).all()
        book_list = []
        if len(book_info) ==0:
            book_list = []
        else:
            for bookdata in book_info:
                book_list.append( bookdata.__dict__)
            k = 0
            style_list = ['success','info','warning','error']
            for j in book_list:
                k+=1
                #删除多余的字段
                del j['_sa_instance_state']
                #为表格加随机样式
                j['style'] = random.choice(style_list)
        return render_template('book.html',list1= book_list,dic1 = dic1,form = form)

#管理界面书本管理修改书本信息
@app.route("/management/book/update",methods = ['POST','GET'])
@login_required
@routing_permission_check
def update_book():
    form = AddBooksForms()
    if request.method == 'POST':
        id = request.form['id']
        book_name = request.form['bookname1']
        book_type = request.form['booktype1']
        book_description = request.form['book_description']
        issue_year = request.form['issue_year']
        file_name = request.form['file_name']
        if id !='':
            book_info = Books.query.filter(Books.id == int(id)).first()
            if book_info:
                if book_name != '':
                    msg1 = 'book_name'
                    book_info.book_name = str(book_name)
                else:
                    msg1 =''
                if book_type != '':
                    msg2 = 'book_type'
                    book_info.book_type = str(book_type)
                else:
                    msg2 =''
                if book_description != '':
                    msg3 = 'book_description'
                    book_info.book_introduction = str(book_description)
                else:
                    msg3 =''
                if issue_year != '':
                    msg4 = 'issue_year'
                    book_info.issue_year = str(issue_year)
                else:
                    msg4 = ''
                if file_name != '':
                    msg5 = 'file_name'
                    book_info.book_file_name = str(file_name)
                else:
                    msg5 =''
                db.session.commit()
                db.session.close()
                #添加成功后渲染到主页
                mssage_full = msg1 + ' '+msg2+ ' ' + msg3 + ' '+ msg4 + ' '+ msg5
                if mssage_full == '':
                    message = 'Update data: None Success!'
                else:
                    message = 'Update data: '+ mssage_full +' Success!'
                style = 'alert alert-success alert-dismissable'
                title = 'SUCCESS! '
            else:
                message = 'No data!'
                style = 'alert alert-dismissable alert-danger'
                title = 'Warning! '   
        else:
            message = 'Lost ID!'
            style = 'alert alert-dismissable alert-danger'
            title = 'Warning! '   
        #返回对应的错误信息渲染页面
        dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'',
                'active_next':'','active_Prev':'','current_page_number':1}
        dic1['message'] = message
        dic1['style'] = style
        dic1['title'] = title
        #根据参数查询用户数据，一次10条
        book_info = Books.query.limit(10).all()
        book_list = []
        if len(book_info) ==0:
            user_list = []
        else:
            for userdata in book_info:
                book_list.append( userdata.__dict__)
            style_list = ['success','info','warning','error']
            for j in book_list:
                #删除多余的字段
                del j['_sa_instance_state']
                #为表格加随机样式
                j['style'] = random.choice(style_list)
        return render_template('book.html',form = form,list1 = book_list,dic1 = dic1)
    elif request.method == 'GET':
        return abort(404)

#管理界面书本管理删除书本信息
@app.route("/management/book/delete",methods = ['POST','GET'])
@login_required
@routing_permission_check
def delete_book():
    id = request.args.get('id')
    if id:
        try:
            id = int(id)
        except:
            return abort(404)
        else:
            book_data = Books.query.filter(Books.id == id).first()
            if book_data:
                #删除对应的书本压缩包
                remove_file = book_data.book_file_name
                file_path = os.getcwd() + os.path.join(os.sep,'media',remove_file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                db.session.delete(book_data)
                db.session.commit()
                return redirect('/management/book')
            else:
                return abort(404)
    else:
        return abort(404)

#管理界面书本管理添加书本
@app.route("/management/book/addbook",methods = ['POST','GET'])
@login_required
@routing_permission_check
def add_book():
    form = AddBooksForms()
    if request.method == 'POST':
        if form.validate_on_submit():
            book_name = request.form['bookname']
            book_type = request.form['booktype']
            book_introduction = request.form['book_description']
            issue_year = request.form['issue_year']
            bookfile = request.files['bookfile']
            if book_name and book_type != "None" and book_introduction and issue_year and bookfile:
                #接收文件以时间戳为文件名
                #获取文件扩展名
                file_namex, file_extension = os.path.splitext(str(bookfile.filename))
                file_name = str(time.time()) + file_extension
                file_path = os.getcwd() + os.path.join(os.sep,'media',file_name).replace(file_name,'')
                bookfile.save(file_path + secure_filename(file_name))
                #压缩文件
                zipped_file_name = str(time.time()) + '.zip'
                zipped_path = file_path + zipped_file_name
                with zipfile.ZipFile(zipped_path, 'w', zipfile.ZIP_DEFLATED) as zf:        
                    zf.write(file_path + file_name,arcname = file_name)
                #删除源文件，只要压缩包
                if os.path.isfile(file_path + file_name) == True:
                    os.remove(file_path + file_name)
                #写入数据库
                data = Books(id = None ,book_name = book_name,book_type = book_type,book_introduction = book_introduction,\
                    issue_year=issue_year,book_file_name = zipped_file_name,add_book_time=time.strftime('%Y-%m-%d %H:%M:%S'),\
                    number_of_downloads=0)
                db.session.add(data)
                #db.session.flush()
                db.session.commit()
                #添加成功，返回成功的消息，渲染页面
                message = ' Add the book: ' + str(book_name) + ' Success!'
                
                dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'',
                        'current_page_number':1,'style':'alert alert-success alert-dismissable',
                        'title':'SUCCESS!','message':message}
                #查询book表中的所有数据
                book_info = Books.query.limit(10).all()
                if len(book_info) ==0:
                    book_info_list=[]
                else:
                    #print(book_info)
                    book_info_list = []
                    for i in book_info:
                        book_info_list.append(i.__dict__)
                    for j in book_info_list:
                        del j['_sa_instance_state']
                    style_list = ['success','info','warning','error']
                    for dict_data in book_info_list:
                        style_value = random.choice(style_list)
                        dict_data['style'] = style_value
                return render_template('book.html',form = form,dic1 = dic1,list1 = book_info_list)
            else:
                #request中的数据不完整
                message = ' No data!'
                dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'',
                        'current_page_number':1,'style':'alert alert-dismissable alert-danger',
                        'title':'FAILED! ','message':message}
                #查询book表中的所有数据
                book_info = Books.query.limit(10).all()
                if len(book_info) ==0:
                    book_info_list=[]
                else:
                    #print(book_info)
                    book_info_list = []
                    for i in book_info:
                        book_info_list.append(i.__dict__)
                    for j in book_info_list:
                        del j['_sa_instance_state']
                    style_list = ['success','info','warning','error']
                    for dict_data in book_info_list:
                        style_value = random.choice(style_list)
                        dict_data['style'] = style_value
                return render_template('book.html',form = form,dic1 = dic1,list1 = book_info_list)
        else:
            #未通过表单校验
            message = ' Failed form validation!'
            dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'',
                    'current_page_number':1,'style':'alert alert-dismissable alert-danger',
                    'title':'ERROR! ','message':message}
            #将form中的error 信息加入到dic1中
            if form.errors:
                dic_errors = form.errors
                for key,value in dic_errors.items():
                    message += '  ' +str(value[0]) + '  '
            dic1['message'] = message
            #查询book表中的所有数据
            book_info = Books.query.limit(10).all()
            if len(book_info) ==0:
                book_info_list=[]
            else:
                #print(book_info)
                book_info_list = []
                for i in book_info:
                    book_info_list.append(i.__dict__)
                for j in book_info_list:
                    del j['_sa_instance_state']
                style_list = ['success','info','warning','error']
                for dict_data in book_info_list:
                    style_value = random.choice(style_list)
                    dict_data['style'] = style_value
            return render_template('book.html',form = form,dic1 = dic1,list1 = book_info_list)
    elif request.method == 'GET':
        return abort(404)

#管理界面系统权限管理
@app.route("/management/system",methods = ['POST','GET'])
@login_required
@routing_permission_check
def system_mgr():
    form = AddPermissionForms()
    dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'','current_page_number':1}
    #获取所有的用户组给页面的select 作为选项
    list2 = []
    res = UserGroup.query.all()
    for value in res:
        list2.append(str(value.name))
    # print(list2)
    #查询book表中的所有数据
    permission_info = Permission.query.limit(10).all()
    if len(permission_info) ==0:
        permission_info_list=[]
    else:
        permission_info_list = []
        for i in permission_info:
            permission_info_list .append(i.__dict__)
            # print(i.__dict__)
        for j in permission_info_list:
            del j['_sa_instance_state']
        style_list = ['success','info','warning','error']
        for dict_data in permission_info_list:
            style_value = random.choice(style_list)
            dict_data['style'] = style_value
    return render_template('system.html',form = form,dic1 = dic1,list1 = permission_info_list,list2 = list2)

#管理界面系统管理页面翻页
@app.route('/management/system/page',methods = ['POST','GET'])
@login_required
@routing_permission_check
def system_page():
    number = request.args.get('number')
    try:
        number = int(number)
    except:
        return abort(404)
    else:
        form = AddPermissionForms()
        #获取所有的用户组给页面的select 作为选项
        list2 = []
        res = UserGroup.query.all()
        for value in res:
            list2.append(str(value.name))
        # print(list2)
        #查询用户数据
        dic1 = {'active1':'','active2':'','active3':'','active4':'','active5':'','active_next':'','active_Prev':'','current_page_number':number}
        if 1<=number<=5:
            dic1['active'+str(number)] = 'active'
        elif number>5:
            dic1['active_next'] = 'active'
        #根据参数查询用户数据，一次10条
        offset_num = (number-1)*10
        limit_num = 10
        permission_info = Permission.query.offset(offset_num).limit(limit_num).all()
        permission_list = []
        if len(permission_info) ==0:
            permission_list = []
        else:
            for permissiondata in permission_info:
                permission_list.append( permissiondata.__dict__)
            style_list = ['success','info','warning','error']
            for j in permission_list:
                #删除多余的字段
                del j['_sa_instance_state']
                #为表格加随机样式
                j['style'] = random.choice(style_list)
        return render_template('system.html',list1= permission_list,dic1 = dic1,form = form,list2 = list2)

#管理界面系统管理页面添加permission
@app.route('/management/system/permission/add',methods = ['POST','GET'])
@login_required
@routing_permission_check
def add_permission():
    form = AddPermissionForms()
    if request.method == 'POST':
        if form.validate_on_submit():
            name = request.form['group_name']
            url = request.form['url']
            description = request.form['description']
            if  name != "None" and name != '' and url and description:
                print(name,url,description)
                data = Permission(id = None,name = str(name),url = str(url) ,description = str(description))
                db.session.add(data)
                #db.session.flush()
                db.session.commit()
                db.session.close()
                message = 'Add Permission : '+ str(name) + ' ' + str(url) + ' '+ str(description) +' Success!'
                style = 'alert alert-success alert-dismissable'
                title = 'SUCCESS! '
            else:
                message = 'No data!'
                style = 'alert alert-dismissable alert-danger'
                title = 'Warning! ' 
        else:
            message = ' '
            error_dict = form.errors
            if error_dict :
                for key,value in error_dict.items():
                    message += ' '+str(value[0])
            style = 'alert alert-dismissable alert-danger'
            title = 'Warning! ' 
        #渲染网页返回提示结果
        form = AddPermissionForms()
        dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'','current_page_number':1}
        #添加提示框的信息
        dic1['message'] = message
        dic1['style'] = style
        dic1['title'] = title
        #获取所有的用户组给页面的select 作为选项
        list2 = []
        res = UserGroup.query.all()
        for value in res:
            list2.append(str(value.name))
        # print(list2)
        #查询book表中的所有数据
        permission_info = Permission.query.limit(10).all()
        if len(permission_info) ==0:
            permission_info_list=[]
        else:
            permission_info_list = []
            for i in permission_info:
                permission_info_list .append(i.__dict__)
                # print(i.__dict__)
            for j in permission_info_list:
                del j['_sa_instance_state']
            style_list = ['success','info','warning','error']
            for dict_data in permission_info_list:
                style_value = random.choice(style_list)
                dict_data['style'] = style_value
        return render_template('system.html',form = form,dic1 = dic1,list1 = permission_info_list,list2 = list2)
    elif request.method == 'GET':
        return abort(404)

#管理界面系统管理页面修改permission
@app.route("/management/system/permission/update",methods = ['POST','GET'])
@login_required
@routing_permission_check
def update_permission():
    form = AddPermissionForms()
    if request.method == 'POST':
        id = request.form['id']
        name = request.form['group_name']
        url = request.form['url']
        description = request.form['description']
        if id !='':
            permission_info = Permission.query.filter(Permission.id == int(id)).first()
            if permission_info:
                if name != '':
                    msg1 = 'name'
                    permission_info.name = str(name)
                else:
                    msg1 =''
                if url != '':
                    msg2 = 'url'
                    permission_info.url = str(url)
                else:
                    msg2 =''
                if description != '':
                    msg3 = 'description'
                    permission_info .description = str(description)
                else:
                    msg3 =''
                db.session.commit()
                db.session.close()
                #添加成功后渲染到主页
                mssage_full = msg1 + ' '+msg2+ ' ' + msg3
                if mssage_full == '':
                    message = 'Update permission: None Success!'
                else:
                    message = 'Update permission: '+ mssage_full +' Success!'
                style = 'alert alert-success alert-dismissable'
                title = 'SUCCESS! '
            else:
                message = 'No data!'
                style = 'alert alert-dismissable alert-danger'
                title = 'Warning! '   
        else:
            message = 'Lost ID!'
            style = 'alert alert-dismissable alert-danger'
            title = 'Warning! '   
        #返回对应的错误信息渲染页面
        dic1 = {'active1':'active','active2':'','active3':'','active4':'','active5':'',
                'active_next':'','active_Prev':'','current_page_number':1}
        dic1['message'] = message
        dic1['style'] = style
        dic1['title'] = title
        #获取所有的用户组给页面的select 作为选项
        list2 = []
        res = UserGroup.query.all()
        for value in res:
            list2.append(str(value.name))
        #根据参数查询用户数据，一次10条
        permission_info = Permission.query.limit(10).all()
        permission_list = []
        if len(permission_info) ==0:
            permission_list = []
        else:
            for data in permission_info:
                permission_list.append( data.__dict__)
            style_list = ['success','info','warning','error']
            for j in permission_list:
                #删除多余的字段
                del j['_sa_instance_state']
                #为表格加随机样式
                j['style'] = random.choice(style_list)
        return render_template('system.html',form = form,list1 = permission_list,dic1 = dic1,list2 = list2)
    elif request.method == 'GET':
        return abort(404)

#管理界面系统管理页面删除permission
@app.route("/management/system/permission/delete",methods = ['POST','GET'])
@login_required
@routing_permission_check
def delete_permission():
    id = request.args.get('id')
    if id:
        try:
            id = int(id)
        except:
            return abort(404)
        else:
            permission_data = Permission .query.filter(Permission.id == id).first()
            if permission_data:
                db.session.delete(permission_data)
                db.session.commit()
                return redirect('/management/system')
            else:
                return abort(404)
    else:
        return abort(404)

if __name__ == '__main__':
    app.run(host = '0.0.0.0',port=5000,debug = True)

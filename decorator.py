#coding=utf-8
from flask import session,jsonify,request,g
from functools import wraps
from models import Permission, User,UserGroup
import hashlib


# # 权限缓存
PERMISSION_DICT = {}

#检查登录
def login_required(func):
    @wraps(func) 
    def inner(*args, **kwargs):
        user_id = session.get('user_id')
        #print("session user_id:", user_id)
        if not user_id:
            return jsonify({'error':'User not logged in'}
                           )
        else:
            g.user_id = user_id
            return func(*args, **kwargs)
    return inner

# #检查路由权限
def routing_permission_check(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        '''
        校验权限的过程:
        1.user表通过获取session user_id(heyi01) 查询group_id 
        2.user_group表通过group_id  查询角色名name
        3.permission 表，通过name 查询所有的url 生成list
        4.获取当前访问的路由的url去掉最后的? ,判断list是否包含url
        '''
        #获取用户名
        user_id = session.get('user_id')
        #获取当前访问的url
        current_url = str(request.full_path).rstrip('?')

        #判断权限字典是否为空
        if PERMISSION_DICT:
            result = User.query.filter(User.username == user_id).first()
            if result:
                group_id = result.group_id
                result1 = UserGroup.query.filter(UserGroup.id == group_id).first()
                if result1:
                    name = result1.name
                    if current_url in PERMISSION_DICT[name]:
                        return func(*args,**kwargs)
                    else:
                        return jsonify({'code':403,'message':'Unauthorized access'})
                else:
                    return jsonify({'code':403,'message':'Unauthorized access'})
            else:
                return jsonify({'code':403,'message':'Unauthorized access'})
        else:
            #在全局变量中写入权限表中得数据格式为{'admin':{},'others':{}}
            #查询所有的用户组
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
                    else:
                        return jsonify({'code':403,'message':'Unauthorized access'})
            else:
                return jsonify({'code':403,'message':'Unauthorized access'})
            # print(PERMISSION_DICT)
            result = User.query.filter(User.username == user_id).first()
            if result:
                group_id = result.group_id
                result1 = UserGroup.query.filter(UserGroup.id == group_id).first()
                if result1:
                    name = result1.name
                    if current_url in PERMISSION_DICT[name]:
                        return func(*args,**kwargs)
                    else:
                        return jsonify({'code':403,'message':'Unauthorized access'})
                else:
                    return jsonify({'code':403,'message':'Unauthorized access'})
            else:
                return jsonify({'code':403,'message':'Unauthorized access'})

        # result = User.query.filter(User.username == user_id).first()
        # if result:
        #     group_id = result.group_id
        #     result1 = UserGroup.query.filter(UserGroup.id == group_id).first()
        #     if result1:
        #         name = result1.name
        #         result2 = Permission.query.filter(Permission.name == name).all()
        #         url_list = []

        #         if len(result2) != 0:
        #             for per in result2:
        #                 url_list.append(per.url)
        #             if current_url in url_list:
        #                 return func(*args,**kwargs)
        #             else:
        #                 return jsonify({'code':403,'message':'Unauthorized access'})
        #         else:
        #             return jsonify({'code':403,'message':'Unauthorized access'})
        #     else:
        #         return jsonify({'code':403,'message':'Unauthorized access'})
        # else:
        #     return jsonify({'code':403,'message':'Unauthorized access'})
    return wrapper

#hash加密
def get_hash_value(pwd,salt):
    hash = hashlib.sha256(salt.encode('utf-8'))
    hash.update(pwd.encode('utf-8'))
    hash_value = hash.hexdigest()
    return hash_value



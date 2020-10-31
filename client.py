# encoding = utf-8
import functools
from flask import Flask, url_for, escape, render_template, request, jsonify, redirect, make_response, flash, session
from entity import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
app.secret_key = "TJH321"
engine = create_engine(
    'sqlite:///./university.sqlite?check_same_thread=False', echo=False)
db_session = sessionmaker(bind=engine)
sess = db_session()
# Base.metadata.create_all(engine)# 创建数据库

#####################################
# 辅助函数
#####################################
@app.errorhandler(404)
def miss(e):
    return render_template('error.html'), 404


@app.errorhandler(500)
def error(e):
    return render_template('error.html'), 500


def LoginValid(func):
    @functools.wraps(func)  # 保留原来的函数名字
    def inner(*args, **kwargs):
        if 'user' in session:
            return func(*args, **kwargs)
        else:
            return render_template('login.html')
    return inner


def UserValid(func):
    '''
    如果登录角色与访问页面是一致则没事，否则返回对应角色首页
    '''
    @functools.wraps(func)  # 保留原来的函数名字
    def inner(*args, **kwargs):
        if 'user' in session and (session['user']['role'] == 'student' or session['user']['role'] == 'admin'):
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return inner


def TeacherValid(func):
    '''
    如果登录角色与访问页面是一致则没事，否则返回对应角色首页
    '''
    @functools.wraps(func)  # 保留原来的函数名字
    def inner(*args, **kwargs):
        if 'user' in session and session['user']['role'] == 'teacher':
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return inner


def AdminValid(func):
    '''
    如果登录角色与访问页面是一致则没事，否则返回对应角色首页
    '''
    @functools.wraps(func)  # 保留原来的函数名字
    def inner(*args, **kwargs):
        if 'user' in session and session['user']['role'] == 'admin':
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return inner


#####################################
# default
#####################################
@app.route('/')
def index():
    return redirect(url_for('login'))  # 函数名映射


@app.route('/welcome')
def welcome():
    '''
    统计信息
    '''
    users = sess.query(User).all()
    courses = sess.query(User).all()
    scs = sess.query(SC).all()

    num_users = len(users)
    stus = []
    teas = []
    admins = []
    
    for u in users:
        if u.role == 'admin':
            admins.append(u)
        if u.role == 'student':
            stus.append(u)
        if u.role == 'teacher':
            teas.append(u)
    
    data = {}
    data['num_user'] = num_users
    data['num_student'] = len(stus)
    data['num_admin'] = len(admins)
    data['num_teacher'] = len(teas)
    data['num_course'] = len(courses)
    data['num_sc'] = len(scs)

    return render_template('welcome.html',data = data)


@app.route('/ui/university/admin')
@LoginValid
@AdminValid
def admin_index():
    user = session['user']
    user = sess.query(User).filter(User.name == user['name']).filter(
        User.role == 'admin').first()
    return render_template('index-admin.html', name=user.name, role=user.role)

#####################################
# System,不需要登录状态检测
#####################################
@app.route('/ui/university/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user' in session:
            user = session['user']
            login_role = user['role']
            if login_role == "admin":
                return render_template("index-admin.html", name=user['name'], role=login_role)
            if login_role == "student":
                return render_template("index-stu.html", name=user['name'], role=login_role)
            if login_role == "teacher":
                return render_template("index-tea.html", name=user['name'], role=login_role)
        return render_template("login.html")
    if request.method == 'POST':
        loginName = request.form.get("loginName")
        password = request.form.get("password")

        u = sess.query(User).filter(User.name == loginName).first()
        response = {}
        if u:
            response['code'] = Status.SUCCESS
            response['role'] = u.role
            user = {}
            user['id'] = u.id
            user['name'] = u.name
            user['role'] = u.role
            session['user'] = user
        else:
            response['code'] = Status.ERROR
            flash('账号不存在或密码错误！')
        return jsonify(response)


@app.route('/ui/university/logout', methods=['GET', 'POST'])
def logout():
    resp = make_response(render_template('login.html'))
    if 'user' in session:
        del session['user']
    return resp


@app.route('/ui/university/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        name = request.form.get("name")
        role = request.form.get("role")
        phone = request.form.get("phone")
        email = request.form.get("email")
        password = request.form.get("password")
        intro = ""

        u = sess.query(User).filter(User.name == name).first()

        response = {}
        if not u:
            response['code'] = Status.SUCCESS
            response['role'] = role

            user = User()
            user.name = name
            user.role = role
            user.phone = phone
            user.email = email
            user.password = password
            user.intro = intro

            sess.add(user)
            sess.commit()
        else:
            response['code'] = Status.ERROR
            flash('账号已存在！')
        return jsonify(response)

#####################################
# User，需要登录状态检测
#####################################


@app.route('/ui/university/user')
@LoginValid
@UserValid
def u_index():
    user = session['user']
    user = sess.query(User).filter(User.name == user['name']).filter(
        User.role == 'student').first()
    return render_template('index-stu.html', name=user.name, role=user.role)


@app.route('/admin/user/list')
@LoginValid
@UserValid
def u_frame_list():
    '''
    frame
    '''
    return render_template('admin-user-list.html')


@app.route('/user/user/add', methods=['GET', 'POST'])
@LoginValid
@UserValid
def u_add():
    if request.method == 'GET':
        return render_template("admin-user-add.html")
    if request.method == 'POST':
        response = {}
        name = request.form.get("username")
        phone = request.form.get("phone")
        intro = request.form.get("intro")
        role = request.form.get("role")

        try:
            t = sess.query(User).filter(User.name == name,User.role == role).first()
            if t:
                flash('用户已存在！')
                response['code'] = Status.ERROR
                return jsonify(response)
            u = User()
            u.name = name
            u.phone = phone
            u.intro = intro
            u.role = role
            sess.add(u)
            sess.commit()
            response['code'] = Status.SUCCESS
        except Exception as e:
            print(e)
            response['code'] = Status.ERROR

        return jsonify(response)
    

@app.route('/admin/user/edit', methods=['GET', 'POST'])
@LoginValid
def u_admin_update():
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        user = sess.query(User).filter(User.id == user_id).first()
        return render_template("admin-user-edit.html", user=user)
    if request.method == 'POST':
        # id = request.form.get("id")# 前端无法id传入
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        password = request.form.get("password")
        response = {}
        try:
            sess.query(User).filter(User.name == name).update(
                {
                    'name': name,
                    'phone': phone,
                    'email': email,
                    'password': password
                }
            )
            sess.commit()
            response['code'] = Status.SUCCESS
        except:
            response['code'] = Status.ERROR
        return jsonify(response)


@app.route('/user/user/edit', methods=['GET', 'POST'])
@LoginValid
def u_update():
    if request.method == 'GET':
        user = session['user']
        user = sess.query(User).filter(User.name == user['name']).first()
        return render_template("admin-user-edit.html", user=user)
    if request.method == 'POST':
        # id = request.form.get("id")# 前端无法id传入
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        password = request.form.get("password")
        response = {}
        try:
            sess.query(User).filter(User.name == name).update(
                {
                    'name': name,
                    'phone': phone,
                    'email': email,
                    'password': password
                }
            )
            sess.commit()
            response['code'] = Status.SUCCESS
        except:
            response['code'] = Status.ERROR
        return jsonify(response)


@app.route('/user/user/delete')
@LoginValid
@AdminValid
def u_delete():
    response = {}
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        try:
            u = sess.query(User).filter(User.id == user_id).first()
            sess.delete(u)
            sess.commit()
            response['code'] = Status.SUCCESS
        except Exception as e:
            print(e)
            response['code'] = Status.ERROR
        return jsonify(response)
    response['code'] = Status.ERROR
    return jsonify(response)



@app.route('/user/user/findByNameLike', methods=["GET", "POST"])
@LoginValid
@AdminValid
def u_find_by_name():
    user = session['user']
    username = request.args.get('username')
    response = {}
    try:
        if username != "":
            users = sess.query(User).filter(
                User.name.like('%'+username+'%')).all()
        else:
            users = sess.query(User).all()
        data = []
        for c in users:
            t = {}
            t["id"] = c.id
            t["name"] = c.name
            t["phone"] = c.phone
            t['email']  = c.email
            t['role']  = c.role
            if c.intro is None or len(c.intro) == 0:
                t["intro"] = ''
            elif len(c.intro) < 50:
                t["intro"] = c.intro
            else:
                t["intro"] = c.intro[:50]+'......'
            data.append(t)

        response['code'] = Status.SUCCESS
        response['result'] = data[:40]  
    except Exception as e:
        print(e)
        response['code'] = Status.ERROR
    return jsonify(response)



#####################################
# Teacher，需要登录状态检测
#####################################
@app.route('/ui/university/teacher')
@LoginValid
@TeacherValid
def t_index():
    user = session['user']
    user = sess.query(User).filter(User.name == user['name']).filter(
        User.role == 'teacher').first()
    return render_template('index-tea.html', name=user.name, role=user.role)


@app.route('/admin/teacher/list')
@LoginValid
@UserValid
def t_frame_list():
    '''
    frame
    '''
    return render_template('admin-teacher-list.html')


@app.route('/teacher/teacher/add', methods=['GET', 'POST'])
@LoginValid
@AdminValid
def t_add():
    if request.method == 'GET':
        return render_template("admin-teacher-add.html")
    if request.method == 'POST':
        response = {}
        name = request.form.get("username")
        phone = request.form.get("phone")
        intro = request.form.get("intro")

        try:
            t = sess.query(User).filter(User.name == name,User.role == 'teacher').first()
            if t:
                flash('用户已存在！')
                response['code'] = Status.ERROR
                return jsonify(response)
            u = User()
            u.name = name
            u.phone = phone
            u.intro = intro
            u.role = 'teacher'
            sess.add(u)
            sess.commit()
            response['code'] = Status.SUCCESS
        except Exception as e:
            print(e)
            response['code'] = Status.ERROR

        return jsonify(response)


@app.route('/admin/teacher/edit', methods=['GET', 'POST'])
@LoginValid
def t_admin_update():
    if request.method == 'GET':
        teacher_id = request.args.get('teacher_id')
        user = sess.query(User).filter(User.id == teacher_id).first()
        return render_template("admin-teacher-edit.html", user=user)
    if request.method == 'POST':
        name = request.form.get("name")
        phone = request.form.get("phone")
        intro = request.form.get("intro")
        password = request.form.get("password")
        response = {}
        try:
            sess.query(User).filter(User.name == name).update(
                {
                    'name': name,
                    'phone': phone,
                    'intro': intro,
                    'password': password
                }
            )
            sess.commit()
            response['code'] = Status.SUCCESS
        except:
            response['code'] = Status.ERROR
        return jsonify(response)

@app.route('/teacher/teacher/edit', methods=['GET', 'POST'])
@LoginValid
def t_update():
    if request.method == 'GET':
        user = session['user']
        user = sess.query(User).filter(User.name == user['name']).first()
        return render_template("admin-teacher-edit.html", user=user)
    if request.method == 'POST':
        name = request.form.get("name")
        phone = request.form.get("phone")
        intro = request.form.get("intro")
        password = request.form.get("password")
        response = {}
        try:
            sess.query(User).filter(User.name == name).update(
                {
                    'name': name,
                    'phone': phone,
                    'intro': intro,
                    'password': password
                }
            )
            sess.commit()
            response['code'] = Status.SUCCESS
        except:
            response['code'] = Status.ERROR
        return jsonify(response)


@app.route('/teacher/teacher/delete', methods=['GET', 'POST'])
@LoginValid
def t_delete():
    response = {}
    if request.method == 'GET':
        teacher_id = request.args.get('teacher_id')
        try:
            u = sess.query(User).filter(User.id == teacher_id, User.role == 'teacher').first()
            sess.delete(u)
            sess.commit()
            response['code'] = Status.SUCCESS
        except Exception as e:
            print(e)
            response['code'] = Status.ERROR
        return jsonify(response)
    response['code'] = Status.ERROR
    return jsonify(response)


@app.route('/teacher/teacher/findByNameLike', methods=["GET", "POST"])
@LoginValid
@AdminValid
def t_find_by_name():
    user = session['user']
    teachername = request.args.get('teachername')
    response = {}
    try:
        if teachername != "":
            teachers = sess.query(User).filter(
                User.name.like('%'+teachername+'%'), User.role == 'teacher').all()
        else:
            teachers = sess.query(User).filter(User.role == 'teacher').all()
        data = []
        for c in teachers:
            t = {}
            t["id"] = c.id
            t["name"] = c.name
            t["phone"] = c.phone
            if c.intro is None or len(c.intro) == 0:
                t["intro"] = ''
            elif len(c.intro) < 50:
                t["intro"] = c.intro
            else:
                t["intro"] = c.intro[:50]+'......'
            data.append(t)

        response['code'] = Status.SUCCESS
        response['result'] = data[:40]  
    except Exception as e:
        print(e)
        response['code'] = Status.ERROR
    return jsonify(response)


#####################################
# Course，需要登录状态检测
#####################################

@app.route('/admin/course/list')
@LoginValid
def c_admin_frame_list():
    '''
    frame
    '''
    return render_template('admin-course-list.html')


@app.route('/user/course/list')
@LoginValid
def c_user_frame_list():
    '''
    frame
    '''
    return render_template('course-list.html')


@app.route('/user/stu_course')
@LoginValid
def c_user_frame2_list():
    '''
    frame
    '''
    return render_template('stu-course-list.html')


@app.route('/user/tea_course')
@LoginValid
def c_teacher_frame2_list():
    '''
    frame
    '''
    return render_template('tea-course-list.html')


@app.route('/course/course/add', methods=["GET", "POST"])
@LoginValid
def c_add():
    if request.method == 'GET':
        user = session['user']
        user = sess.query(User).filter(User.name == user['name']).first()
        return render_template("admin-course-add.html", user=user)
    if request.method == 'POST':
        coursename = request.form.get("coursename")
        teachername = request.form.get("teacher")
        intro = request.form.get("intro")

        t = sess.query(User).filter(User.name == teachername,
                                    User.role == 'teacher').first()
        response = {}
        if not t:
            flash('教师名称不存在！')
            response['code'] = Status.ERROR
            return jsonify(response)

        course = Course()
        course.course_name = coursename
        course.teacher_name = teachername
        course.teacher_id = t.id
        course.intro = intro

        try:
            sess.add(course)
            sess.commit()
            response['code'] = Status.SUCCESS
        except Exception as e:
            print(e)
            response['code'] = Status.ERROR
        return jsonify(response)


@app.route('/course/course/edit', methods=["GET", "POST"])
def c_update():
    if request.method == 'GET':
        course_id = request.args.get('course_id')
        c = sess.query(Course).filter(Course.id == course_id).first()
        return render_template("admin-course-edit.html", course=c)
    if request.method == 'POST':
        response = {}
        coursename = request.form.get("coursename")
        teachername = request.form.get("teacher")
        intro = request.form.get("intro")

        response = {}
        try:
            t = sess.query(User).filter(User.name == teachername,
                                        User.role == 'teacher').first()
            if not t:
                flash('教师名称不存在！')
                response['code'] = Status.ERROR
                return jsonify(response)

            sess.query(Course).filter(Course.course_name == coursename).update(
                {
                    'teacher_id': t.id,
                    'teacher_name': t.name,
                    'intro': intro
                }
            )
            sess.commit()
            response['code'] = Status.SUCCESS
        except Exception as e:
            print(e)
            response['code'] = Status.ERROR
        return jsonify(response)


@app.route('/course/course/delete', methods=["GET", "POST"])
def c_delete():
    response = {}
    if request.method == 'GET':
        course_id = request.args.get('course_id')
        try:
            c = sess.query(Course).filter(Course.id == course_id).first()
            sess.delete(c)
            sess.commit()
            response['code'] = Status.SUCCESS
        except Exception as e:
            print(e)
            response['code'] = Status.ERROR
        return jsonify(response)

    response['code'] = Status.ERROR
    return jsonify(response)


@app.route('/course/course/selectCourse', methods=["GET", "POST"])
@LoginValid
def c_selectCourse():
    user = session['user']
    response = {}

    course_id = request.args.get('course_id')
    try:
        c = sess.query(Course).filter(Course.id == course_id).first()
        u = sess.query(User).filter(User.id == user['id']).first()
        sc = SC()
        sc.course_id = c.id
        sc.course_name = c.course_name
        sc.user_id = u.id
        sc.user_name = u.name
        sess.add(sc)
        sess.commit()
        response['code'] = Status.SUCCESS
    except Exception as e:
        print(e)
        response['code'] = Status.ERROR

    return jsonify(response)


@app.route('/course/course/removeCourse', methods=["GET", "POST"])
@LoginValid
def c_removeCourse():
    user = session['user']
    response = {}
    course_id = request.args.get('course_id')
    try:
        sc = sess.query(SC).filter(SC.course_id == course_id,
                                   SC.user_id == user['id']).first()
        sess.delete(sc)
        sess.commit()
        response['code'] = Status.SUCCESS
    except Exception as e:
        print(e)
        response['code'] = Status.ERROR
    return jsonify(response)


@app.route('/course/course/findByNameLike', methods=["GET", "POST"])
@LoginValid
def c_find_by_name():
    user = session['user']
    coursename = request.args.get('coursename')
    response = {}
    if user['role'] == 'admin':
        try:
            if coursename != "":
                courses = sess.query(Course).filter(
                    Course.course_name.like('%'+coursename+'%')).all()
            else:
                courses = sess.query(Course).all()
            data = []
            for c in courses:
                t = {}
                t["id"] = c.id
                t["name"] = c.course_name
                t["teacher"] = c.teacher_name
                if c.intro is None or len(c.intro) == 0:
                    t["content"] = ''
                elif len(c.intro) < 50:
                    t["content"] = c.intro
                else:
                    t["content"] = c.intro[:50]+'......'
                data.append(t)

            response['code'] = Status.SUCCESS
            response['result'] = data[:40]  
        except Exception as e:
            print(e)
            response['code'] = Status.ERROR
        return jsonify(response)
    if user['role'] == 'teacher':
        try:
            if coursename != "":
                courses = sess.query(Course).filter(
                    Course.course_name.like('%'+coursename+'%'), Course.teacher_name == user['name']).all()
            else:
                courses = sess.query(Course).filter(
                    Course.teacher_name == user['name']).all()
            data = []
            for c in courses:
                t = {}
                t["id"] = c.id
                t["name"] = c.course_name
                t["teacher"] = c.teacher_name
                if c.intro is None or len(c.intro) == 0:
                    t["content"] = ''
                elif len(c.intro) < 50:
                    t["content"] = c.intro
                else:
                    t["content"] = c.intro[:50]+'......'
                data.append(t)

            response['code'] = Status.SUCCESS
            response['result'] = data[:40]  
        except Exception as e:
            print(e)
            response['code'] = Status.ERROR
        return jsonify(response)
    if user['role'] == 'student':
        mycourse = request.args.get('mycourse')
        if mycourse:
            try:
                scs = sess.query(SC).filter(SC.user_id == user['id']).all()
                cids = [sc.course_id for sc in scs]
                courses = sess.query(Course).filter(Course.id.in_(cids)).all()
                data = []
                for c in courses:
                    t = {}
                    t["id"] = c.id
                    t["name"] = c.course_name
                    t["teacher"] = c.teacher_name
                    if c.intro is None or len(c.intro) == 0:
                        t["content"] = ''
                    elif len(c.intro) < 50:
                        t["content"] = c.intro
                    else:
                        t["content"] = c.intro[:50]+'......'
                    if sess.query(SC).filter(SC.course_id == c.id, SC.user_id == user['id']).first():
                        t['is_selected'] = 1  # 1已经选择
                    else:
                        t['is_selected'] = 0  # 0未选择
                    data.append(t)
                response['code'] = Status.SUCCESS
                response['result'] = data[:40]  
            except Exception as e:
                print(e)
                response['code'] = Status.ERROR
        else:
            try:
                if coursename != "":
                    courses = sess.query(Course).filter(
                        Course.course_name.like('%'+coursename+'%')).all()
                else:
                    courses = sess.query(Course).all()
                data = []
                for c in courses:
                    t = {}
                    t["id"] = c.id
                    t["name"] = c.course_name
                    t["teacher"] = c.teacher_name
                    if c.intro is None or len(c.intro) == 0:
                        t["content"] = ''
                    elif len(c.intro) < 50:
                        t["content"] = c.intro
                    else:
                        t["content"] = c.intro[:50]+'......'
                    if sess.query(SC).filter(SC.course_id == c.id, SC.user_id == user['id']).first():
                        t['is_selected'] = 1  # 1已经选择
                    else:
                        t['is_selected'] = 0  # 0未选择
                    data.append(t)

                response['code'] = Status.SUCCESS
                response['result'] = data[:40]  
            except Exception as e:
                print(e)
                response['code'] = Status.ERROR
    return jsonify(response)


def test_url():
    with app.test_request_context():
        print(url_for('index'))
        print(url_for('login'))
        print(url_for('login', next='/'))
        print(url_for('profile', username='John Doe'))


if __name__ == "__main__":
    try:
        app.run(debug=False, host='0.0.0.0', port=9800)
    finally:
        if 'user' in session:
            del session['user']
        sess.close()

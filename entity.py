# encoding = utf-8
from sqlalchemy import create_engine, Column, Integer, String,ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    role = Column(String)
    phone = Column(String)
    email = Column(String)
    password = Column(String)
    intro = Column(String)

    def __repr__(self):
        return "<User(id='%s', name='%s', password='%s')>" % (self.id, self.name, self.password)


class Course(Base):
    __tablename__ = 'course'

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey(('user.id')))
    course_name = Column(String)
    teacher_name = Column(String)
    intro = Column(String)

    def __repr__(self):
        return "<Course(id='%s', course_name='%s', teacher_name='%s')>" % (self.id, self.course_name, self.teacher_name)


class SC(Base):
    __tablename__ = 'sc'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(('user.id')))
    course_id = Column(Integer, ForeignKey(('course.id')))
    course_name = Column(String)
    user_name = Column(String)

    def __repr__(self):
        return "<Course(id='%s', course_name='%s', teacher_name='%s')>" % (self.id, self.course_name, self.teacher_name)



class Status:
    SUCCESS = 0
    ERROR = 1

if __name__ == "__main__":
    engine = create_engine('sqlite:///./university.sqlite', echo=False)
    db_session = sessionmaker(bind=engine)
    session = db_session()
    # Base.metadata.create_all(engine)

    
    # 查询全部
    users = session.query(User).all()
    for u in users:
        print(u)
    
    # 名字模糊查询
    courses = session.query(Course).filter(Course.course_name.like('%分析%')).all()
    for c in courses:
        print(c)
    
    
    # 添加
    course = Course()
    course.course_name = "网络安全技术"
    course.teacher_id = ''
    course.teacher_name = '闫怀志'
    course.intro = ''
    session.add(course)
    session.commit()
    courses = session.query(Course).all()
    for c in courses:
        print(c)

    # 更新
    u = session.query(User).first()
    print(u.password)
    u.password = 'zjzj'
    session.commit()# 直接更改查出来的对象
    u = session.query(User).first()
    print(u.password)

    # 删除
    # session.query(User).first().delete()
    # session.commit()

    print(session.query(SC).filter(SC.course_id=='1',SC.user_id=='100').first())

    courses = session.query(Course).filter(Course.id.in_(['1','2'])).all()
    for c in courses:
        print(c)

    session.close()

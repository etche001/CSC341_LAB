
import os
import sys
import oracledb
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect

db_user = "test"
db_password = "Fall2024Fall20241031"
db_connect = "(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=adb.us-ashburn-1.oraclecloud.com))(connect_data=(service_name=t0o4ohckoaairsp_o1oou2wrt1y9wcit_tp.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))"

def init_session(connection, requestedTag_ignored):
    cursor = connection.cursor()
    cursor.execute("""
        ALTER SESSION SET
          TIME_ZONE = 'UTC'
          NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI'""")


# start_pool(): starts the connection pool
def start_pool():

    # Generally a fixed-size pool is recommended, i.e. pool_min=pool_max.
    # Here the pool contains 4 connections, which is fine for 4 conncurrent
    # users.
    #
    # The "get mode" is chosen so that if all connections are already in use, any
    # subsequent acquire() will wait for one to become available.

    pool_min = 1
    pool_max = 2
    pool_inc = 0
    pool_gmd = oracledb.SPOOL_ATTRVAL_WAIT

    print("Connecting to", db_connect)

    pool = oracledb.SessionPool(user=db_user,
                                 password=db_password,
                                 dsn=db_connect,
                                 min=pool_min,
                                 max=pool_max,
                                 increment=pool_inc,
                                 threaded=True,
                                 getmode=pool_gmd,
                                 sessionCallback=init_session)

    return pool



app = Flask(__name__)

def output_type_handler(cursor, metadata):

    def out_converter(d):
        print( d )
        if d is None:
            return ""
        else:
            return d

    if metadata.type_code is oracledb.DB_TYPE_NUMBER:
        return cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=cursor.arraysize, outconverter=out_converter, convert_nulls=True)
            
def emp(empno):
    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.outputtypehandler = output_type_handler
	
    cursor.execute("select * from emp where empno = :empno", [empno])
	
    columns = [col[0] for col in cursor.description]
    cursor.rowfactory = lambda *args: dict(zip(columns, args))

    data = cursor.fetchone()
    connection.close()
    return (data if data else "Unknown user id")

def empAll():
    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.outputtypehandler = output_type_handler
	
    cursor.execute("select * from emp ")
	
    columns = [col[0] for col in cursor.description]
    cursor.rowfactory = lambda *args: dict(zip(columns, args))

    data = cursor.fetchall()

    connection.close()
    return (data)

def empForAManager(empno):
    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.outputtypehandler = output_type_handler
	
    cursor.execute("select * from emp where mgr = :empno",  [empno])
	
    columns = [col[0] for col in cursor.description]
    cursor.rowfactory = lambda *args: dict(zip(columns, args))

    data = cursor.fetchall()

    connection.close()
    return (data)


def empUpdate(empno, ename, job, mgr, sal, deptno):
    connection = pool.acquire()
    cursor = connection.cursor()
	
    cursor.execute("update emp set ename = :ename, job = :job, mgr = :mgr, sal = :sal, deptno = :deptno  where empno = :empno", [ename, job, mgr, sal, deptno, empno])
	
    connection.commit()

def empDelete(empno):
    connection = pool.acquire()
    cursor = connection.cursor()
	
    cursor.execute("delete from  emp where empno = :empno", [empno])
	
    connection.commit()

def empInsert(empno, ename, job, mgr, sal, deptno):
    connection = pool.acquire()
    cursor = connection.cursor()
	
    cursor.execute("insert into emp(EMPNO, ENAME, JOB, MGR, SAL, DEPTNO) values( :EMPNO, :ENAME, :JOB, :MGR, :SAL, :DEPTNO)", [empno, ename, job, mgr, sal, deptno])
	
    connection.commit()

@app.route('/')
@app.route('/index')
def index():
    return empall()
	
# Show the username for a given id
@app.route('/emp/<int:empno>')
def show_emp(empno):
    row = emp(empno)
    return render_template('EmpDetail.html', title='EmpDetail', data = row)

@app.route('/post/emp/<int:empno>', methods=['POST']) 
def update_emp(empno):
    ename = request.form.get('ename')
    job = request.form.get('job')
    mgr = request.form.get('mgr')
    sal = request.form.get('sal')
    deptno = request.form.get('deptno')

    row = empUpdate(empno, ename, job, mgr, sal, deptno)
    
    return show_emp(empno)

@app.route('/delete/emp/<int:empno>', methods=['post']) 
def delete_emp(empno):
    empDelete(empno)
    return redirect("/empall/")
    

@app.route('/empall/')
def empall():
    row = empAll()
    return render_template('EmpList.html', title='ListEmp', data = row)

@app.route('/create/')
def create():
    return render_template('EmpCreate.html', title='EmpCreate')

@app.route('/empfilter/<int:empno>')
def empfilter(empno):
    row = empForAManager(empno)
    return render_template('EmpList.html', title='ListEmp', data = row)

@app.route('/insert/emp/',  methods=['post'])
def empCreate():
    empno = request.form.get('empno')
    ename = request.form.get('ename')
    job = request.form.get('job')
    mgr = request.form.get('mgr')
    sal = request.form.get('sal')
    deptno = request.form.get('deptno')

    row = empInsert(empno, ename, job, mgr, sal, deptno)
    
    row = empAll()
    return render_template('EmpList.html', title='ListEmp', data = row)
	
################################################################################
#
# Initialization is done once at startup time
#
if __name__ == '__main__':

    # Start a pool of connections
    pool = start_pool()

    # Start a webserver
    app.run(port=int(os.environ.get('PORT', '8080')))

	
from flask import Flask,Response, request, render_template, json
import os
from fpdf import FPDF
from database_connection import *
app = Flask(__name__)
login = {}

@app.route('/')
def homepage():
    return render_template("home.html")

@app.route('/patient_register', methods=['POST'])
def register_patient():
    form = request.form
    if request.method == 'POST':
        pid = 0 #incr()+1 # disp("select count(*) from patient")[0][0]
        password = form['pass']
        p_name = form['fname'] + " " + form['lname']
        blood_grp = form['blood_grp']
        age = form['age']
        gender = form['gender']
        ph_no = form['ph_no']
        address = form['address']
        aadhar_id = form['adhar_id']
        p_history = "NULL"
        execute_query("insert into patient values(" + str(pid) + ", '" + password + "', '" + p_name + "', '" + blood_grp + "', " + str(age) + ", '" + gender + "', '" + ph_no + "', '" + address + "', " + str(aadhar_id) + ", '" + p_history + "')")
        return render_template("patient_login.html")

@app.route('/doctor_login', methods=['POST'])
def login_doctor():
    form = request.form
    if request.method == 'POST':
        doctor = disp("select * from doctor where doc_id=" + form['userid'] + " AND password='" + form['password'] + "';")
        if(len(doctor)):
            login[request.remote_addr] = 'd' + str(doctor[0][0])
            return render_template("doctor_home.html", d_name= (doctor[0][2] + " " + doctor[0][3]),doctor_data= doctor[0][4:])
        return render_template("doctor_wrong_pass.html")
        
@app.route('/admin_login', methods=['POST'])
def login_admin():
    form = request.form
    if request.method == 'POST':
        admin = form['userid']
        passworda = form['passwd']
        if(len(admin)):
            login[request.remote_addr] = 'a'
            return render_template("admin_home.html")
        return render_template("admin_wrong_pass.html")
        
@app.route('/patient_login', methods=['POST'])
def login_patient():
    form = request.form
    if request.method == 'POST':
        patient = disp("select * from patient where p_id=" + form['userid'] + " AND password='" + form['password'] + "';")
        if(len(patient)):
            login[request.remote_addr] = 'p' + str(patient[0][0])
            return render_template("patient_home.html", p_name=str(patient[0][2]),patient_data=patient[0][3:])
        return render_template("patient_wrong_pass.html")

@app.route('/admin_manage_doctors.html', methods=['POST'])
def manage_doctor():
    form = request.form
    if "action" in form.keys() and form["action"] == "delete":
        execute_query("delete from doctor where doc_id = " +form["docid"])
    elif "pass" in form.keys():
        execute_query("insert into doctor values (" + '0' + ",'" + form['pass'] + "','" + form['fname'] + "','" +  form['lname'] + "'," + form['adhar_id'] + ",'" + form['chamber'] + "',"+form['salary']+"," + form['add_dept_id'] +",'"+form['timeslot'] + "')")
    else:
        execute_query('update doctor set first_name = "' + form['fname'] + '", last_name = "' + form['lname'] + '", aadhar_id = ' + form['adhar_id'] + ', chamber = "' + form['chamber'] + '", salary = ' + form['salary'] + ', timeslot = "' + form['timeslot'] + '", dept_id=' + form['edit_dept_id'] +' where doc_id = ' + form['docid'])
    return admin_manage_doctors()

@app.route('/admin_manage_pharmacy.html', methods=['POST'])
def manage_pharmacy():
    form = request.form
    if "action" in form.keys() and form["action"] == "delete":
        execute_query("delete from expense where item_id = " +form["itemid"])
    elif "itemadd" in form.keys():
        execute_query("insert into expense values (" + form['itemid'] + ",'" + form['item_name'] + "'," + form['qty'] + "," + form['price'] + ")")
    else:
        execute_query('update expense set item_name = "' + form['item_name'] + '", qty = ' + form['qty'] + ', price = ' + form['price'] + ' where item_id = ' + form['itemid'])
    return render_template("admin_manage_pharmacy.html", pharmacy=disp("select item_id, item_name, qty, price from expense"))

@app.route('/patient_shop.html', methods=['POST'])
def add_to_cart():
    form = request.form
    new_transaction(login[request.remote_addr][1:], form['itemid'], form['quantity'])
    return render_patient_shop(form['p_name'], 'Item added to cart')

@app.route('/patient_book_appointment.html', methods=['POST'])
def book_appointment():
    form = request.form
    p_id = login[request.remote_addr][1:]
    item_id = str(disp('select item_id from expense where item_name="consultation"')[0][0])
    new_transaction(p_id, item_id, 1)
    execute_query('insert into appointment values(' + p_id +', ' + form['docid'] + ', ' + '"'+ form['date'] +'", ' + form['slot'] + ');')
    return render_patient_book_appointment(form['p_name'], 'Appointment booked.')

@app.route('/doctor_appointments.html', methods=['POST'])
def doctor_appointments_det():
    form = request.form
    doc_id = login[request.remote_addr][1:]
    #print('update patient set p_history = "' + form['patdet'] + '" where p_id = '+form['patid'])
    execute_query('update patient set p_history = "' + form['patdet'] + '" where p_id = '+form['patid'])
    doctor_data = disp("select * from doctor where doc_id = " + doc_id)[0]
    d_name = doctor_data[2] + " " + doctor_data[3]
    return render_doctor_appointment(d_name)
    
       
@app.route('/patient_shop_cart.html', methods=['POST'])
def pay_charges():
    form = request.form
    for key in form.keys():
        execute_query('update transact set pay_status = 1 where transact_id = ' + key[1:])
    m_status = login[request.remote_addr]
    patient_data = disp("select * from patient where p_id = " + m_status[1:])[0]
    p_name = str(patient_data[2])
    return render_shop_cart(p_name, m_status)

@app.route('/doctor_appointments2.html', methods=['POST'])
def allot_room():
    pid = request.form['pid']
    doc_id = request.form['d_name']
    doc_id = disp('select doc_id from doctor where CONCAT(first_name, " ", last_name)="' + doc_id+'"')[0][0]
    timeslot = request.form['timeslot']
    free_room = disp('select room_id from room where isAvailable="Y"')[0][0]
    execute_query('update room set p_id = ' + str(pid) + ' isAvailable="NO" where room_id = ' + str(free_room))
    execute_query('update appointment set start_date = NULL where p_id=' + str(pid) + " and doc_id = " + str(doc_id) + " and time = " + str(timeslot))
    return render_doctor_appointment(request.form['d_name'])
       
def new_transaction(p_id, item_id, qty_bought):
    transaction_number = disp('select max(transact_id) from transact')[0][0]
    if transaction_number == None:
        transaction_number = 0
    execute_query('insert into transact values(' + str(transaction_number+1) + ', ' + str(p_id) + ',' + str(item_id) + ',0,' + str(qty_bought) +', NULL)')

def render_patient_shop(p_name, message):
    items=disp('select item_id, item_name, qty, price from expense where not item_name="consultation"')
    items_json = {}
    for item in items:
        items_json[item[0]] = [item[1], item[2], item[3]]
    return render_template('patient_shop.html', p_name=p_name, items=items, message=message, items_json=items_json)

@app.route('/<page_type>', methods=['GET'])
def page(page_type):
    if(page_type == "patient_register.html"):
        userid = disp("select MAX(P_ID) from patient")[0][0]
        if userid is None:
            userid = 1000
        else:
            userid += 1
        return render_template(page_type, value=userid)
    if(request.remote_addr in login.keys()):
        if(login[request.remote_addr] == 'a'):
            if(page_type == 'admin_manage_doctors.html'):
                return admin_manage_doctors()
            elif(page_type == 'admin_manage_patients.html'):
                return render_template(page_type, patient_table=disp("select p_id, p_name, blood_grp, age, gender, ph_no, address, aadhar_id, p_history from patient"))
            elif(page_type == 'admin_manage_pharmacy.html'):
                return render_template(page_type, pharmacy=disp("select item_id, item_name, qty, price from expense"))
            return render_template(page_type)
        elif(login[request.remote_addr][0] == 'p'):
            m_status = login[request.remote_addr]
            patient_data = disp("select * from patient where p_id = " + m_status[1:])[0]
            p_name = str(patient_data[2])
            if(page_type == 'patient_book_appointment.html'):
                return render_patient_book_appointment(p_name, "")
            elif(page_type == 'patient_book_room.html'):
                return render_template(page_type, p_name=p_name)
            elif(page_type == 'patient_home.html'):
                return render_template(page_type, p_name=p_name ,patient_data= patient_data[3:])
            elif(page_type == 'patient_shop.html'):
                return render_patient_shop(p_name, "")
            elif(page_type == 'patient_shop_cart.html'):
                return render_shop_cart(p_name, m_status);
            elif(page_type == 'patient_transaction_history.html'):
                return render_template(page_type, p_name=p_name)
            return render_template(page_type)
        elif(login[request.remote_addr][0] == 'd'):
            m_status = login[request.remote_addr]
            doctor_data = disp("select * from doctor where doc_id = " + m_status[1:])[0]
            d_name = doctor_data[2] + " " + doctor_data[3]
            if(page_type == 'doctor_appointments.html'):
                return render_doctor_appointment(d_name)
            elif(page_type == 'doctor_home.html'):
                return render_template(page_type, d_name=d_name,doctor_data= doctor_data[4:])
            return render_template(page_type)
    else:
        if(page_type == "home.html"):
            del login[request.remote_addr]
        return render_template(page_type)

def admin_manage_doctors():
    return render_template('admin_manage_doctors.html', doctor_table=disp("select doc_id, first_name, last_name, aadhar_id, chamber, salary, dept_id, timeslot from doctor"), departments=disp('select dept_id, dept_name from department')) 

def render_shop_cart(p_name, m_status):
    return render_template("patient_shop_cart.html", p_name=p_name, items=disp("select transact_id, item_name, (price*qty_bought) from transact, expense where transact.item_id = expense.item_id and pay_status=0 and p_id="+m_status[1:])) 

def render_patient_book_appointment(p_name, message):
    appointments_json = {}
    current_appointments = disp('select doc_id, start_date, time from appointment')
    for appointment in current_appointments:
        if appointment[0] not in appointments_json.keys():
           appointments_json[appointment[0]] = {}
        if appointment[1] == "NULL":
            appointments_json[appointment[0]]['room'] = appointment[2]
        else:
            date_str = appointment[1].strftime("%Y-%m-%d")
            if date_str not in appointments_json[appointment[0]].keys():
                appointments_json[appointment[0]][date_str] = []
            appointments_json[appointment[0]][date_str].append(appointment[2])
    return render_template('patient_book_appointment.html', p_name=p_name, doctor_names=disp('select doc_id, concat(first_name, " ", last_name) from doctor;'), doctor_slots=disp('select doc_id,timeslot from doctor;'), message=message, appointments_json=appointments_json)

def render_doctor_appointment(d_name):
    appointments_json = {}
    m_status = login[request.remote_addr]
    current_appointments = disp('select p_id, start_date, time from appointment where doc_id = ' + m_status[1:])
    chamber = disp('select chamber from doctor where doc_id = ' + m_status[1:])[0][0]
    i = 0
    for appointment in current_appointments:
        patient_data = disp('select p_name, p_history, p_id from patient where p_id = ' + str(appointment[0]))[0]
        location = ""
        if appointment[1] != "NULL":
            location = chamber
        else:
            location = disp('select room_id from room where p_id = ' + appointment[0])[0][0]
        appointments_json[i] = [patient_data[0], int(appointment[2]), appointment[1], location, patient_data[1],patient_data[2]]
        i += 1        
    
    return render_template("doctor_appointments.html", d_name=d_name, appointments_json=appointments_json)

@app.route('/admin_report/download/expenseReport')
def download_exp_report():
    pdf = FPDF()
    pdf = make_page_expense(pdf)
    return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment;filename=Expense_report.pdf'})    
@app.route('/admin_report/download/patientReport')
def download_pat_report():
    pdf = FPDF()
    pdf = make_page(pdf,"patient")
    return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment;filename=Patient_report.pdf'})    

@app.route('/admin_report/download/doctorReport')
def download_doc_report():
    pdf = FPDF()
    pdf = make_page(pdf,"doctor")
    return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment;filename=Doctor_report.pdf'})    


    
# def get_pdf():
#     try:
#         pdf = make_page(pdf,"doctor")
#         pdf = make_page(pdf,"patient")
        
#         return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment;filename=Expense_report.pdf'})    
#     except Exception as e:
#         print(e)


def mainFnc():
    init()
    app.run(debug=True)
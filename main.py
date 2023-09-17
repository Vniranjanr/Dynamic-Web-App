from flask import Flask, request, render_template, session, redirect
from datetime import datetime, timedelta
app = Flask(__name__)
import pymongo
import os
from bson import objectid, ObjectId
my_client = pymongo.MongoClient("mongodb://localhost:27017/")
my_db = my_client["Shooting_Arena"]
player_col = my_db['Player']
shooting_place_col=my_db['Shooting_place']
time_slots_col = my_db['time_slots']
shooting_cabin_col = my_db['Shooting_cabin']
schedule_col = my_db['Schedule']
payment_col = my_db['Payment']
holidays_col = my_db['Holidays']
app.secret_key="key"


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/alogin")
def alogin():
    return render_template("alogin.html")


@app.route("/alogin1", methods=['post'])
def alogin1():
    username = request.form.get("username")
    password = request.form.get("password")
    if username == 'admin' and password == 'admin':
        session['role'] = 'admin'
        return redirect("/admin_home")
    return render_template("msg.html", msg="Invalid Details", color='bg-danger')


@app.route("/admin_home")
def admin_home():
    return render_template('admin_home.html')


@app.route("/player_login")
def player_login():
    return render_template("player_login.html")


@app.route("/player_registration")
def player_registration():
    return render_template("player_registration.html")


@app.route("/player_registration1", methods=['post'])
def player_registration1():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')
    query = {'$or': [{'email': email}, {'phone': phone}]}
    count = player_col.count_documents(query)
    if count>0:
        return render_template('msg.html', msg='Player Exits', color='bg-danger')
    query = {'name': name, 'email': email, 'phone': phone, 'password': password}
    player_col.insert_one(query)
    return render_template('msg.html', msg='Player Registration Successful', color='bg-success')


@app.route("/player_login1", methods=['post'])
def player_login1():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {'$or':[{"email": email}, {"password": password}]}
    count = player_col.count_documents(query)
    if count > 0:
        player = player_col.find_one(query)
        session['player_id'] = str(player['_id'])
        session['role'] = 'player'
        return render_template('player_home.html')
    else:
        return render_template("msg.html", msg="Invalid login details", color='text-danger')


@app.route("/add_shooting_places")
def add_shooting_places():
    return render_template('add_shooting_places.html')


@app.route("/add_shooting_places1", methods=['post'])
def add_shooting_places1():
    Place_name = request.form.get('Place_name')
    phone = request.form.get('phone')
    opening_time = request.form.get('opening_time')
    closing_time = request.form.get('closing_time')
    email = request.form.get('email')
    address = request.form.get('address')
    query = {'address': address, 'Place_name': Place_name}
    count = shooting_place_col.count_documents(query)
    if count>0:
        return render_template('msg.html', msg='You Are Adding Existing Address')
    query = {'Place_name': Place_name, 'phone': phone, 'opening_time': opening_time, 'closing_time': closing_time, 'email': email, 'address': address}
    result = shooting_place_col.insert_one(query)
    shooting_place_id = result.inserted_id
    current_date_time = datetime.date(datetime.now())
    date = str(current_date_time) + ' ' + (opening_time)
    date2 = str(current_date_time) + ' ' + (closing_time)
    date_time = datetime.strptime(date, '%Y-%m-%d %H:%M')
    date_time2 = datetime.strptime(date2, '%Y-%m-%d %H:%M')
    slot_number = 0
    slots = []
    while date_time < date_time2:
        from_date = date_time
        to_date = from_date + timedelta(minutes=60)
        date_time = to_date
        fromTime = from_date.strftime('%H:%M')
        toTime = to_date.strftime('%H:%M')
        slot_number = slot_number + 1
        query = {"shooting_place_id": shooting_place_id, "slot_number": slot_number, "start_time": fromTime, "end_time":toTime}
        time_slots_col.insert_one(query)
    return render_template('msg.html', msg='Place Added successfully')


@app.route("/view_shooting_places")
def view_shooting_places():
    shooting_places = shooting_place_col.find()
    return render_template('view_shooting_places.html', shooting_places=shooting_places)


@app.route("/view_time_slots")
def view_time_slots():
    booking_date = request.args.get('booking_date')
    query = {'date': booking_date}
    count = holidays_col.count_documents(query)
    if count>0:
        holiday = holidays_col.find_one(query)
        msg = 'This Day '+str(booking_date)+ ' Is '+holiday['holiday_title']
        return render_template('msg.html', msg=msg)
    shooting_place_id = request.args.get('shooting_place_id')
    shooting_cabin_id = request.args.get('shooting_cabin_id')
    if booking_date == None:
        booking_date = datetime.today().strftime('%Y-%m-%d')
        booking_date = str(booking_date)
    query = {'shooting_place_id': ObjectId(shooting_place_id)}
    time_slots = time_slots_col.find(query)
    return render_template('view_time_slots.html', time_slots=time_slots, shooting_place_id=shooting_place_id,booking_date=booking_date,shooting_cabin_id=shooting_cabin_id,get_schedule_by_cabin_booking_time_slot_id=get_schedule_by_cabin_booking_time_slot_id, get_schedule_by_id=get_schedule_by_id)


def get_schedule_by_id(time_slot_id,booking_date):
    query ={"$or": [{'time_slot_id': ObjectId(time_slot_id),"booking_date": booking_date,"status":"Booked"}, {'time_slot_id': ObjectId(time_slot_id),"booking_date": booking_date,"status":"Completed"}] }
    schedule = schedule_col.find_one(query)
    return schedule

@app.route("/selectSlot", methods=['post'])
def selectSlot():
    booking_date = request.form.get('booking_date')
    time_slot_id = request.form.get('time_slot_id')
    shooting_cabin_id = request.form.get('shooting_cabin_id')
    shooting_place_id = request.form.get('shooting_place_id')
    shooting_cabin = shooting_cabin_col.find_one({"_id": ObjectId(shooting_cabin_id)})
    bill_amount = shooting_cabin['price_per_slot']
    print(bill_amount)
    card_type = request.form.get('card_type')
    card_holder_name = request.form.get('card_holder_name')
    card_number = request.form.get('card_number')
    cvv = request.form.get('cvv')
    expiry_date = request.form.get('expiry_date')
    query = {'booking_date': booking_date, 'shooting_cabin_id': ObjectId(shooting_cabin_id), 'time_slot_id': ObjectId(time_slot_id), 'player_id': ObjectId(session['player_id']), 'date':datetime.now(),'status':'Pending'}
    result = schedule_col.insert_one(query)
    schedule_id = result.inserted_id
    query = {'schedule_id': ObjectId(schedule_id), 'card_type': card_type, 'card_holder_name': card_holder_name, 'card_number': card_number, 'cvv': cvv, 'expiry_date': expiry_date, 'bill_amount': bill_amount, "status" : 'pending'}
    payment_col.insert_one(query)
    return redirect('/view_time_slots?booking_date='+booking_date+'&shooting_cabin_id='+shooting_cabin_id+'&shooting_place_id='+shooting_place_id)


def get_schedule_by_cabin_booking_time_slot_id(booking_date,shooting_place_id,shooting_cabin_id,time_slot_id):
    query = {
        '$or': [
            {'booking_date': booking_date,'shooting_cabin_id': ObjectId(shooting_cabin_id),'time_slot_id': ObjectId(time_slot_id),'status': 'Booked'},
            {'booking_date': booking_date,'shooting_cabin_id': ObjectId(shooting_cabin_id),'time_slot_id': ObjectId(time_slot_id),'status': 'Completed'},
            {'booking_date': booking_date,'shooting_cabin_id': ObjectId(shooting_cabin_id),'time_slot_id': ObjectId(time_slot_id),'status': 'Pending'}
        ]
    }
    schedule = schedule_col.find_one(query)
    return schedule

@app.route("/add_cabins")
def add_cabins():
    shooting_place_id = request.args.get('shooting_place_id')
    return render_template('add_cabins.html', shooting_place_id=shooting_place_id)


@app.route("/add_cabins1", methods=['post'])
def add_cabins1():
    cabin_number = request.form.get('cabin_number')
    shooting_place_id = request.form.get('shooting_place_id')
    shooting_range = request.form.get('shooting_range')
    price = request.form.get('price')
    query = {'shooting_place_id':ObjectId(shooting_place_id), 'cabin_number': cabin_number}
    count = shooting_cabin_col.count_documents(query)
    if count > 0:
        return render_template('msg.html', msg='Can not add cabin to the Existing cabin ')
    query = {'shooting_place_id': ObjectId(shooting_place_id), 'shooting_range': shooting_range, 'price_per_slot':price,'cabin_number': cabin_number}
    shooting_cabin_col.insert_one(query)
    return render_template('msg.html', msg='Cabin Added Successfully')


@app.route("/view_cabins")
def view_cabins():
    shooting_place_id = request.args.get('shooting_place_id')
    query = {'shooting_place_id': ObjectId(shooting_place_id)}
    cabins = shooting_cabin_col.find(query)
    return render_template('view_cabins.html', cabins=cabins, shooting_place_id=shooting_place_id)

@app.route("/schedule", methods=['post'])
def schedule():
    booking_date = request.form.get('booking_date')
    shooting_cabin_id = request.form.get('shooting_cabin_id')
    time_slot_id = request.form.get('time_slot_id')
    return render_template('payment.html', booking_date=booking_date, time_slot_id=time_slot_id, shooting_cabin_id=shooting_cabin_id,get_shooting_cabin_by_id=get_shooting_cabin_by_id)

def get_shooting_cabin_by_id(shooting_cabin_id):
    query = {'_id': ObjectId(shooting_cabin_id)}
    shooting_cabin = shooting_cabin_col.find_one(query)
    print(shooting_cabin)
    return shooting_cabin


@app.route("/paynow", methods=['post'])
def paynow():
    booking_date = request.form.get('booking_date')
    time_slot_id = request.form.get('time_slot_id')
    shooting_cabin_id = request.form.get('shooting_cabin_id')
    bill_amount = request.form.get('bill_amount')
    print(bill_amount)
    card_type = request.form.get('card_type')
    card_holder_name = request.form.get('card_holder_name')
    card_number = request.form.get('card_number')
    cvv = request.form.get('cvv')
    expiry_date = request.form.get('expiry_date')
    query = {'booking_date': booking_date, 'shooting_cabin_id': ObjectId(shooting_cabin_id), 'time_slot_id': ObjectId(time_slot_id), 'player_id': ObjectId(session['player_id']), 'date':datetime.now(),'status':'Booked' }
    result = schedule_col.insert_one(query)
    schedule_id = result.inserted_id
    query = {'schedule_id': ObjectId(schedule_id), 'card_type': card_type, 'card_holder_name': card_holder_name, 'card_number': card_number, 'cvv': cvv, 'expiry_date': expiry_date, 'bill_amount': bill_amount}
    payment_col.insert_one(query)
    return render_template("msg.html", msg='Payment Successful')



@app.route("/view_bookings")
def view_bookings():
    if session['role'] == 'player':
        player_id = session['player_id']
        query = {'player_id': ObjectId(player_id)}
    else:
        schedule_id= request.args.get('schedule_id')
        query = {'_id': ObjectId(schedule_id)}
    schedules = schedule_col.find(query)
    return render_template('view_bookings.html', schedules=schedules,get_time_slot_by_id=get_time_slot_by_id,get_shooting_cabin_by_id=get_shooting_cabin_by_id)

def get_time_slot_by_id(time_slot_id):
    query = {'_id': ObjectId(time_slot_id)}
    time_slot = time_slots_col.find_one(query)
    return time_slot

def get_shooting_cabin_by_id(shooting_cabin_id):
    query = {'_id': ObjectId(shooting_cabin_id)}
    cabin = shooting_cabin_col.find_one(query)
    return cabin


@app.route("/cancel_booking")
def cancel_booking():
    schedule_id = request.args.get('schedule_id')
    query = {'_id': ObjectId(schedule_id)}
    query2 = {'$set': {'status': 'Cancelled'}}
    schedule_col.update_one(query,query2)
    return render_template("msg.html", msg="Booking Cancelled")

@app.route("/view_admin_bookings")
def view_admin_bookings():
    booking_date = request.args.get('booking_date')
    shooting_cabin_id = request.args.get('shooting_cabin_id')
    print(shooting_cabin_id)
    if booking_date == None:
        booking_date = datetime.today().strftime('%Y-%m-%d')
        booking_date = str(booking_date)
    query = {'shooting_cabin_id': ObjectId(shooting_cabin_id),"booking_date":booking_date}
    schedules = schedule_col.find(query)
    return render_template('view_admin_bookings.html', schedules=schedules,get_cabins_by_id=get_cabins_by_id,get_time_slot_by_id=get_time_slot_by_id, get_player_by_id=get_player_by_id,booking_date=booking_date, shooting_cabin_id=shooting_cabin_id)


def get_cabins_by_id(shooting_cabin_id):
    query = {'_id': ObjectId(shooting_cabin_id)}
    cabin = shooting_cabin_col.find_one(query)
    return cabin

def get_player_by_id(player_id):
    query = {'_id': ObjectId(player_id)}
    player = player_col.find_one(query)
    return player

@app.route('/view_payment_details')
def view_payment_details():
    schedule_id = request.args.get('schedule_id')
    player_id = request.args.get('player_id')
    query = {'schedule_id': ObjectId(schedule_id)}
    payments = payment_col.find(query)
    return render_template('view_payment_details.html', payments=payments)

@app.route('/complete_schedule')
def complete_schedule():
    schedule_id = request.args.get('schedule_id')
    query = {'_id': ObjectId(schedule_id)}
    query2 = {'$set': {'status': 'Scheduled'}}
    schedule_col.update_one(query, query2)
    return render_template("msg.html", msg="Booking Scheduled")


@app.route("/player_home")
def player_home():
    return render_template('player_home.html')


@app.route('/add_holidays')
def add_holidays():
    return render_template('add_holidays.html')


@app.route('/add_holidays1', methods=['post'])
def add_holidays1():
    holiday_title = request.form.get('holiday_title')
    date = request.form.get('date')
    query = {'holiday_title': holiday_title, 'date': date}
    holidays_col.insert_one(query)
    return render_template('msg.html', msg='Holiday Added Successfully')

@app.route('/view_holidays')
def view_holidays():
    holidays = holidays_col.find()
    return render_template('view_holidays.html', holidays=holidays)


@app.route('/viewPending')
def viewPending():
    player_id = session['player_id']
    query = {'player_id': ObjectId(player_id), 'status': 'Pending'}
    schedules = schedule_col.find(query)
    return render_template('viewPending.html', schedules=schedules, get_time_slot_by_id=get_time_slot_by_id, get_shooting_cabin_by_id=get_shooting_cabin_by_id, float=float)


@app.route('/payAmount')
def payAmount():
    schedule_id = request.args.get('schedule_id')
    total_charge = request.args.get('total_charge')
    return render_template('payAmount.html', total_charge=total_charge, schedule_id=schedule_id)

@app.route('/payAmount1', methods=['post'])
def payAmount1():
    card_holder_name = request.form.get('card_holder_name')
    card_number = request.form.get('card_number')
    cvv = request.form.get('cvv')
    expiry_date = request.form.get('expiry_date')
    card_type = request.form.get('card_type')
    queryy = {'player_id': ObjectId(session['player_id']),"status":"Pending"}
    print(queryy)
    schedules = schedule_col.find(queryy)
    for schedule in schedules:
        print('innnn')
        query1 = {"schedule_id": schedule['_id']}
        query2 = {"$set": {'card_holder_name': card_holder_name, 'card_number': card_number, 'cvv': cvv,'expiry_date': expiry_date,"card_type": card_type} }
        payment_col.update_one(query1,query2)
        print(query1)
        print(query2)
    query2 = {'$set': {'status': "Booked"}}
    schedule_col.update_many(queryy, query2)
    return render_template('msg.html', msg='Payment Successful')

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")







app.run(debug=True)
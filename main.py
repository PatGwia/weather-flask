from flask import Flask, render_template, request, redirect, url_for
from utils.fetch_weather_data import weather
from pymongo import MongoClient
from datetime import datetime
from utils.convert_temp import convert_temp
from apscheduler.schedulers.background import BackgroundScheduler

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import io

from bson import ObjectId

app = Flask(__name__)
app.debug = True

client = MongoClient("mongodb://localhost:27017")
db = client['Bukowno']
weather_collection = db['wether']
task_collection = db['tasks'] #przechwytuje kolekcje jesli jej nie ma to sie utworzy

def save_to_mongodb(x):

    current_weather = {
        "area":x['name'],
        "temp":convert_temp(x['main']['temp']),
        "min":convert_temp(x['main']['temp_min']),
        "max":convert_temp(x['main']['temp_max']),
        "humidity":x['main']['humidity'],
        "pressure":x['main']['pressure'],
        "timestamp":datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "description":f"{x['weather'][0]['main']}, {x['weather'][0]['description']}"
    }
    weather_collection.insert_one(current_weather)

def job():
    data = weather() #dane pogodowe
    if data:
        save_to_mongodb(data)
        print("Dostarczono nowe dane")
    else:
        print("Nie udało sie pobrać danych")


scheduler = BackgroundScheduler()
scheduler.add_job (job,'interval',minutes=15)
scheduler.start()


@app.route("/")
def homepage():
    lates_data = weather_collection.find().sort([('_id',-1)]).limit(30)
    return render_template("index.html", weather_documents=list(lates_data))

@app.route("/chart")
def generate_chart():
    chart_data = weather_collection.find({},{'_id':0, 'temp':1, 'timestamp':1}).sort([('_id',-1)]).limit(5)
    data = list(chart_data)
    timestamps =[datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S").day for entry in data]
    temperatures = [entry["temp"] for entry in data]
    


    fig = Figure()
    axis = fig.add_subplot(1,1,1)
    axis.plot(timestamps,temperatures)
    axis.set_xlabel("Czas")
    axis.set_ylabel("Temperatura")
    axis.set_title("Pogoda Bukowno")

    canvas = FigureCanvasAgg(fig)
    png = io.BytesIO()
    canvas.print_png(png)

    return png.getvalue(),200,{"Content-Type":"image/png"}

#  na podstawie dodanych wartosci w formularzu przekazujemy dane do bazy
@app.route('/add-task', methods=["POST"])
def add_tasks():
    title = request.form.get("title")
    desc = request.form.get("desc")
    category = request.form.get("category")
    urgency = request.form.get("urgency")

    new_task={

        "title":title,
        "desc":desc,
        "category":category,
        "urgency":urgency,
    }
    try:
        task_collection.insert_one(new_task)
    except Exception as e:
        return "Błąd" + str(e)


    return redirect(url_for("tasks"))

@app.route("/delete-task/<id>", methods=["POST"])
def delete_task(id):
    try:
        task_collection.delete_one({"_id":ObjectId(id)})

    except Exception as e:
        return "Bład" + str(e)
    
    return redirect(url_for("tasks"))


@app.route("/tasks")
def tasks():

    tasks = list(task_collection.find())

    return render_template("tasks.html", tasks=tasks)
   

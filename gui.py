import tkinter as tk
from tkinter import messagebox
import numpy as np
import cv2
from PIL import Image
import os
import sys
import pickle
import cx_Oracle
import shutil
import pyttsx3
import PyInstaller
engine=pyttsx3.init()
engine.setProperty('voice','HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0')
engine.setProperty('rate',170)
d_set=set()
connection=None
cursor=None
connection=cx_Oracle.connect('system/system@localhost')
if connection is not None:
    cur=connection.cursor()
    #cur.execute("create table attendance(ID NUMBER(20) PRIMARY KEY,name VARCHAR2(30),branch VARCHAR2(30))")
else:
    messagebox.showinfo("CONNECTION", "Connection already established")
def takeimages():
    name=e1.get()
    sno=int(e2.get())
    branch=e3.get()
    c=count=0
    #cur.execute("alter table db add column attendance INTEGER")
    cur.execute("insert into attendance(sno,name,branch,attendance,percent) values({},'{}','{}',{},{})".format(sno,name,branch,count,c))
    connection.commit()
    #cur.execute("select * from db")
    #for row in cur.fetchall():
     #   print(row)
    #label=tk.Label(root,text=name)
    #label.place(x=600,y=600)
    dirname='F:\python\project\images\{}'.format(sno)
    label=os.path.basename(dirname)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
        print("directory",dirname,"created")
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        cap=cv2.VideoCapture(0)
        i=0
        while(True):
            ret, frame=cap.read()
            gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            faces=face_cascade.detectMultiScale(frame,1.1,5)
            for(x,y,w,h) in faces:
                roi_gray=gray[y:y+h,x:x+w]
                roi_color=frame[y:y+h,x:x+w]    
                cv2.imwrite("{}\{}_{}.png".format(dirname,label,i),roi_color)
                cv2.imshow("IMAGE",frame)
                i+=1
            if cv2.waitKey(1) & 0xFF == ord('s'):
                break
        cap.release()
        cv2.destroyAllWindows();
        return 
    else:
        print("error")
    
def train_images():
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    recognizer=cv2.face.LBPHFaceRecognizer_create()
    current_id=0
    label_ids={}
    x_train=[]
    y_labels=[]
    BASE_DIR=os.path.dirname(os.path.abspath(__file__))
    img_dir=os.path.join(BASE_DIR,"images")
    for root,dirs,files in os.walk(img_dir):
        for file in files:
            if file.endswith(".png") or file.endswith(".jpg"):
                path=os.path.join(root,file)
                label=os.path.basename(root).replace(" ","-").lower()
                #print(label)
                #print(path)
                if not label in label_ids:
                    label_ids[label]=current_id
                    current_id+=1
                id_=label_ids[label]
                print(id_)
                pil_image=Image.open(path).convert("L") # used for converting image into grayscale
                size=(550,550)
                final_image=pil_image.resize(size,Image.ANTIALIAS)
                img_array=np.array(final_image,"uint8") #uint8 is type and converts images to array format
                #print(img_array)
                faces=face_cascade.detectMultiScale(img_array,1.4,5)
                for (x,y,w,h) in faces:
                    roi=img_array[y:y+h, x:x+w]
                    x_train.append(roi)
                    y_labels.append(id_)
    #print(x_train)
    #print(y_labels)
    with open("labels.pickle",'wb') as f:
        pickle.dump(label_ids,f)

    recognizer.train(x_train,np.array(y_labels))
    recognizer.save("trainner.yml")
    engine.say("training completed successfully")
    engine.runAndWait()
    
def track_images():
    dir_name=r'F:\python\project\tracked_images'
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        eye_cascade=cv2.CascadeClassifier('haarcascade_eye.xml')
        recognizer=cv2.face.LBPHFaceRecognizer_create()
        label={}
        with open("labels.pickle",'rb') as f:
            og_label=pickle.load(f)
            label={v:k for k,v in og_label.items()}
        recognizer.read("trainner.yml")

        cap=cv2.VideoCapture(0)
        i=0
        while(True):
            ret, frame=cap.read()
            gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            faces=face_cascade.detectMultiScale(frame,1.4,5)
            
            for(x,y,w,h) in faces:
                #cv2.rectangle(frame,(x,y),(x+w,y+h),(255,255,255),2)
                
                roi_gray=gray[y:y+h,x:x+w]
                roi_color=frame[y:y+h,x:x+w]
                id_,percent=recognizer.predict(roi_gray)
                if percent>50:
                #print(label[id_])
                    #font=cv2.FONT_HERSHEY_SIMPLEX
                    #color=(255,230,255)
                    #stroke=2
                    #cv2.putText(frame,"{}".format(label[id_]),(x,y),font,1,color,stroke,cv2.LINE_AA)
                    cv2.imshow("image",frame)
                    cv2.imwrite(r"{}\tracked{}.png".format(dir_name,i),roi_color)
                    i+=1
            if cv2.waitKey(1) & 0xFF == ord('s'):
                        break
        cap.release();
        cv2.destroyAllWindows();
        return
    else:
        messagebox.showerror("error","Directory already exists")
    
def matching():
    i=700
    t_set=set()
    
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    recognizer=cv2.face.LBPHFaceRecognizer_create()
    label={}
    with open("labels.pickle",'rb') as f:
        og_label=pickle.load(f)
        label={v:k for k,v in og_label.items()}
    recognizer.read("trainner.yml")
    
    T_BASE_DIR=os.path.dirname(os.path.abspath(__file__))
    t_img_dir=os.path.join(T_BASE_DIR,"tracked_images")
    
    for root,dirs,files in os.walk(t_img_dir):
        for file in files:
            
            if file.endswith(".png") or file.endswith(".jpg"):
                
                path=os.path.join(root,file)
                #print(path)
                #roi_color=frame[y:y+h,x:x+w]
                pil_image=Image.open(path).convert("L") # used for converting image into grayscale
                size=(550,550)
                final_image=pil_image.resize(size,Image.ANTIALIAS)
                img_array=np.array(final_image,"uint8") #uint8 is type and converts images to array format
                #print(img_array)

                faces=face_cascade.detectMultiScale(img_array,1.4,3)
                #print(faces)
                
                for(x,y,w,h) in faces:
                    
                    roi=img_array[y:y+h, x:x+w]
                    id_,percent=recognizer.predict(roi)
                    
                    if percent>15:
                        if  label[id_] not in t_set:
                            t_set.add(label[id_])
                            #print(label[id_])
                            cur.execute("select attendance from attendance where sno={}".format(label[id_]))
                            for x in cur.fetchall():
                                for y in x:
                                    cur.execute("update attendance set attendance={}+1 where sno={}".format(y,label[id_]))
                            cur.execute("select attendance from attendance where sno={}".format(label[id_]))
                            for i in cur.fetchall():
                                for j in i:
                                    #print(j)
                                    cur.execute("update attendance set percent=({}/20)*100 where sno={}".format(j,label[id_]))
                                    connection.commit()
                                    
    if len(t_set)>1:
        say="There are {} students in the class".format(len(t_set))
        engine.say(say)
        engine.runAndWait()
    elif len(t_set)==1:
        say="There is only a single student in the class and He bears id number {}".format(t_set)
        engine.say(say)
        engine.runAndWait()
    else:
        say="There is no student in the class"
        engine.say(say)
        engine.runAndWait()
        
def del_dir():
    if os.path.exists(r"F:\python\project\tracked_images"):
        
        shutil.rmtree(r"F:\python\project\tracked_images")
        engine.say("Tracked Directory recmoved")
        engine.runAndWait()
    else:
        engine.say("No directory exists")
        engine.runAndWait()
        
    
def del_record():
    s=int(e2.get())
    cur.execute("delete from attendance where sno={}".format(s))
    connection.commit()
    shutil.rmtree(r"F:\python\project\images\{}".format(s)) 
    engine.say("Record removed successsfully")
    engine.runAndWait()
def del_records():
    cur.execute("select sno from attendance")
    for i in cur.fetchall():
        for j in i:
            if os.path.exists(r"F:\python\project\images\{}".format(j)):
                shutil.rmtree(r"F:\python\project\images\{}".format(j))    
            else:
                engine.say("{} directory donot exists".format(j));
    cur.execute("delete from attendance")
    connection.commit()
    engine.say("All records are removed successfully")
    engine.runAndWait()
def get_att():
    v=int(e4.get())
    print(v)
    cur.execute("select name,percent from attendance where sno={}".format(v))
    for i in cur.fetchall():
        engine.say("Attendance percentage for {} bearing id{} is {} percent".format(i[0],v,i[1]))
        engine.runAndWait()
    connection.commit()
def reset():
    cur.execute("select sno from attendance")
    for i in cur.fetchall():
        for j in i:
            cur.execute("update attendance set percent=0 where sno={}".format(j))
            cur.execute("update attendance set attendance=0 where sno={}".format(j))
    engine.say("reset done successfully")
    engine.runAndWait()
                
def get_results():
    i=1
    root1=tk.Tk()
    root1.configure(bg="white")
    root1.title("Attendance")
    root1.geometry("500x500")
    cur.execute("select * from attendance")
    tk.Label(root1,text="ID",fg="red").grid(row=0,column=0)
    tk.Label(root1,text="Name",fg="red").grid(row=0,column=1)
    tk.Label(root1,text="Branch",fg="red").grid(row=0,column=2)
    tk.Label(root1,text="Classes attended",fg="red").grid(row=0,column=3)
    tk.Label(root1,text="percentage",fg="red").grid(row=0,column=4)
    for dat in cur.fetchall():
        tk.Label(root1, text=dat[0],fg="blue").grid(row=i, column=0)
        tk.Label(root1, text=dat[1],fg="blue").grid(row=i, column=1)
        tk.Label(root1, text=dat[2],fg="blue").grid(row=i, column=2)
        tk.Label(root1, text=dat[3],fg="blue").grid(row=i, column=3)
        tk.Label(root1, text=dat[4],fg="blue").grid(row=i, column=4)
        i+=1
root=tk.Tk()
root.configure(bg="teal")
root.title("Face Recognition")
root.geometry("500x500")
l=tk.Label(root,text="FACE RECOGNITION",fg="black",bg="blue",width="100",height="2" ,font=("bold",20))
l.place(x=0,y=0)


label1=tk.Label(root,text="Name",fg="red",width="10",height="1",font=("bold",20))
label1.place(x=50,y=200)

e1=tk.Entry(root,width="10",font=("italic",20))
e1.place(x=250,y=200)

label2=tk.Label(root,text="ID",fg="red",width="10",height="1",font=("bold",20))
label2.place(x=550,y=200)

e2=tk.Entry(root,width="10",font=("italic",20))
e2.place(x=750,y=200)

label3=tk.Label(root,text="Branch",fg="red",width="10",height="1",font=("bold",20))
label3.place(x=1050,y=200)

e3=tk.Entry(root,width="10",font=("italic",20))

e3.place(x=1250,y=200)

button0=tk.Button(root,text="DELETE TRACKED IMAGES",command=del_dir,fg="white",bg="black",width="30",height="2")
button0.place(x=950,y=300)

button1=tk.Button(root,text="TAKE IMAGES",command=takeimages,fg="white",bg="black",width="30",height="2")
button1.place(x=650,y=300)

button2=tk.Button(root,text="TRAIN IMAGES",command=train_images,fg="white",bg="black",width="30",height="2")
button2.place(x=650,y=400)

button3=tk.Button(root,text="TRACK IMAGES",command=track_images,fg="white",bg="black",width="30",height="2")
button3.place(x=650,y=500)

button3=tk.Button(root,text="MATCH IMAGES",command=matching,fg="white",bg="black",width="30",height="2")
button3.place(x=650,y=600)

button4=tk.Button(root,text="DELETE RECORD",command=del_record,fg="white",bg="black",width="30",height="2")
button4.place(x=70,y=300)

button4=tk.Button(root,text="DELETE ALL RECORDS",command=del_records,fg="white",bg="black",width="30",height="2")
button4.place(x=70,y=350)

button5=tk.Button(root,text="GET RESULTS",command=get_results,fg="white",bg="black",width="30",height="3")
button5.place(x=650,y=700)

e4=tk.Entry(root,width="10",font=("italic",10))
button6=tk.Button(root,text="GET ATTENDANCE",command=get_att,fg="white",bg="black",width="20",height="3")
e4.place(x=1100,y=700)
button6.place(x=1070,y=750)
button7=tk.Button(root,text="RESET",command=reset,fg="white",bg="black",width="20",height="3")
button7.place(x=70,y=400)

root.mainloop()

    

import argparse
import io
import os
from PIL import Image
import cv2
import numpy as np

import datetime
import torch
from flask import Flask, render_template, request, redirect, Response
from keras.models import load_model
from keras.preprocessing import image
import numpy as np

# Membuat direktori Upload untuk menyimpan data input dari user
uploads_dir = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

app = Flask(__name__)
DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S-%f"
# Kamus untuk memetakan nomor kelas ke label yang lebih deskriptif
dic_model1 = {0: 'Jagung Sudah Matang Kemungkinan besar jagung tersebut sudah berumur lebih dari 60 hari karena memiliki ciri fisik jagung yang sudah mulai berwarna Oren.',
              1: 'Jagung Belum Matang Kemungkinan besar jagung tersebut masih berumur dibawah 60 hari karena memiliki ciri fisik jagung yang masih berwarna Putih.', 
              2:  'Padi Sudah Matang Kemungkinan besar padi tersebut sudah berumur lebih dari 3 bulan karena dari ciri fisik gabahnya yang sudah berwarna Kuning', 
              3: 'Padi Belum Matang Kemungkinan besar padi tersebut belum masih berumur dibawah 3 bulan karena dari ciri fisik gabahnya yang masih berwarna Hijau',
              4: 'Pisang Matang kemungkinan besar pisang tersebut sudah berusia lebih dari 9 bulan',
              5: 'Pisang Mentah kemungkinan pisang tersebut berusia kurang dari 9 bulan'}

dic_model2 = {0: 'Blight. Terdapat banyak jenis macam Blight. salah satu yang mendasar adalah  Northern leaf blight atau sering disebut Hawar daun jagung bagian utara. Penyakit ini biasanya terjadi di daerah yang memiliki iklim lembab dan suhu yang cenderung sejuk. Gejala utama NLB termasuk munculnya lesi berwarna coklat pada daun-daun tanaman jagung. Lesi ini sering kali memiliki bentuk linear dan dapat menyebabkan daun mengering, yang pada akhirnya dapat mengurangi hasil panen jagung. Untuk menangani masalah penyakit ini dengan cara praktik manajemen penyakit dan gunakan  hibrida yang tahan. Fungisida mungkin diperlukan pada tanaman inbrida untuk produksi benih selama tahap awal penyakit ini. Praktek rotasi tanaman dan pengolahan tanah mungkin membantu dalam beberapa kasus. Oleh karena itu, praktik manajemen tanaman yang baik, seperti memberikan nutrisi yang cukup dan menjaga kondisi tanah yang sehat, dapat membantu meningkatkan ketahanan tanaman terhadap penyakit.', 
              1: 'Common Rust adalah penyakit jamur yang umum pada tanaman jagung, disebabkan oleh Puccinia sorghi. Gejala utamanya adalah bercak merah-orange atau kuning pucat pada daun jagung. Solusinya pemilihan varietas jagung yang tahan terhadap penyakit, penggunaan fungisida jika diperlukan, danmenjaga tanaman jagung dalam keadaan sehat dengan pemupukan yang tepat.', 
              2: 'Gray Leaf Spot adalah penyakit daun yang disebabkan oleh jamur Cercospora zeae-maydis. Gejala utamanya adalah bercak abu-abu dengan tepi merah-brown pada daun. Hal ini dapat mengurangi hasil panen. Solusi meliputi pemilihan varietas tahan, aplikasi fungisida yang sesuai, dan menjaga jarak tanaman untuk meningkatkan sirkulasi udara dan mengurangi kelembaban daun. Rotasi tanaman juga dapat membantu mengurangi risiko infeksi.', 
              3: 'Healthy atau Tanaman Jagung dalam keadaan sehat.'}

dic_model3 = {0:'Brown Spot.  Brown Spot (disebabkan oleh jamur Bipolaris oryzae). Gejalanya termasuk bercak coklat pada daun padi.',
              1:'Healthy atau Tanaman Padi dalam keadaan sehat.',
              2:'Hispa Hispa (Dicladispa armigera) adalah jenis kumbang yang termasuk dalam keluarga Chrysomelidae. Kumbang ini merupakan hama pada tanaman padi dan tanaman lainnya. Hispa dikenal karena kebiasaannya menggigit dan menghisap cairan tumbuhan, menyebabkan kerusakan pada daun dan batang tanaman. Sebagai hama pada tanaman padi, pengendalian yang efektif melibatkan berbagai strategi, seperti penggunaan varietas tahan, praktik pengelolaan tanaman yang baik, dan penggunaan insektisida yang sesuai.Penyakit Hispa pada Tanaman Padi:Penyebab:-  Agen Penyebab: Kumbang Hispa (Dicladispa armigera).',
              3:'Leaf Streak akibat bakteri disebabkan oleh Xanthomonas oryzae pv. oryzicola.dll.Tanaman yang terinfeksi menunjukkan daun berwarna coklat dan kering. Dalam kondisi yang parah, hal ini dapat menyebabkan berkurangnya berat butir karena hilangnya area fotosintesis.',
              4:'Sheath Blight. Penyakit hawar pelepah merupakan penyakit jamur yang disebabkan oleh Rhizoctonia solani. Daun yang terserang menjadi tua atau mengering dan mati lebih cepat, anakan muda juga dapat musnah.Akibatnya luas daun pada tajuk dapat berkurang secara signifikan akibat penyakit. Berkurangnya luas daun, seiring dengan penuaan daun yang disebabkan oleh penyakit dan anakan muda yang terinfeksi merupakan penyebab utama penurunan hasil.',
              5:'Tungro adalah penyakit yang disebabkan oleh virus tungro, yang ditularkan oleh wereng. gejalanya termasuk daun menguning, pertumbuhan terhambat, dan rendahnya hasil panen. Solusi melibatkan pemilihan varietas tahan, pemantauan rutin dan pengendalian populasi wereng menggunakan insektisida, serta penerapan praktik budidaya yang baik seperti pemupukan yang seimbang.',
              6:'Bacterial Leaf Blight adalah penyakit tanaman padi yang disebabkan oleh bakteri Xanthomonas oryzae pv. oryzae. Gejalanya termasuk bercak air pada daun, batang, dan malai padi. Solusinya pemilihan varietas padi yang tahan terhadap penyakit, penggunaan fungisida atau antibakteri yang sesuai, serta praktik sanitasi seperti pemangkasan tanaman yang terinfeksi dan mengurangi kelembaban. ',
              7:'LeafBlast. Penyakit blas disebabkan oleh jamur Magnaporthe oryzae. Penyakit ini dapat menyerang seluruh bagian tanaman padi di atas tanah: daun, kerah, ruas, leher, bagian malai, dan kadang-kadang pelepah daun.',
              8:'LeafScald adalah penyakit daun pada tanaman padi yang disebabkan oleh bakteri Xanthomonas oryzae. Gejala melibatkan bercak kuning kecoklatan atau merah pada daun padi. Solusinya mencakup pemilihan varietas padi yang tahan terhadap penyakit, dan praktik sanitasi seperti pemangkasan dan pembakaran tanaman yang terinfeksi untuk mencegah penyebaran penyakit.',
              9:'Narrow BrownS merupakan penyakit jamur yang menyerang tanaman padi. Disebabkan oleh jamur, Cercospora janseana, bercak daun mungkin menjadi masalah tahunan bagi banyak orang. Gejala yang paling umum terjadi pada padi dengan gejala bercak daun coklat sempit bermanifestasi dalam bentuk bintik-bintik sempit berwarna gelap pada tanaman padi dengan berbagai ukuran. Meskipun keberadaan dan tingkat keparahan infeksi bervariasi dari satu musim ke musim berikutnya, kasus penyakit cercospora padi yang sudah jelas dapat menyebabkan penurunan hasil panen, serta hilangnya panen sebelum waktunya. Mengendalikan Bercak Daun Coklat Sempit pada Padi Meskipun petani komersial mungkin berhasil menggunakan fungisida, penggunaan fungisida seringkali bukan pilihan yang hemat biaya bagi pekebun rumah. Selain itu, varietas padi yang mengaku tahan terhadap bercak daun coklat sempit tidak selalu merupakan pilihan yang dapat diandalkan, karena strain jamur baru biasanya muncul dan menyerang tanaman yang menunjukkan resistensi. Bagi sebagian besar orang, tindakan terbaik untuk mengendalikan kerugian akibat penyakit jamur ini adalah dengan memilih varietas yang matang pada awal musim. Dengan melakukan hal ini, para petani dapat menghindari tekanan penyakit yang hebat pada waktu panen di akhir musim tanam dengan lebih baik.'		}						

dic_model4 = {0: 'Early Blight Early Blight pada tanaman kentang yang disebabkan oleh jamur Alternaria solani. Klasifikasi penyakit ini mencakup: Penyebab Jamur Alternaria solani: Penyebab utama Early Blight, menyerang daun, batang, dan buah kentang. Gejala Lesi Coklat dengan Cincin Gelap: Lesi berbentuk cincin dengan bagian tengah yang lebih gelap. Daun Kering dan Gugur: Daun terinfeksi kering, kemudian gugur.', 
              1: 'Late Blight Late Blight pada tanaman kentang disebabkan oleh oomycete Phytophthora infestans. Berikut adalah klasifikasi penyakit ini:Penyebab:- Oomycete Phytophthora infestans: Organisme berbeda dari jamur, tetapi sering dianggap sebagai penyakit tanaman. Merupakan penyebab utama Late Blight pada kentang. Gejala: - Bercak Air pada Daun: Muncul bercak air yang berkembang menjadi lesi coklat kemerahan. -  Batang dan Buah Terinfeksi: Selain daun, batang dan buah kentang juga dapat terinfeksi, menunjukkan gejala berupa bercak basah dan berjamur.',
              2: 'Healthy Tanaman Dalam keadaan sehat'}

dic_model5 = {0:'Healthy. Tanaman dalam keadaan sehat',
              1: 'Healthy Leaf Tanaman Dalam keadaan sehat',
              2: 'Leaf Spot. Leaf Spot pada tanaman pisang adalah suatu penyakit yang umum disebabkan oleh jamur atau bakteri. Gejalanya mencakup bercak-bercak pada daun yang dapat berkembang menjadi lesi yang lebih besar seiring berjalannya waktu. Kondisi ini dapat mengakibatkan penurunan kualitas daun dan bahkan menurunkan hasil panen. Penyakit Leaf Spot pada tanaman pisang dapat disebabkan oleh berbagai patogen, termasuk jamur dan bakteri. Berikut adalah informasi umum tentang klasifikasi, penyebab, gejala, dan pengendalian penyakit Leaf Spot: jamur penyebab Leaf Spot pada pisang termasuk Mycosphaerella spp. dan Cercospora spp dan  Xanthomonas campestris pv. musacearum dapat menyebabkan bakteri penyakit Leaf Spot pada pisang. Gejala :  Awalnya muncul bercak-bercak kecil pada daun. - Perluasan Lesi: Bercak dapat berkembang menjadi lesi yang lebih besar dengan tepi yang berbeda warna.- Daun Berlubang: Lesi pada daun dapat menyebabkan daun mengering dan berlubang. Penanganan Penggunaan Fungisida atau Bakterisida',
              3: 'Leaf Spot Leaf. Leaf Spot leaf pada tanaman pisang adalah suatu penyakit yang umum disebabkan oleh jamur atau bakteri. Gejalanya mencakup bercak-bercak pada daun yang dapat berkembang menjadi lesi yang lebih besar seiring berjalannya waktu. Kondisi ini dapat mengakibatkan penurunan kualitas daun dan bahkan menurunkan hasil panen. Penyakit Leaf Spot pada tanaman pisang dapat disebabkan oleh berbagai patogen, termasuk jamur dan bakteri. Berikut adalah informasi umum tentang klasifikasi, penyebab, gejala, dan pengendalian penyakit Leaf Spot: jamur penyebab Leaf Spot pada pisang termasuk Mycosphaerella spp. dan Cercospora spp dan  Xanthomonas campestris pv. musacearum dapat menyebabkan bakteri penyakit Leaf Spot pada pisang. Gejala :  Awalnya muncul bercak-bercak kecil pada daun. - Perluasan Lesi: Bercak dapat berkembang menjadi lesi yang lebih besar dengan tepi yang berbeda warna.- Daun Berlubang: Lesi pada daun dapat menyebabkan daun mengering dan berlubang. Penanganan Penggunaan Fungisida atau Bakterisida ',
              4: 'Panama. Penyakit Panama pada tanaman pisang, juga dikenal sebagai Fusarium Wilt atau Layu Panama, disebabkan oleh jamur pathogen Fusarium oxysporum f. sp. cubense. Penyakit ini sangat merugikan dan dapat menyebabkan kerusakan serius pada kebun pisang. Gejala:-  Layu: Daun-daun tanaman mulai layu secara perlahan, dimulai dari daun paling tua.- Pembusukan dan Perubahan Warna Batang: Batang tanaman mengalami pembusukan, dan warna dalam batang bisa berubah menjadi coklat atau hitam. Penyebaran:- Penyakit ini dapat menyebar melalui tanah terkontaminasi, alat pertanian yang terinfeksi, atau bahkan air irigasi. Pengendalian:- Penggunaan Tanaman yang Tahan: Pemilihan varietas pisang yang tahan terhadap strain tertentu dari Fusarium oxysporum f. sp. cubense dapat membantu dalam pengendalian ',
              5: 'Panama Leaf Penyakit Panama pada tanaman pisang, juga dikenal sebagai Fusarium Wilt atau Layu Panama, disebabkan oleh jamur pathogen Fusarium oxysporum f. sp. cubense. Penyakit ini sangat merugikan dan dapat menyebabkan kerusakan serius pada kebun pisang. Gejala:-  Layu: Daun-daun tanaman mulai layu secara perlahan, dimulai dari daun paling tua.- Pembusukan dan Perubahan Warna Batang: Batang tanaman mengalami pembusukan, dan warna dalam batang bisa berubah menjadi coklat atau hitam.  Penyebaran:- Penyakit ini dapat menyebar melalui tanah terkontaminasi, alat pertanian yang terinfeksi, atau bahkan air irigasi.Pengendalian:- Penggunaan Tanaman yang Tahan: Pemilihan varietas pisang yang tahan terhadap strain tertentu dari Fusarium oxysporum f. sp. cubense dapat membantu dalam pengendalian '}


# Load dua model H5 yang berbeda
model1 = load_model('kematangan.h5')
model2 = load_model('Penyakitjagung.h5')
model3 = load_model('PenyakitPadi.h5')
model4 = load_model('PenyakitKentang.h5')
model5 = load_model('PenyakitPisang.h5')

# Load YOLOv5 Model
model = torch.hub.load( "ultralytics/yolov5","yolov5s", pretrained=True, force_reload=True)#.autos
model.eval()
model.conf = 0.6  # confidence threshold (0-1)
model.iou = 0.45  # NMS IoU threshold (0-1)

def predict_image(model, img_path, dic):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    class_probabilities = model.predict(img_array)
    predicted_class = np.argmax(class_probabilities)
    
    # Menggunakan dic untuk mendapatkan label yang sesuai dengan kelas yang diprediksi
    predicted_label = dic.get(predicted_class, "Unknown Class")
    # Mengambil nilai probabilitas kelas yang diprediksi
    confidence =  class_probabilities[0][predicted_class] * 100
    
    return predicted_label, confidence

# Route untuk halaman utama
@app.route("/", methods=['GET', 'POST'])
def main():
    return render_template("index.html")

# Route untuk halaman about
@app.route("/about", methods=['GET'])
def about():
    return render_template("about.html")

# Route untuk halaman education_agriculture
@app.route("/education_agriculture", methods=['GET'])
def education_agriculture():
    return render_template("education_agriculture.html")

# Route untuk halaman team
@app.route("/team", methods=['GET'])
def team():
    return render_template("team.html")

# Route untuk detection_temperature
@app.route("/detection_temperature", methods=['GET', 'POST'])
def detection_temperature():
    return render_template("monitoring.html")

def gen():
    cap=cv2.VideoCapture(0)
    # Read until video is completed
    while(cap.isOpened()):
        
        # Capture frame-by-fram ## read the camera frame
        success, frame = cap.read()
        if success == True:

            ret,buffer=cv2.imencode('.jpg',frame)
            frame=buffer.tobytes()
    
            img = Image.open(io.BytesIO(frame))
            results = model(img, size=640)
            results.print()  # print results to screen
            #convert remove single-dimensional entries from the shape of an array
            img = np.squeeze(results.render()) #RGB
            # read image as BGR
            img_BGR = cv2.cvtColor(img, cv2.COLOR_RGB2BGR) #BGR
        else:
            break
        # Encode BGR image to bytes so that cv2 will convert to RGB
        frame = cv2.imencode('.jpg', img_BGR)[1].tobytes()
        #print(frame)
        
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
def video():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')
# Route untuk halaman detection_webcamm
@app.route("/detection_webcam", methods=['GET'])
def detection_webcam():
    return render_template("detection_webcam.html")

# Route untuk detection_image
@app.route("/detection_image", methods=['GET', 'POST'])
def detection_image():
    return render_template("detection_image.html")

@app.route("/submit", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        model_name = request.form['model_name']
        img = request.files['my_image']
        img_path = "static/images/detect/"+ img.filename
        img.save(img_path)

        if model_name == 'model1':
            prediction = predict_image(model1, img_path, dic_model1)
            result = f"Prediksi Kematangan : {prediction} "
        elif model_name == 'model2':
            prediction = predict_image(model2, img_path, dic_model2)
            result = f"Prediksi Penyakit Jagung : {prediction} "
        elif model_name == 'model3':
            prediction = predict_image(model3, img_path, dic_model3)
            result = f"Prediksi Penyakit Padi : {prediction}"
        elif model_name == 'model4':
            prediction = predict_image(model4, img_path, dic_model4)
            result = f"Prediksi Penyakit Kentang : {prediction}"
        elif model_name == 'model5':
            prediction = predict_image(model5, img_path, dic_model5)
            result = f"Prediksi Penyakit Pisang : {prediction}"
        else:
            with open(img_path, 'rb') as f:
               img_bytes = f.read()
            img = Image.open(io.BytesIO(img_bytes))
            results = model([img])

            results.render()  # updates results.imgs with boxes and labels
            now_time = datetime.datetime.now().strftime(DATETIME_FORMAT)
            img_savename = f"static/images/detect/{now_time}.png"
            Image.fromarray(results.ims[0]).save(img_savename)
            img_path = img_savename
            result = f"Hasil Object Detection"
           
        return render_template("detection_image.html", img_path=img_path, result=result)

    return render_template("detection_image.html")


if __name__ == '__main__':
    app.run(debug=True)

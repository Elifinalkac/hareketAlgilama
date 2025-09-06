# Gerekli kütüphaneleri içe aktar
import cv2  # Görüntü işleme için
import time  # Zamanlama işlemleri için
import webbrowser  # Web tarayıcıyı açmak için
import pyautogui  # Klavye ve fare otomasyonu için
import os  # Dosya ve klasör işlemleri için

def send_whatsapp_message():
    """
    WhatsApp Web üzerinden belirli bir numaraya mesaj gönderir.
    Bu işlem, tarayıcıyı açıp kapatmayı içerdiği için zaman alabilir.
    """
    phone_number = "+90 Telefon numarası girin"
    # Güncel tarih ve saat bilgisini al
    timestamp = time.strftime("%d.%m.%Y %H:%M:%S")
    # Gönderilecek mesajı hazırla
    message = f"Hareket tespit edildi! Tarih/Saat: {timestamp}"
    # WhatsApp Web API URL'sini oluştur
    web_url = f"https://web.whatsapp.com/send?phone={phone_number.strip('+')}&text={message}"

    try:
        print(f"[BİLGİ] WhatsApp üzerinden mesaj gönderiliyor: '{message}'")
        
        # Tarayıcıyı aç ve WhatsApp Web'e git
        webbrowser.open(web_url)
        
        # WhatsApp Web'in yüklenmesi için bekle
        time.sleep(15) 
        
        # Mesajı göndermek için Enter tuşuna bas
        pyautogui.press('enter')
        
        # Mesajın iletilmesi için 3 saniye bekle
        time.sleep(3)
        
        # Tarayıcı sekmesini kapat
        pyautogui.hotkey('ctrl', 'w')
        
        print("[BİLGİ] WhatsApp mesajı başarıyla gönderildi!")
        return True
    
    except Exception as e:
        print(f"[HATA] WhatsApp gönderiminde hata oluştu: {e}")
        return False

def save_motion_image(frame, save_folder):
    """
    Kameradan alınan görüntüyü belirtilen klasöre kaydeder.
    """
    try:
        # Dosya adını benzersiz yapmak için tarih ve saat ekle
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"hareket_{timestamp}.jpg"
        file_path = os.path.join(save_folder, filename)
        
        # Görüntüyü dosyaya kaydet
        if cv2.imwrite(file_path, frame):
            print(f"[BİLGİ] Hareket görüntüsü başarıyla kaydedildi: '{file_path}'")
            return True
        else:
            print(f"[HATA] Görüntü dosyaya yazılamadı. Yol veya izin sorunu olabilir: '{file_path}'")
            return False

    except Exception as e:
        print(f"[HATA] Görüntü kaydedilirken beklenmedik bir hata oluştu: {e}")
        return False
    
def main():
    """
    Ana program döngüsünü çalıştırır: kamerayı başlatır, klasörü oluşturur ve hareket algılar.
    """
    # Resimlerin kaydedileceği klasör yolunu girin
    save_folder = "Resimlerin kaydedileceği klasör yolunu girin"
    
    # Program başlar başlamaz klasörü oluştur
    try:
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
            print(f"[BİLGİ] '{save_folder}' klasörü oluşturuldu.")
        else:
            print(f"[BİLGİ] '{save_folder}' klasörü zaten mevcut.")
    except Exception as e:
        print(f"[KRİTİK HATA] Klasör oluşturulurken beklenmedik bir hata oluştu: {e}")
        return

    # Kamerayı bulana kadar farklı indeksleri dene
    cap = None
    max_index_to_try = 5 # 0'dan 4'e kadar dene
    for i in range(max_index_to_try):
        cap = cv2.VideoCapture(i)
        if cap and cap.isOpened():
            print(f"[BİLGİ] Kamera, indeks {i} ile başarıyla açıldı.")
            break
        else:
            print(f"[UYARI] Kamera, indeks {i} ile açılamadı. Başka bir indeksi deniyor...")
            if cap: cap.release()
            cap = None
            
    if not cap:
        print("[HATA] Herhangi bir kamera bulunamadı veya açılamadı.")
        print("Lütfen kameranızın doğru çalıştığından ve sürücülerinin güncel olduğundan emin olun.")
        return

    # MOG2 algoritması ile arka plan çıkarıcı oluştur
    backSub = cv2.createBackgroundSubtractorMOG2(
        history=500,
        varThreshold=25,
        detectShadows=True
    )
    
    last_motion_time = 0
    cooldown = 10  # Hareket algılamaları arasında bekleme süresi (saniye)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[HATA] Kamera görüntüsü alınamadı!")
                break

            # Görüntüden ön plan maskesini al
            fgMask = backSub.apply(frame)

            # Maskedeki gürültüyü temizle ve hareketi belirginleştir
            _, thresh = cv2.threshold(fgMask, 250, 255, cv2.THRESH_BINARY)
            thresh = cv2.erode(thresh, None, iterations=2)
            thresh = cv2.dilate(thresh, None, iterations=2)

            # Hareket eden bölgelerin sınırlarını bul
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            motion_detected = False
            for contour in contours:
                if cv2.contourArea(contour) < 1500:
                    continue
                motion_detected = True
                break

            current_time = time.time()
            
            # Hareket algılandıysa ve bekleme süresi dolduysa işlemleri gerçekleştir
            if motion_detected and (current_time - last_motion_time > cooldown):
                print("[BİLGİ] Hareket algılandı!")
                
                # Hareketin gerçekleştiği kareye metin ekle
                cv2.putText(frame, "Hareket Algilandi!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Resim kaydetme ve mesaj gönderme işlemini aynı anda başlat
                image_saved = save_motion_image(frame, save_folder)
                whatsapp_message_sent = send_whatsapp_message()
                
                if image_saved and whatsapp_message_sent:
                    last_motion_time = current_time
                else:
                    print("[UYARI] İşlem tamamlanamadı. Tekrar denenecek.")
            else:
                cv2.putText(frame, "Hareket Yok!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Canlı görüntü ve hareket maskesini göster
            cv2.imshow("Kamera", frame)
            cv2.imshow("Hareket Maskesi", thresh)

            # 'q' tuşuna basıldığında döngüden çık
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("[BİLGİ] Program kullanıcı tarafından durduruldu.")
    finally:
        # Program sonlandığında kaynakları temizle
        if 'cap' in locals() and cap and cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

import socket
from main import main as run_main  # Sizin main.py içindeki main fonksiyonu

HOST = "0.0.0.0"
PORT = 5000

def main_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"[SERVER] Beklemede: {HOST}:{PORT}")

    while True:
        print("[SERVER] Bir istemci bağlanması bekleniyor...")
        client_socket, addr = server_socket.accept()
        print(f"[SERVER] İstemci bağlandı: {addr}")

        try:
            data = client_socket.recv(1024)
            if not data:
                print("[SERVER] Boş veri, bağlantı kapandı.")
                client_socket.close()
                continue

            command = data.decode("utf-8").strip()
            print(f"[SERVER] Alınan komut: {command}")

            if command == "START_MAIN":
                # Burada main() fonksiyonunu çağırıyoruz
                print("[SERVER] main() fonksiyonu çalıştırılıyor...")
                try:
                    run_main()  # main.py içindeki main()
                    # Bittiğinde DONE cevabını gönderelim
                    client_socket.sendall(b"DONE")
                except Exception as e:
                    # Eğer main() içinde hata çıkarsa, hata mesajı da yollayabilirsiniz
                    err_msg = f"ERROR: {e}"
                    client_socket.sendall(err_msg.encode("utf-8"))
            else:
                # Geçersiz komut
                client_socket.sendall(b"INVALID_COMMAND")

        except Exception as ex:
            print(f"[SERVER] Hata: {ex}")
        finally:
            client_socket.close()
            print("[SERVER] İstemci bağlantısı kapatıldı.")

if __name__ == "__main__":
    main_server()

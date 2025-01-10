import requests

# URL API
url = "http://10.126.15.25:3000/recipe-eph"

try:
    # Mengirim permintaan GET ke API
    response = requests.get(url)
    
    # Memeriksa status kode respons
    if response.status_code == 200:
        # Menampilkan data yang diterima
        data = response.json()  # Mengubah respons menjadi format JSON
        print("Data berhasil diambil:")
        print(data)
    else:
        print(f"Gagal mengambil data. Status kode: {response.status_code}")
        print(f"Pesan: {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Terjadi kesalahan saat mengakses API: {e}")

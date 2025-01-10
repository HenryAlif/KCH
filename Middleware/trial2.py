import requests

# URL API
url = "http://10.126.15.25:3000/recipe-eph"

try:
    # Mengirim permintaan GET ke API
    response = requests.get(url)
    
    # Menampilkan status kode dan respons mentah
    print(f"Status kode: {response.status_code}")
    print("Respons mentah:")
    print(response.text)  # Menampilkan data mentah dari respons
    
    # Memeriksa apakah respons berupa JSON
    try:
        data = response.json()  # Mencoba mengubah respons ke format JSON
        print("Data dalam format JSON:")
        print(data)
    except ValueError:
        print("Respons bukan format JSON yang valid.")
except requests.exceptions.RequestException as e:
    print(f"Terjadi kesalahan saat mengakses API: {e}")

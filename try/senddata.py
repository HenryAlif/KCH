import json

# List untuk menampung 100 data
data_list = []

# Membuat 100 data dengan nama dan kelas yang berbeda
for i in range(1, 101):
    senddata = {
        "nama": f"data {i}",
        "kelas": i % 12 + 1  # kelas bervariasi dari 1 sampai 12
    }
    data_list.append(senddata)  # Tambahkan data ke list

# Menyimpan list data ke dalam file JSON dengan format rapi
with open("sample2.json", "w") as outfile:
    json.dump(data_list, outfile, indent=4)

print("Data telah disimpan dengan format yang rapi.")

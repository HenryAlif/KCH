import json

#contoh program untuk membaca data json
file_json = open("datauji.json")

data = json.loads(file_json.read())
print(data)


#contoh program untuk mengirim data ke json

x = {
  "name": "John",
  "age": 30,
  "married": True,
  "divorced": False,
  "children": ("Ann","Billy"),
  "pets": None,
  "cars": [
    {"model": "BMW 230", "mpg": 27.5}, 
    {"model": "Ford Edge", "mpg": 24.1}
  ]
}

    
export = json.dumps(x)
print(export)
import time
import webbrowser

folder = "Danny"
dataset_name = "TVC03_TEST50"
base_url = "http://localhost:3000/data/b010a08f-1904-cd04-abac-42a45cd23f3f"
url = f"{base_url}/{folder}/{dataset_name}"

webbrowser.open(url)
time.sleep(5)
print("done")

import requests
#
# folder = "Danny"
# dataset_name = "TVC03_TEST50"
# base_url = "http://localhost:3000/data/b010a08f-1904-cd04-abac-42a45cd23f3f"
# url = f"{base_url}/{dataset_name}/{folder}"
#
# response = requests.get(url)
#
# if response.status_code == 200:
#     print("Request was successful.")
#     print(response.text)  # Print the content of the webpage
# else:
#     print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
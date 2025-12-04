# AI Sous Chef

### Description

<img width="1181" height="747" alt="image" src="https://github.com/user-attachments/assets/3ef6ea7c-f538-4a12-a2be-4dca1a4866bb" />
<img width="1170" height="722" alt="image" src="https://github.com/user-attachments/assets/dc0df563-57b3-4b91-a4c7-b09c0d8d92ca" />
<img width="1028" height="728" alt="image" src="https://github.com/user-attachments/assets/adb7b527-ee24-46d3-83ed-83ad7986f09a" />




**A hands-free, low-cost kitchen assistant powered by AWS and on-device interaction.**

AI Sous Chef turns cooking into a frictionless experience.

Instead of scrolling through recipe sites, ads, and infinite paragraphs, you simply ask what you want to make – “I want pasta,” “something with chicken,” “a 20-minute dinner” – and the device instantly returns clean, structured recipes.

Built with a custom ETL pipeline, a keyword-search engine, and a minimal AWS architecture (Lambda + S3 + API Gateway), the system delivers fast, vitually zero-cost lookups to a dedicated Raspberry-Pi-based kitchen tablet.

The motivation is simple:
Cooking shouldn’t require a phone, a search engine, or patience. Just ask, and cook.

### To Run

1. Clone to Raspberry Pi
2. `cd ~/ai-sous-chef`
3. `python run_new.py`


### AWS Disclaimer

Amazon Web Services is an integral component of this project, so I write Infrastructure as Code (IaC) to provision and tear down almost all AWS services and functionalities programatically. However, some actions (such as creating an access key) must be completed first in the console; re-creating this project requires a baseline understanding of AWS.


### Dataset

* Uses the Kaggle dataset – Food.com - Recipes and Reviews – containing over 500,000 detailed recipes.

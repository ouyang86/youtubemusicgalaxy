Music Galaxy Application

#Reserve static external IP Address
gcloud compute addresses create galaxy-address

#Check reserved static IP Address
gcloud compute addresses list

#Create application server using reserved static IP Address
gcloud compute instances create galaxy-server --boot-disk-device-name galaxy-disk --boot-disk-size 20GB --boot-disk-type pd-ssd --address 104.198.96.97

#Copy the youtube database to galaxy-server
gcloud compute copy-files youtube.db galaxy-server:/var/www/MusicGalaxy/MusicGalaxy/youtube.db

#Copy model component to galaxy-server
gcloud compute copy-files youtube/train galaxy-server:/var/www/MusicGalaxy/MusicGalaxy/train

#Copy code to galaxy-server
gcloud compute copy-files static galaxy-server:/var/www/MusicGalaxy/MusicGalaxy/static

gcloud compute copy-files templates galaxy-server:/var/www/MusicGalaxy/MusicGalaxy/templates

gcloud compute copy-files __init__.py galaxy-server:/var/www/MusicGalaxy/MusicGalaxy/__init__.py

gcloud compute copy-files ner.py galaxy-server:/var/www/MusicGalaxy/MusicGalaxy/ner.py

gcloud compute copy-files musicgalaxy.wsgi galaxy-server:/var/www/MusicGalaxy/musicgalaxy.wsgi

#Set up galaxy-server
gcloud ssh galaxy-server

sudo apt-get install libapache2-mod-wsgi python-dev

sudo a2enmod wsgi 

sudo pip install --upgrade google-api-python-client

sudo pip install -U nltk

sudo pip install -U numpy

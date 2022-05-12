# Data-Collection-Pipeline
This repository is for my AiCore project for data collection. 

And this README is for the description of this project and answering the questions of the project milestones. 

## Milestone 1 - Decide the website you are going to collect data from
I am working with horse racing data for several years and still interesting in digging more 'useful knowledge' on this area. So I will try to collect data from a horse racing web site. I will try to learn again from AiCore and compare the method between mine and AiCore. And hope it will have some inspiration to improve my skill.

## Milestone 2 - Prototype finding the individual page for each entry

Many website using front rendering and cookie to limit accessing html directly from the http protocol althrogh it will be the most efficient way to capture the data. And now I will use selenium to get the source and content of the website. But it needs to sort out some way to increase the speed of capturing data later. 

### Parser
I will use BeautifulSoap and Regular Expression to parse inforamtion from the website. 

### Extract, Transform and Load (ETL)
I will divide the whole process into three parts namely Extract, Transform and Load. 

#### Extract
Get all html source files in the local repository 

#### Transform
Parse local source files and get need information to local database or files

#### Load
Load local dataset to the central database with all history data 


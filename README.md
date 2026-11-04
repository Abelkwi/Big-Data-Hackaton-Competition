**SMARTSAVE RWANDA**

**Competition:** NISR Big Data Hackathon 2026 

**Track:** Track 1 — Agricultural Productivity  

Team: 
    1. Abel KWIZERA
    2. Francine UWAJENEZA
    
This README is a working draft based on SMARTSAVE RWANDA's project research and the datasets identified in the project workspace.

**1. Project overview**

Rwanda has made remarkable progress in agricultural development over the past two decades. Investments in agricultural productivity, improved inputs, climate-smart farming, and rural development, agricultural productivity, climate-smart farming, improved inputs, and rural development have significantly increased food production. . Nevertheless, improving the amount of food produced is not sufficient on its own: farmers also need effective post-harvest handling, storage and market access, while buyers and communities need reliable access to suitable and nutritious food. Fragmented information across production, prices, food availability, food security, and nutrition can make it harder for stakeholders to identify where further investigation or intervention may be needed.

However, **important structural challenges remain**: Many smallholder farmers continue to experience post-harvest losses, limited storage capacity, weak market access, and low bargaining power. At the same time, institutional buyers including schools, hotels, restaurants, hospitals, retailers, and food processors often struggle to secure reliable, high-quality supplies from local producers. These inefficiencies exist alongside persistent food insecurity, malnutrition, and youth unemployment.

For the NISR Big Data Hackathon 2026, the project uses available NISR and other public datasets to investigate agricultural production and productivity alongside relevant food-loss, market-price, food-security, food-availability, and nutrition indicators. The aim is to turn statistical information into clear Excel-based indicators and visualizations that can support evidence-informed discussion and prioritization by agricultural planners, cooperatives, researchers, development partners, and other food-system stakeholders.

National and international evidence demonstrates the urgency of addressing these challenges. Approximately 20.6% of Rwanda's population continues to experience food insecurity, 40-50% harvest in Rwanda is lost yearly due to structural inefficiencies (around 141kgs per person) that comes between the farmers(producers) and consumers which makes 12% of yearly GDP, While 20.6% of Rwandan population faces food insecurity of while 27% of children under five remain affected by stunting. Furthermore, studies indicate that significant quantities of food are lost or wasted across the value chain every year, representing not only economic losses but also wasted natural resources and missed opportunities to improve livelihoods and nutrition. 

SMARTSAVE RWANDA responds to these challenges by **introducing an integrated system that connects farmers, cooperatives, institutional buyers, logistics providers, youth entrepreneurs, and development partners within one collaborative ecosystem**. Rather than replacing existing agricultural programmes, SMARTSAVE RWANDA complements national efforts by improving coordination across the food system, increasing market efficiency, promoting responsible food utilisation, and strengthening local value chains.

The initiative directly contributes to Rwanda's Vision 2050, the Second National Strategy for Transformation (NST2), and the Sustainable Development Goals, particularly SDG 1 (No Poverty), SDG 2 (Zero Hunger), SDG 4 (Quality Education) SDG 8 (Decent Work and Economic Growth), SDG 12 (Responsible Consumption and Production), SDG 13 (Climate Action) and SDG 17 (Partnership for the Goals).

Beyond improving agricultural markets, SMARTSAVE seeks to build a more connected, resilient, and inclusive food system where every harvest creates greater value, nutritious food reaches those who need it most, and young innovators become active contributors to Rwanda's sustainable development. SMARTSAVE RWANDA is therefore more than a digital system or an agricultural project. It is a scalable social enterprise that transforms fragmented food systems into connected opportunities; creating shared economic, social, and environmental value for farmers, institutions, communities, and future generations.

You can find all the datasets Here: https://drive.google.com/drive/folders/1mlUg2ti11CShWQDenfifRId2TnJprRVU?usp=drive_link

The Excel-centered analytical workflow is found here: https://docs.google.com/spreadsheets/d/13uaMbMCLB_yIAbeO7hkqEEMGX-npjxqy/edit?usp=sharing&ouid=115192111389233668118&rtpof=true&sd=true 

And the engaging interpretations were provided here: https://colab.research.google.com/drive/1ohqeb6bSejv5i7vXrSE7dwtvnMwpN4p6?usp=sharing

The published website: https://abelkwi.github.io/Big-Data-Hackaton-Competition/

Demo video : https://youtu.be/MdDpt8RrRY4   

**Note:** 

1. You can also watch this kinyarwanda version of the demo video about our wesite here: https://youtu.be/0g0TjdCXk1s?si=373nE4HT6yIKX3Dr Please note that this is not the official video for submission, only a reference !
2. The Excel File https://docs.google.com/spreadsheets/d/13uaMbMCLB_yIAbeO7hkqEEMGX-npjxqy/edit?usp=sharing&ouid=115192111389233668118&rtpof=true&sd=true was constucted manually offline. If you want to see its full dynamism or its full potential experience, you can download it to your local computer.

## Repository structure ##

This is a monorepo holding the full project. Each subfolder is a complete, independently versioned project with its own full git history.

| Folder | Project | What it is |
|---|---|---|
| [`SmartSave-frontend/`](./SmartSave-frontend) | Frontend | Static HTML/CSS/JS website (marketplace, farmers portal, food recovery, innovation hub, blog, auth pages) + JS API client |
| [`SmartSave-backend/`](./SmartSave-backend) | Backend | Django REST API (accounts/auth, marketplace, recovery, orders, messaging, notifications, innovation, blog) deployed with Gunicorn |

## Quick start

### Frontend
```bash
cd SmartSave-frontend
# Open index.html in a browser (or serve the folder statically)
# API URL is configured in js/config.js
```

### Backend
```bash
cd SmartSave-backend
python -m venv venv
# Windows: venv\Scripts\activate    |    macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
# API available at http://localhost:8000/api/
```

See each subfolder's own `README.md` for full setup and deployment instructions.

## Original repositories
- Frontend: https://github.com/Abelkwi/SmartSave-frontend
- Backend: https://github.com/Abelkwi/SmartSave-backend

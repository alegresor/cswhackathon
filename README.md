# CSW Hackathon: Mobile Food Bank Alert System

By Aleksei Sorokin [asorokin@hawk.iit.edu](mailto:asorokin@hawk.iit.edu) and Sinjin Acuna [sacuna@hawk.iit.edu](mailto:sacuna@hawk.iit.edu). Please feel free to contact us with any quesitons!

Our work is reproducible using conda and the `environment.yml` file. Note that the `main.py` file will not be able to run without a Google Cloud Service Account and email/password. Our credentials are hidden for privacy reasons, but we can help users setup/link their own credentials in order to reproduce our work. 

## Purpose

1. Someone is interested in getting emails updates when a [Greater Chicago Food Depository's (GCFD) mobile food locations](https://www.chicagosfoodbank.org/find-food/covid-19-neighborhood-sites/) is in their area. 
2. They fill out the [Google Form](https://forms.gle/ie1UDvo1vrx1UEZm8), which would likely be linked from the GCFD website. This form collects their name, email, address, and number of miles they are willing to travel for these opportunities (radius). 
3. GCFD identifies a new mobile food location and adds it to their website. 
4. A GCFD administrator runs the `main.py` file in [this GitHub repo](https://github.com/alegresor/cswhackathon) to:
    1. Scrape data from the GCFD website regarding (updated) available mobile food locations. 
    2. Pull all responses from the google form.
    3. Determine latitude/longitude of each mobile food location and user based on addresses provided on the GCFD website and Google Form responses.
    4. Determine which users are within their desired radius of which mobile food banks. 
    5. When a food bank is within the desired radius of a user, an email is sent with the mobile food banks details. 

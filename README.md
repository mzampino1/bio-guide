# bio-guide

Given a location entered by the user, this project uses iNaturalist data (most recent 10,000 observations)
to create a PDF biodiversity guide \
(See sample guides in `examples/` folder).

## Sections of Guide:
- Wildlife Sighting Distribution
  - Map of the area with dots indicating where observations were found
- Monthly Observation Counts
  - Bar graph showing how many observations were found in each month
- Ecosystem Relative Abundance Distribution (Top 35)
  - Table showing the top 35 most observed species, along with the number of sightings and the percentage of total observations for each species
- Top 20 Dominant Regional Flora/Fauna (Plants/Animals)
  - Tables showing top 20 plants and top 20 animals with pictures of each species, along with the month in which that species was observed most frequently

## Prerequisites:
Python 3.14+

## How to Use:
1. Clone repository and navigate to the project folder:
     ```bash
     git clone https://github.com/mzampino1/bio-guide.git
     cd bio-guide
     ```
2. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. Run program:
   ```bash
   python3 src/main.py
   ```
   *When prompted, enter the location for your biodiversity guide.* \
   The program will take up to about 2-3 minutes to create your guide. \
   When finished, the guide will be in `output/`.

## Tests:
In order to run the project's test suite, follow these steps:
1. Install pytest:
   ```bash
   python3 -m pip install pytest
   ```
2. Run the tests:
   ```bash
   python3 -m pytest
   ```

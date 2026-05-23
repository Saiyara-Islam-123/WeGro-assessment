from fastapi import FastAPI, HTTPException
from data_processing import *

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "root"}

def region_input_val(region):
    if not((region == None) or (region in ["Dhaka", "Chittagong", "Sylhet", 'Rajshahi', 'Khulna', 'Rangpur', 'Barisal', 'Mymensingh'])):
        raise HTTPException(status_code=422, detail="region=Invalid")
    
def farm_type_input_val(farm_type):
    if not((farm_type == None) or farm_type in ['Small', 'Medium', 'Large', 'Commercial']):
            raise HTTPException(status_code=422, detail="farm_type=Invalid")
    
def year_input_val(year):
    if not (year.isnumeric()):
        raise HTTPException(status_code=422, detail="year=Invalid")

    if not((year==None) or year in ["2022", "2023", "2024"]):
        raise HTTPException(status_code=422, detail="year=Invalid")

def season_input_val(season):
    if not((season==None) or  season in ["Spring", "Summer", "Autumn", "Winter"]):
        raise HTTPException(status_code=422, detail="season=Invalid")

def growing_season_input_val(growing_season):
    if not((growing_season==None) or  growing_season in ["Rabi", "Kharif", "Zaid", "Year-Round"]):
        raise HTTPException(status_code=422, detail="growing_season=Invalid")
    
def crop_category_input_val(crop_category):
    if not((crop_category==None) or  crop_category in ["Cereal", "Vegetable", "Fruit", "Pulse", "Oilseed", "Cash Crop", "Spice"]):
        raise HTTPException(status_code=422, detail="crop_category=Invalid")
    
def market_type_input_val(market_type):
    if not ((market_type == None) or (market_type in ["Local", "Wholesale", "Export", "Retail", "Government Procurement"])):
        raise HTTPException(status_code=422, detail="crop_category=Invalid")
    

@app.get("/farms/summary")
async def get_farm_summary(region=None, farm_type=None, year=None, season=None):
    
    region_input_val(region)
    farm_type_input_val(farm_type)
    #year_input_val(year)
    if year != None:
        year = int(year)
    season_input_val(season)

    df = retrive_df("vw_harvest_full")
    return farm_summary_df_json(df, region, farm_type, year, season)

@app.get("/farms/{farm_id}/performance")
async def get_farm_performance(farm_id, year=None, crop_category=None, market_type=None):
    if not (farm_id.isnumeric()):
        raise HTTPException(status_code=422, detail="year=Invalid")
    
    farm_id = int(farm_id)

    #year_input_val(year)

    if year != None:
        year = int(year)

    if not(1 <= farm_id <= 30):
        raise HTTPException(status_code=422, detail="farm_id=Invalid")
    
    #year_input_val(year)
    
    if not ((crop_category==None) or (crop_category in ["Cereal", "Vegetable", 'Fruit', 'Pulse', 'Oilseed', 'Cash Crop', 'Spice'])):
        raise HTTPException(status_code=422, detail="crop_category=Invalid")
    
    market_type_input_val(market_type)   
    
    df = retrive_df("vw_harvest_full")
    
    df_dim_farm = retrive_df("dim_farm")
    return single_farm_performance_json(farm_id, df, df_dim_farm, year, crop_category, market_type)

@app.get("/farms/top")
async def get_top_farms(metric="profit", region=None, farm_type=None, year=None, limit=10):
    if year != None and not (year.isnumeric()):
        raise HTTPException(status_code=422, detail="year=Invalid")
    
    if year != None:
        year = int(year)

    #year_input_val(year)

    region_input_val(region)
    farm_type_input_val(farm_type)
    
    limit = int(limit)
    df = retrive_df("vw_harvest_full")
    
    return top_farms_json(df, metric, region, farm_type, year, limit)

@app.get("/farms/loss-analysis")
async def get_loss_analysis(year=None, season=None, quality_grade =None, crop_category=None):
    if year != None and not (year.isnumeric()):
        raise HTTPException(status_code=422, detail="year=Invalid")
    
    if year != None:
        year = int(year)
    #year_input_val(year)
    growing_season_input_val(season)

    if not((quality_grade==None) or  quality_grade in ["A", "B", "C", "D"]):
        raise HTTPException(status_code=422, detail="quality_grade=Invalid")

    crop_category_input_val(crop_category)
    df = retrive_df("vw_harvest_full")
    
    return loss_analysis_json(df, year, season, quality_grade, crop_category)

@app.get("/crops/yield-efficiency")
async def get_crop_yield_json(crop_category=None, season=None, year=None, region=None, water_requirement=None):
    df, df_crop, = retrive_df("vw_harvest_full"), retrive_df("dim_crop")

    if year != None and not (year.isnumeric()):
        raise HTTPException(status_code=422, detail="year=Invalid")
    
    if year != None:
        year = int(year)
    #year_input_val(year)
    crop_category_input_val(crop_category)
    growing_season_input_val(season)
    region_input_val(region)
    if not((water_requirement==None) or  water_requirement in ["Low", "Medium", "High"]):
        raise HTTPException(status_code=422, detail="quality_grade=Invalid")
    
    return crop_yield_json(df, df_crop, crop_category, season, year, region, water_requirement)

@app.get("/crops/seasonal-trend")
async def get_crop_seasonal_trend(crop_name=None, crop_category=None, year=None, quarter=None, market_type=None):

    df = retrive_df("vw_harvest_full")
    
    if year != None and not (year.isnumeric()):
        raise HTTPException(status_code=422, detail="year=Invalid")
    
    if year != None:
        year = int(year)
    
    if quarter != None:
        quarter = int(quarter)
    
    market_type_input_val(market_type)
    
    crop_category_input_val(crop_category)
    
    return crops_trend_json(df, crop_name, crop_category, year, quarter, market_type)


@app.get("/markets/price-comparison")
async def get_market_price(market_type=None, crop_category=None, year=None, season=None, price_tier=None, district=None):
    df = retrive_df("vw_harvest_full")
    df_market = retrive_df("dim_market")

    if year != None and not (year.isnumeric()):
        raise HTTPException(status_code=422, detail="year=Invalid")
    
    if year != None:
        year = int(year)

    crop_category_input_val(crop_category)
    market_type_input_val(market_type)
    season_input_val(season)

    if not((price_tier==None) or  price_tier in ["Low", "Medium", "High", "Premium"]):
        raise HTTPException(status_code=422, detail="price_tier=Invalid")
    
    return market_price_json(df, df_market, market_type, crop_category, year, season, price_tier, district)

@app.get("/crops/quality-breakdown")
def get_quality_grade(crop_id=None, crop_category=None, year=None, region=None, market_type=None, pesticide_residue=None):
    df = retrive_df("vw_harvest_full")
    df_crop = retrive_df("dim_crop")

    crop_category_input_val(crop_category)
    if year != None and not (year.isnumeric()):
        raise HTTPException(status_code=422, detail="year=Invalid")
    
    if year != None:
        year = int(year)
    
    market_type_input_val(market_type)
    region_input_val(region)

    if not((pesticide_residue==None) or  pesticide_residue in ["None", "Low", "Medium", "High"]):
        raise HTTPException(status_code=422, detail="pesticide_residue=Invalid")

    return quality_grade_json(df, df_crop, crop_id, crop_category, year, region, market_type, pesticide_residue)
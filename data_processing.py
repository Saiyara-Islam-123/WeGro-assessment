from sqlalchemy import create_engine,text
import pandas as pd
import numpy as np
import json


def retrive_df(table):
    f = open("credentials.txt")
    content = f.read().split("\n")
    host = content[0].split("HOST=")[1]
    port = content[1].split("PORT=")[1]
    db = content[2].split("DB=")[1]
    user = content[3].split("USER=")[1]
    password = content[4].split("PASSWORD=")[1]

    engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:3306/agriculture_db')
    df = pd.DataFrame(engine.connect().execute(text(f"SELECT * FROM {table}")))
    return df

def boolean_filter(df, col, accepted_val):
        if accepted_val == None: #no filter, accept all records regardless of col val
            return np.full(len(df), True)
        else:
            return df[col] == accepted_val

def farm_summary_df(df, region=None, farm_type=None, year=None, season=None):
    df=df.copy(deep=True)

    region_filter = boolean_filter(df, "region", region)
    farm_type_filter = boolean_filter(df, "farm_type", farm_type)
    year_filter = boolean_filter(df, "year", year)
    season_filter = boolean_filter(df, "season", season)

    df = df[(region_filter) & (farm_type_filter) & (year_filter) & (season_filter)]

    df = df[['farm_name', "region", 'farm_type',  "revenue_bdt", "input_cost_bdt", "net_profit_bdt", 
             'quantity_harvested_ton', 'quantity_lost_ton',"year", "price_per_ton_bdt"           
             ]]
    
    df["lost_revenue_percentage"] = 100*(((df["quantity_lost_ton"])*(df["price_per_ton_bdt"]))/df["revenue_bdt"])
    #assuming lost_revenue is computed as fraction of quantity_lost_ton by quantity_harvested_ton
    #assuming avg_loss_pct is computed individually for each harvest_id and then this percentage is averaged
    #across all harvest_ids for a particular farm

    #if year == None:
    '''
    df = df.groupby(["farm_name", "region", "farm_type"]).agg({
                                      
                                      "revenue_bdt" : "sum",
                                      "input_cost_bdt" : "sum",
                                      "net_profit_bdt" : "sum",
                                       "lost_revenue_percentage" : "mean"                                
                                      
                                      }
    ).reset_index()
    '''
    #else:
    df = df.groupby(["farm_name", "region", "farm_type", "year"]).agg({
                                      
                                      "revenue_bdt" : "sum",
                                      "input_cost_bdt" : "sum",
                                      "net_profit_bdt" : "sum",
                                       "lost_revenue_percentage" : "mean"                                
                                      
                                      }
    ).reset_index()


    df.rename(columns={"revenue_bdt" : "total_revenue_bdt",
                       "input_cost_bdt" : "total_cost_bdt",
                       "lost_revenue_percentage" : "avg_loss_pct"
                       
                       }, inplace=True)
    
    
    df[['total_revenue_bdt', 'total_cost_bdt', 'net_profit_bdt']]= df[['total_revenue_bdt', 'total_cost_bdt', 'net_profit_bdt']].map(lambda x : int(x))
    df["avg_loss_pct"] = df["avg_loss_pct"].apply(lambda x : round(x, 1))


    return df

def farm_summary_df_json(df, region=None, farm_type=None, year=None, season=None):
    df = farm_summary_df(df, region, farm_type, year, season)
    data = df.to_dict(orient="records")
    d = {}
    d["total_farms"] = len(df["farm_name"].unique())

    filters_applied_dict = {}
    if region != None:
        filters_applied_dict["region"] = region
    
    if farm_type != None:
        filters_applied_dict["farm_type"] = farm_type

    if year != None:
        filters_applied_dict["year"] = year
    
    if season != None:
        filters_applied_dict["season"] = season

    d["filters_applied"] =  filters_applied_dict
    d["data"]=data
    d = json.dumps(d)
    return json.loads(d)

def single_farm_performance(farm_id, df, df_dim_farm, year=None, crop_category=None, market_type=None):
    df = pd.merge(df_dim_farm, df, on="farm_name", how="right")
    df=df.copy(deep=True)
    df = df[df["farm_id"] == farm_id]

    year_filter = boolean_filter(df, "year", year)
    crop_category_filter = boolean_filter(df, "crop_category", crop_category)
    market_type_filter = boolean_filter(df, "market_type", market_type)
    farm_name = df["farm_name"].iloc[0]
    owner = df["owner_name_x"].iloc[0]
    region = df["region_x"].iloc[0]

    df = df[(crop_category_filter) & (market_type_filter) & (year_filter)]

    df[['revenue_bdt','net_profit_bdt']] = df[['revenue_bdt','net_profit_bdt']].map(lambda x : int(x))
    df["quantity_sold_ton"] = df["quantity_sold_ton"].apply(lambda x : float(x))
    

    return farm_name, owner, region, df[['crop_name', 'crop_category', "year", "market_type", 'quantity_sold_ton', 'revenue_bdt',
               'net_profit_bdt', 'quality_grade'
               
               ]]


def single_farm_performance_json(farm_id, df, df_dim_farm, year=None, crop_category=None, market_type=None):
    farm_name, owner, region, df = single_farm_performance(farm_id, df, df_dim_farm, year, crop_category, market_type)
    data = df.to_dict(orient="records")
    d = {}

    d["farm_id"] = farm_id
    d["farm_name"] = farm_name
    d["owner"] = owner
    d["region"] = region

    filters_applied_dict = {}
    if year != None:
        filters_applied_dict["year"] = year
    
    if crop_category != None:
        filters_applied_dict["crop_category"] = crop_category

    if market_type != None:
        filters_applied_dict["market_type"] = market_type 
    
    d["filters_applied"] =  filters_applied_dict
    d["performance"]=data
    d = json.dumps(d)
    return json.loads(d)

def top_farms(df, metric="profit", region=None, farm_type=None, year=None, limit=10):
    year_filter = boolean_filter(df, "year", year)
    region_filter = boolean_filter(df, "region", region)
    farm_type_filter = boolean_filter(df, "farm_type", farm_type)

    df = df[(region_filter) & (farm_type_filter) & (year_filter)]

    df = df.groupby(["farm_name", "region", "farm_type", "year"]).agg({
                                      
                                      "revenue_bdt" : "sum",
                                      "net_profit_bdt" : "sum",
                                       "quantity_harvested_ton" : "sum",
                                       "quantity_sold_ton" : "sum"                                
                                      
                                      }
    ).reset_index()

    df.rename(columns={"revenue_bdt" : "total_revenue_bdt",
                                             
                       }, inplace=True)


    if metric == "profit":
        df = df.sort_values(by=["net_profit_bdt"], ascending=False)

    elif metric == "yield":
        df["yield_efficiency"] = df["quantity_sold_ton"] / df["quantity_harvested_ton"]
        df["yield_efficiency"] = df["yield_efficiency"].apply(lambda x : float(round(100*x, 1)))
        df = df.sort_values(by=["yield_efficiency"], ascending=False)
        

    elif metric == "revenue":
        df = df.sort_values(by=["total_revenue_bdt"], ascending=False)

    df[['total_revenue_bdt','net_profit_bdt']] = df[['total_revenue_bdt','net_profit_bdt']].map(lambda x : int(x))
    
    
    return df.drop(columns=["quantity_sold_ton", "quantity_harvested_ton"]).iloc[0:limit]

def top_farms_json(df, metric="profit", region=None, farm_type=None, year=None, limit=10):
    df = top_farms(df, metric, region, farm_type, year, limit)
    data = df.to_dict(orient="records")
    d = {}
    d["metric"] = metric
    filters_applied_dict = {}

    if region != None:
        filters_applied_dict["region"] = region

    if farm_type != None:
        filters_applied_dict["farm_type"] = farm_type 

    if year != None:
        filters_applied_dict["year"] = year
    
    d["filters_applied"] =  filters_applied_dict
    d["limit"] = limit

    d["rankings"] = data

    d = json.dumps(d)
    return json.loads(d)

def loss_analysis(df, year=None, growing_season=None, quality_grade =None, crop_category=None):
    year_filter = boolean_filter(df, "year", year)
    growing_season_filter = boolean_filter(df, "growing_season", growing_season)
    quality_grade_filter = boolean_filter(df, "quality_grade", quality_grade)
    crop_category_filter = boolean_filter(df, "crop_category", crop_category)

    df = df[(growing_season_filter) & (quality_grade_filter) & (year_filter) & (crop_category_filter)]

    df = df.groupby(["region", "year", "crop_category",  "growing_season", "quality_grade", "pesticide_residue"]).agg({
                                       "quantity_harvested_ton" : "sum",
                                       "quantity_lost_ton" : "sum"                                
                                      
                                      }
    ).reset_index()
    df["loss_pct"] =  100*df["quantity_lost_ton"]/df["quantity_harvested_ton"]
    avg_loss_pct = round(df["loss_pct"].mean(),2)
    df["loss_pct"] = df["loss_pct"].apply(lambda x : round(x, 1)).apply(float)

    df.rename(columns={"quantity_harvested_ton" : "total_harvested_ton",
                        "quantity_lost_ton" : "total_lost_ton"
                       }, inplace=True)
    
    df["total_lost_ton"] = df["total_lost_ton"].apply(float)
    total_harvested_ton = df["total_harvested_ton"].sum()
    
    df.drop(columns=["total_harvested_ton"],inplace=True)
  
    return df, float(avg_loss_pct), float(total_harvested_ton), float(df["total_lost_ton"].sum())

def loss_analysis_json(df, year=None, growing_season=None, quality_grade =None, crop_category=None):
    df, overall_loss_pct, total_harvested_ton, total_lost_ton = loss_analysis(df, year, growing_season, quality_grade, crop_category)
    
    data = df.to_dict(orient="records")
    d = {}
    filters_applied = {}
    if year != None:
        filters_applied["year"] = year
    if growing_season != None:
        filters_applied["season"] = growing_season
    if quality_grade != None:
        filters_applied["quality_grade"] = quality_grade
    
    if crop_category != None:
        filters_applied["crop_category"] = crop_category

    d["filters_applied"] = filters_applied
    d["summary"] = {"total_harvested_ton":total_harvested_ton, "total_lost_ton":total_lost_ton,
                    "overall_loss_pct" : overall_loss_pct
                    }
    
    d["breakdown"] = data

    d = json.dumps(d)
    return json.loads(d)

def crop_yield(df, df_crop, crop_category=None, season=None, year=None, region=None, water_requirement=None):
    df_crop_yield_water = df_crop[["crop_name","avg_yield_ton_per_ha","water_requirement"]]
    df = pd.merge(df, df_crop_yield_water, on="crop_name", how="left")
    crop_category_filter = boolean_filter(df, "crop_category", crop_category)
    season_filter =  boolean_filter(df, "growing_season", season)
    year_filter = boolean_filter(df, "season", season)
    region_filter = boolean_filter(df, "region", region)
    year_filter = boolean_filter(df, "year", year)
    water_requirement_filter = boolean_filter(df, "water_requirement", water_requirement)

    df = df[(crop_category_filter) & (season_filter) & (year_filter) & (crop_category_filter) & (region_filter) & (water_requirement_filter)]

    df["yield_ton_per_ha"] = df["quantity_sold_ton"] / df["total_area_ha"]
    
    df = df.groupby(["crop_name", "crop_category", "avg_yield_ton_per_ha", "season", "water_requirement"]).agg({
        "yield_ton_per_ha" : "mean",
        "total_area_ha" : "sum"
    }).reset_index()

    df.rename(columns={"yield_ton_per_ha" : "actual_avg_yield_ton_per_ha",
                       "avg_yield_ton_per_ha" : "avg_yield_benchmark_ton_per_ha",
                       "total_area_ha" : "total_area_planted_ha"
                       }, inplace=True)

    df["actual_avg_yield_ton_per_ha"] = df["actual_avg_yield_ton_per_ha"].apply(float)
    df["avg_yield_benchmark_ton_per_ha"] = df["avg_yield_benchmark_ton_per_ha"].apply(float)

    df["yield_diff"] = df["actual_avg_yield_ton_per_ha"] - df["avg_yield_benchmark_ton_per_ha"]
    df["yield_diff"] = df["yield_diff"].apply(lambda x : abs(x))
    df["efficiency_pct"] = 100 * df["yield_diff"] / df["avg_yield_benchmark_ton_per_ha"]
    df["efficiency_pct"]  = df["efficiency_pct"].apply(float)

    df[["actual_avg_yield_ton_per_ha", "efficiency_pct", "total_area_planted_ha"]] = df[["actual_avg_yield_ton_per_ha", "efficiency_pct", "total_area_planted_ha"]].map(lambda x : float(round(x, 1)))

    df.drop(columns=["yield_diff"], inplace=True)

    return df

def crop_yield_json(df, df_crop, crop_category=None, season=None, year=None, region=None, water_requirement=None):
    df = crop_yield(df, df_crop, crop_category, season, year, region, water_requirement)
    data = df.to_dict(orient="records")
    d = {}
    filters_applied = {}
    if crop_category != None:
        filters_applied["crop_category"] = crop_category

    if season != None:
        filters_applied["season"] = season

    if year != None:
        filters_applied["year"] = year

    if region != None:
        filters_applied["region"] = region
    
    if water_requirement != None:
        filters_applied["water_requirement"] = water_requirement

    d["filters_applied"] = filters_applied
    d["data"] = data
    #print(df)
    d = json.dumps(d)
    return json.loads(d)

def crops_trend(df, crop_name=None, crop_category=None, year=None, quarter=None, market_type=None):
    crop_name_filter = boolean_filter(df, "crop_name", crop_name)
    crop_category_filter = boolean_filter(df, "crop_category", crop_category)
    year_filter = boolean_filter(df, "year", year)
    quarter_filter = boolean_filter(df, "quarter", quarter)
    market_type_filter = boolean_filter(df, "market_type", market_type)

    df = df[(crop_category_filter) & (crop_name_filter) & (year_filter) & (crop_category_filter) & (quarter_filter) & (market_type_filter)]

    df = df.groupby(["crop_name", "crop_category", "year", "quarter", "season",]).agg({
        "quantity_sold_ton" : "sum",
        "revenue_bdt" : "sum",
        "price_per_ton_bdt" : "mean",
        "quantity_lost_ton" : "count"
    }).reset_index()

    df.rename(columns={
        "quantity_sold_ton" : "total_quantity_sold_ton",
        "revenue_bdt" : "total_revenue_bdt",
        "price_per_ton_bdt" : "avg_price_per_ton_bdt",
        "quantity_lost_ton" : "num_harvests"

    },inplace=True)

    df["total_quantity_sold_ton"] = df["total_quantity_sold_ton"].apply(float).apply(lambda x : float(round(x, 1)))

    df[["total_revenue_bdt", "avg_price_per_ton_bdt"]] = df[["total_revenue_bdt", "avg_price_per_ton_bdt"]].map(int)
    return df

def crops_trend_json(df, crop_name=None, crop_category=None, year=None, quarter=None, market_type=None):
    df = crops_trend(df, crop_name, crop_category, year, quarter, market_type)
    data = df.to_dict(orient="records")
    d = {}
    filters_applied = {}

    if crop_name != None:
        filters_applied["crop_name"] = crop_name

    if crop_category != None:
        filters_applied["crop_category"] = crop_category

    if quarter != None:
        filters_applied["quarter"] = quarter

    if year != None:
        filters_applied["year"] = year

    if market_type != None:
        filters_applied["market_type"] = market_type

    d["filters_applied"] = filters_applied
    d["trend"] = data
    #print(df)
    d = json.dumps(d)
    return json.loads(d)

def market_price(df, df_market, market_type=None, crop_category=None, year=None, season=None, price_tier=None, district=None):
    df_market = df_market[["market_name", "district"]]
    df = pd.merge(df, df_market, how="left", on= "market_name")
    market_type_filter = boolean_filter(df, "market_type", market_type)
    crop_category_filter = boolean_filter(df, "crop_category", crop_category)
    year_filter = boolean_filter(df, "year", year)
    season_filter = boolean_filter(df, "season", season)
    price_tier_filter = boolean_filter(df, "price_tier", price_tier)
    district_filter = boolean_filter(df, "district", district)

    df = df[(market_type_filter) & (crop_category_filter) & (year_filter) & (season_filter) & (price_tier_filter) & (district_filter)]

    df = df.groupby(["market_name", "market_type", "price_tier", "district", "crop_name"]).agg({

        "price_per_ton_bdt" : "mean",
        "quantity_sold_ton" : "sum",
        "revenue_bdt" : "sum"
    }).reset_index()

    df.rename(columns={
        "quantity_sold_ton" : "total_quantity_sold_ton",
        "revenue_bdt" : "total_revenue_bdt",
        "price_per_ton_bdt" : "avg_price_per_ton_bdt",

    },inplace=True)

    df["total_quantity_sold_ton"] = df["total_quantity_sold_ton"].apply(float).apply(lambda x : float(round(x, 1)))
    df[["total_revenue_bdt", "avg_price_per_ton_bdt"]] = df[["total_revenue_bdt", "avg_price_per_ton_bdt"]].map(int)
    return df

def market_price_json(df, df_market, market_type=None, crop_category=None, year=None, season=None, price_tier=None, district=None):
    df = market_price(df, df_market, market_type, crop_category, year, season, price_tier, district)
    data = df.to_dict(orient="records")
    d = {}
    filters_applied = {}

    if market_type != None:
        filters_applied["market_type"] = market_type

    if crop_category != None:
        filters_applied["crop_category"] = crop_category

    if year != None:
        filters_applied["year"] = year

    if season != None:
        filters_applied["season"] = season

    if price_tier != None:
        filters_applied["price_tier"] = price_tier

    if district != None:
        filters_applied["district"] = district

    d["filters_applied"] = filters_applied
    d["comparison"] = data
    #print(df)
    d = json.dumps(d)
    return json.loads(d)
    

def quality_grade(df, df_crop, crop_id=None, crop_category=None, year=None, region=None, market_type=None, pesticide_residue=None):
    def adding_missing_keys(d, type_d):
        if type_d == "quality_grade":
            
            for grade in(["A", "B", "C", "D"]):
                if grade not in d:
                    d[grade] = {"count": 0, "pct": 0.0, "avg_revenue_bdt": 0}
        
        elif type_d == "pesticide":
            for p in ["None", "Trace", "Low", "High"]:
                if p not in d:
                    d[p] = {"count": 0, "pct": 0.0}
        
        return d
    
    df_crop = df_crop[["crop_id", "crop_name"]]
    df = pd.merge(df, df_crop, how="left", on= "crop_name")
    
    crop_id_filter = boolean_filter(df, "crop_id", crop_id)
    market_type_filter = boolean_filter(df, "market_type", market_type)
    crop_category_filter = boolean_filter(df, "crop_category", crop_category)
    region_filter = boolean_filter(df, "region", region)
    year_filter = boolean_filter(df, "year", year)
    pesticide_residue_filter = boolean_filter(df, "pesticide_residue", pesticide_residue)

    df = df[(crop_id_filter) & (market_type_filter) & (crop_category_filter) & (year_filter) & (region_filter) & (pesticide_residue_filter)]
    
    grade_dist= df.groupby("quality_grade").agg({
    "quantity_harvested_ton" : "count",
    "revenue_bdt" : "mean"
    
    })
    grade_dist.rename(columns={
        "quantity_harvested_ton" : "count",
        "revenue_bdt" : "avg_revenue_bdt"

    },inplace=True)

    grade_dist["pct"] = 100 * (grade_dist["count"]/grade_dist["count"].sum())
    grade_dist["pct"] = grade_dist["pct"].apply(lambda x : round(x, 1))
    grade_dist["avg_revenue_bdt"] = grade_dist["avg_revenue_bdt"].apply(int)

    cols = grade_dist.columns.tolist()

    cols = [cols[0]] + [cols[2]] + [cols[1]]
    grade_dist = grade_dist[cols]

    grade_dist_dict = grade_dist.to_dict(orient="index")
    grade_dist_dict = adding_missing_keys(grade_dist_dict, "quality_grade")

    pesticide = df.groupby("pesticide_residue").agg({
        "quantity_harvested_ton" : "count"})

    pesticide.rename(columns={
        "quantity_harvested_ton" : "count"}, inplace=True)

    pesticide["pct"] = 100 * (pesticide["count"]/pesticide["count"].sum())
    pesticide["pct"] = pesticide["pct"].apply(lambda x : round(x, 1))

    pesticide_dict = pesticide.to_dict(orient="index")
    pesticide_dict = adding_missing_keys(pesticide_dict, "pesticide")

    return grade_dist_dict, pesticide_dict, len(df)


def quality_grade_json(df, df_crop, crop_id=None, crop_category=None, year=None, region=None, market_type=None, pesticide_residue=None):
    grade_dist_dict, pesticide_dict, total_records = quality_grade(df, df_crop, crop_id, crop_category, year, region, market_type, pesticide_residue)

    d = {}
    filters_applied = {}

    if crop_id != None:
        filters_applied["crop_id"] = crop_id
    
    if crop_category != None:
        filters_applied["crop_category"] = crop_category

    if year != None:
        filters_applied["year"] = year

    if region != None:
        filters_applied["region"] = region

    if market_type != None:
        filters_applied["market_type"] = market_type
    
    if pesticide_residue != None:
        filters_applied["pesticide_residue"] = pesticide_residue

    d["filters_applied"] = filters_applied

    d["total_records"] = total_records

    d["grade_distribution"] = grade_dist_dict
    d["pesticide_residue_breakdown"] = pesticide_dict

    d = json.dumps(d)
    return json.loads(d)
#!/bin/bash

source keys.txt
afdc_key=$afdc_key

mkdir -p Data/AFDC
mkdir -p Data/State
mkdir -p Data/Place
mkdir -p Outputs

if [ ! -f Data/AFDC/evse_stations.json ]; then
	afdc_url="https://developer.nrel.gov/api/alt-fuel-stations/v1.json?fuel_type=ELEC&limit=all&api_key=${afdc_key}"
	echo $afdc_url
	curl -o Data/AFDC/evse_stations.json $afdc_url
	echo "AFDC Data Downloaded"
else
	echo "AFDC Data Downloaded"
fi

if [ ! -f Data/State/tl_2023_us_state.zip ]; then
	url="https://www2.census.gov/geo/tiger/TIGER2023/STATE/tl_2023_us_state.zip"
	curl -o Data/State/tl_2023_us_state.zip $url
else
	echo "State Geometries Downloaded"
fi

if [ ! -f Data/State/tl_2023_us_state.shp ]; then
	unzip Data/State/tl_2023_us_state.zip -d Data/State
	echo "State Geometries Unzipped"
else
	echo "State Geometries Unzipped"
fi

if [ ! -f Data/Place/tl_2023_06_place.zip ]; then
	url="https://www2.census.gov/geo/tiger/TIGER2023/PLACE/tl_2023_06_place.zip"
	curl -o Data/Place/tl_2023_06_place.zip $url
else
	echo "Place Geometries Downloaded"
fi

if [ ! -f Data/Place/tl_2023_06_place.shp ]; then
	unzip Data/Place/tl_2023_06_place.zip -d Data/Place
	echo "Place Geometries Unzipped"
else
	echo "Place Geometries Unzipped"
fi

if [ ! -f Data/Place/populations.xlsx ]; then
	url="https://www2.census.gov/programs-surveys/popest/tables/2020-2022/cities/totals/SUB-IP-EST2022-POP-06.xlsx"
	curl -o Data/Place/populations.xlsx $url
else
	echo "Place Populations Downloaded"
fi


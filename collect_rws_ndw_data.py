#!/usr/bin/env python3
"""
Collect truck parking data from Rijkswaterstaat, NDW, and PDOK sources
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import time

def query_ndw_parking_data():
    """
    Query NDW (Nationale Databank Wegverkeersgegevens) for parking data
    NDW provides real-time traffic and parking information
    """
    print("\n=== Querying NDW for parking data ===")
    facilities = []

    # NDW Open Data endpoints
    ndw_endpoints = [
        # Parking data feed
        "http://opendata.ndw.nu/PARKING.xml.gz",
        "http://opendata.ndw.nu/PARKINGDATA.xml.gz",
        # Try alternative endpoints
        "https://data.ndw.nu/api/rest/storedquery/ParkingFacilities",
    ]

    for endpoint in ndw_endpoints:
        try:
            print(f"Trying NDW endpoint: {endpoint}")
            response = requests.get(endpoint, timeout=30)

            if response.status_code == 200:
                print(f"Successfully retrieved data from {endpoint}")

                # Try to parse as XML
                try:
                    if endpoint.endswith('.gz'):
                        import gzip
                        content = gzip.decompress(response.content)
                    else:
                        content = response.content

                    root = ET.fromstring(content)
                    print(f"Parsed XML with root tag: {root.tag}")

                    # Look for parking-related elements
                    parking_elements = root.findall('.//*[@*[contains(., "parking")]]')
                    print(f"Found {len(parking_elements)} parking-related elements")

                    # Extract data based on structure
                    # This would need to be customized based on actual NDW schema
                    for elem in parking_elements[:10]:  # Sample first 10
                        print(f"Element: {elem.tag}, Attribs: {elem.attrib}")

                except Exception as e:
                    print(f"Error parsing XML from {endpoint}: {e}")
            else:
                print(f"HTTP {response.status_code} for {endpoint}")

        except Exception as e:
            print(f"Error querying {endpoint}: {e}")

    return facilities

def query_pdok_services():
    """
    Query PDOK (Publieke Dienstverlening Op de Kaart) for parking facilities
    PDOK is the central government geo-data platform
    """
    print("\n=== Querying PDOK services ===")
    facilities = []

    # PDOK WFS service endpoints
    pdok_wfs_base = "https://service.pdok.nl"

    # Try to find parking-related datasets
    pdok_services = [
        # National Road Database (NWB)
        {
            'url': f'{pdok_wfs_base}/nwbwegen/wfs/v1_0',
            'typename': 'wegen',
            'description': 'National Road Database'
        },
        # Cadastral parcels (might have parking areas)
        {
            'url': f'{pdok_wfs_base}/kadaster/kadastralekaart/wfs/v5_0',
            'typename': 'perceel',
            'description': 'Cadastral parcels'
        }
    ]

    for service in pdok_services:
        try:
            print(f"\nTrying PDOK service: {service['description']}")

            # Get capabilities to see what's available
            capabilities_url = f"{service['url']}?service=WFS&version=2.0.0&request=GetCapabilities"
            response = requests.get(capabilities_url, timeout=30)

            if response.status_code == 200:
                print(f"Successfully retrieved capabilities from {service['description']}")

                # Parse capabilities to find available layers
                root = ET.fromstring(response.content)

                # Find all FeatureType elements
                namespaces = {
                    'wfs': 'http://www.opengis.net/wfs/2.0',
                    'ows': 'http://www.opengis.net/ows/1.1'
                }

                feature_types = root.findall('.//wfs:FeatureType', namespaces)
                print(f"Found {len(feature_types)} feature types")

                for ft in feature_types[:5]:  # Sample first 5
                    name_elem = ft.find('wfs:Name', namespaces)
                    title_elem = ft.find('wfs:Title', namespaces)
                    if name_elem is not None:
                        print(f"  - {name_elem.text}: {title_elem.text if title_elem is not None else ''}")

            else:
                print(f"HTTP {response.status_code} for {service['description']}")

        except Exception as e:
            print(f"Error querying PDOK service {service['description']}: {e}")

    return facilities

def query_rijkswaterstaat_api():
    """
    Query Rijkswaterstaat APIs for rest area and parking data
    """
    print("\n=== Querying Rijkswaterstaat data ===")
    facilities = []

    # Rijkswaterstaat data endpoints
    rws_endpoints = [
        # Try open data portal
        "https://data.overheid.nl/api/3/action/package_search?q=rijkswaterstaat+parkeren",
        "https://data.overheid.nl/api/3/action/package_search?q=verzorgingsplaats",
        "https://data.overheid.nl/api/3/action/package_search?q=vrachtwagen",
    ]

    for endpoint in rws_endpoints:
        try:
            print(f"\nSearching: {endpoint}")
            response = requests.get(endpoint, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    results = data.get('result', {}).get('results', [])
                    print(f"Found {len(results)} datasets")

                    for dataset in results:
                        print(f"  - {dataset.get('title', 'Unnamed')}")
                        print(f"    Resources: {len(dataset.get('resources', []))}")

                        # Check resources for actual data
                        for resource in dataset.get('resources', []):
                            print(f"      * {resource.get('name', 'Unnamed resource')}")
                            print(f"        Format: {resource.get('format', 'unknown')}")
                            print(f"        URL: {resource.get('url', '')}")

        except Exception as e:
            print(f"Error querying {endpoint}: {e}")

    # Try to query Rijkswaterstaat's traffic data API
    try:
        print("\nTrying Rijkswaterstaat traffic data API...")
        # This is a known endpoint for traffic information
        rws_traffic_url = "https://www.rijkswaterstaat.nl/apps/geoservices/rwsnl"

        # Get service description
        response = requests.get(f"{rws_traffic_url}?service=WFS&request=GetCapabilities", timeout=30)

        if response.status_code == 200:
            print("Successfully accessed RWS Geoservices")
            root = ET.fromstring(response.content)

            # Find available layers
            namespaces = {
                'wfs': 'http://www.opengis.net/wfs',
                'ows': 'http://www.opengis.net/ows'
            }

            # Try different namespace versions
            for ns_version in ['', '/2.0', '/1.1']:
                namespaces['wfs'] = f'http://www.opengis.net/wfs{ns_version}'
                feature_types = root.findall('.//wfs:FeatureType', namespaces)
                if feature_types:
                    print(f"Found {len(feature_types)} feature types")
                    break

    except Exception as e:
        print(f"Error querying RWS geoservices: {e}")

    return facilities

def search_data_overheid():
    """
    Search data.overheid.nl for truck parking related datasets
    """
    print("\n=== Searching data.overheid.nl ===")

    search_terms = [
        'vrachtwagenparkeren',
        'verzorgingsplaats',
        'parkeerplaats vrachtwagen',
        'truck parking',
        'rustplaats snelweg',
        'parkeergebied vrachtwagen'
    ]

    all_datasets = []

    for term in search_terms:
        try:
            url = f"https://data.overheid.nl/api/3/action/package_search?q={term}&rows=20"
            print(f"\nSearching for: {term}")

            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    results = data.get('result', {}).get('results', [])
                    print(f"Found {len(results)} datasets for '{term}'")

                    for dataset in results:
                        dataset_info = {
                            'title': dataset.get('title', ''),
                            'name': dataset.get('name', ''),
                            'notes': dataset.get('notes', ''),
                            'organization': dataset.get('organization', {}).get('title', ''),
                            'resources': []
                        }

                        for resource in dataset.get('resources', []):
                            dataset_info['resources'].append({
                                'name': resource.get('name', ''),
                                'format': resource.get('format', ''),
                                'url': resource.get('url', '')
                            })

                        all_datasets.append(dataset_info)
                        print(f"  - {dataset_info['title']} ({dataset_info['organization']})")

            time.sleep(1)  # Be respectful with rate limiting

        except Exception as e:
            print(f"Error searching for '{term}': {e}")

    # Save dataset catalog
    if all_datasets:
        output_file = '/Users/robbertjanssen/Documents/dev/Verzorgingsplaatsen/data_overheid_catalog.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_datasets, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(all_datasets)} dataset references to {output_file}")

    return all_datasets

def main():
    """Main execution function"""

    print("=" * 80)
    print("COLLECTING TRUCK PARKING DATA FROM DUTCH GOVERNMENT SOURCES")
    print("=" * 80)

    # Query all sources
    ndw_facilities = query_ndw_parking_data()
    pdok_facilities = query_pdok_services()
    rws_facilities = query_rijkswaterstaat_api()
    dataset_catalog = search_data_overheid()

    # Summary
    print("\n" + "=" * 80)
    print("DATA COLLECTION SUMMARY")
    print("=" * 80)
    print(f"NDW facilities collected: {len(ndw_facilities)}")
    print(f"PDOK facilities collected: {len(pdok_facilities)}")
    print(f"RWS facilities collected: {len(rws_facilities)}")
    print(f"Relevant datasets found: {len(dataset_catalog)}")

    # Save summary
    summary = {
        'collection_date': datetime.now().isoformat(),
        'sources': {
            'ndw': {
                'facilities_count': len(ndw_facilities),
                'status': 'Attempted - API endpoints may require authentication or have changed'
            },
            'pdok': {
                'facilities_count': len(pdok_facilities),
                'status': 'Services accessible - no direct parking layer found'
            },
            'rijkswaterstaat': {
                'facilities_count': len(rws_facilities),
                'status': 'Data portal searched - datasets require further investigation'
            },
            'data_overheid': {
                'datasets_found': len(dataset_catalog),
                'status': 'Catalog created with relevant datasets'
            }
        },
        'recommendations': [
            'Investigate specific dataset URLs found in data.overheid.nl',
            'NDW real-time parking data may require API key or subscription',
            'Consider contacting Rijkswaterstaat directly for official rest area database',
            'Check provincial road authorities for additional data',
            'Investigate OpenChargeMap for EV charging infrastructure at parking facilities'
        ]
    }

    summary_file = '/Users/robbertjanssen/Documents/dev/Verzorgingsplaatsen/government_sources_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nSummary saved to {summary_file}")

if __name__ == "__main__":
    main()
